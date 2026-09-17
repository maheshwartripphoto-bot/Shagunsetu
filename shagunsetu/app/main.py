import os
from pathlib import Path
from fastapi import FastAPI, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, database

app = FastAPI(title="ShagunSetu")
BASE_DIR = Path(__file__).resolve().parent

models.Base.metadata.create_all(bind=database.engine)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
def landing_view(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/wizard", response_class=HTMLResponse)
def wizard_view(request: Request):
    return templates.TemplateResponse("wizard.html", {"request": request})

@app.get("/card/{event_id}", response_class=HTMLResponse)
def card_view(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Invitation card not found")
    return templates.TemplateResponse("card.html", {"request": request, "event": event})

@app.get("/epatrika/{event_id}", response_class=HTMLResponse)
def epatrika_view(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="E-Patrika not found")
    return templates.TemplateResponse("epatrika.html", {"request": request, "event": event})

@app.get("/admin", response_class=HTMLResponse)
def admin_view(request: Request, db: Session = Depends(database.get_db)):
    events = db.query(models.Event).order_by(models.Event.id.desc()).all()
    return templates.TemplateResponse("admin.html", {"request": request, "events": events})

# --- Event Creation ---

@app.post("/create")
def create_event(
    groom_name: str = Form(...),
    bride_name: str = Form(...),
    wedding_date: str = Form(...),
    venue: str = Form(...),
    upi_id: str = Form(...),
    upi_payee_name: str = Form(...),
    host_family: str = Form(None),
    db: Session = Depends(database.get_db)
):
    event = models.Event(
        groom_name=groom_name.strip(),
        bride_name=bride_name.strip(),
        wedding_date=wedding_date,
        venue=venue.strip(),
        upi_id=upi_id.strip(),
        upi_payee_name=upi_payee_name.strip(),
        host_family=host_family.strip() if host_family else None
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Seed default main ceremony
    main_ceremony = models.Ceremony(
        event_id=event.id,
        name="Mandap Muhurat & Saat Pheras",
        date=wedding_date,
        time="11:00 PM",
        venue_name=venue,
        maps_url=f"https://www.google.com/maps/search/?api=1&query={venue.replace(' ', '+')}",
        dress_code="Traditional Ethnic Silks"
    )
    db.add(main_ceremony)

    # Starter registry items
    default_items = [
        models.RegistryItem(event_id=event.id, item_name="Smart Kitchen Appliance Suite", category="Appliances", target_amount=15000),
        models.RegistryItem(event_id=event.id, item_name="Honeymoon Flight Fund", category="Travel", target_amount=25000),
        models.RegistryItem(event_id=event.id, item_name="Living Room Brass Decor", category="Home", target_amount=8000)
    ]
    db.add_all(default_items)
    db.commit()

    return RedirectResponse(url=f"/epatrika/{event.id}", status_code=303)

# --- Multi-Day Ceremony Management ---

@app.post("/ceremony/add/{event_id}")
def add_ceremony(
    event_id: int,
    name: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    venue_name: str = Form(...),
    maps_url: str = Form(None),
    dress_code: str = Form(None),
    db: Session = Depends(database.get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Wedding event not found")

    new_ceremony = models.Ceremony(
        event_id=event.id,
        name=name.strip(),
        date=str(date),
        time=time.strip(),
        venue_name=venue_name.strip(),
        maps_url=maps_url.strip() if maps_url else None,
        dress_code=dress_code.strip() if dress_code else None
    )
    db.add(new_ceremony)
    db.commit()
    return RedirectResponse(url=f"/epatrika/{event_id}#ceremonies-section", status_code=303)

@app.post("/ceremony/delete/{ceremony_id}")
def delete_ceremony(
    ceremony_id: int,
    db: Session = Depends(database.get_db)
):
    ceremony = db.query(models.Ceremony).filter(models.Ceremony.id == ceremony_id).first()
    if not ceremony:
        raise HTTPException(status_code=404, detail="Ceremony not found")
    
    event_id = ceremony.event_id
    db.delete(ceremony)
    db.commit()
    return RedirectResponse(url=f"/epatrika/{event_id}#ceremonies-section", status_code=303)

# --- RSVP & Shagun Handlers ---

@app.post("/rsvp/{event_id}")
def post_rsvp(
    event_id: int,
    guest_name: str = Form(...),
    phone: str = Form(None),
    attending: str = Form("Yes"),
    guest_count: int = Form(1),
    message: str = Form(None),
    db: Session = Depends(database.get_db)
):
    rsvp = models.RSVP(
        event_id=event_id,
        guest_name=guest_name.strip(),
        phone=phone.strip() if phone else None,
        attending=attending,
        guest_count=guest_count if attending == "Yes" else 0,
        message=message.strip() if message else None
    )
    db.add(rsvp)
    db.commit()
    return RedirectResponse(url=f"/card/{event_id}?rsvp_done=1", status_code=303)

@app.post("/shagun/{event_id}")
def post_shagun(
    event_id: int,
    sender_name: str = Form(...),
    amount: float = Form(...),
    blessing_message: str = Form(None),
    db: Session = Depends(database.get_db)
):
    entry = models.ShagunEntry(
        event_id=event_id,
        sender_name=sender_name.strip(),
        amount=amount,
        blessing_message=blessing_message.strip() if blessing_message else None
    )
    db.add(entry)
    db.commit()
    return RedirectResponse(url=f"/epatrika/{event_id}?shagun_sent=1", status_code=303)

# --- Wishlist & Registry Handlers ---

@app.post("/registry/add/{event_id}")
def add_registry_item(
    event_id: int,
    item_name: str = Form(...),
    category: str = Form("Home"),
    target_amount: float = Form(...),
    db: Session = Depends(database.get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Wedding event not found")

    new_item = models.RegistryItem(
        event_id=event.id,
        item_name=item_name.strip(),
        category=category.strip(),
        target_amount=target_amount,
        collected_amount=0.0,
        is_claimed=False
    )
    db.add(new_item)
    db.commit()
    return RedirectResponse(url=f"/epatrika/{event_id}#registry-section", status_code=303)

@app.post("/registry/contribute/{item_id}")
def contribute_registry(
    item_id: int,
    contributor_name: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(database.get_db)
):
    item = db.query(models.RegistryItem).filter(models.RegistryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registry item not found")

    item.collected_amount += amount
    if item.collected_amount >= item.target_amount:
        item.is_claimed = True
        item.claimed_by = contributor_name
    db.commit()
    return RedirectResponse(url=f"/epatrika/{item.event_id}?gift_sent=1", status_code=303)

@app.post("/registry/delete/{item_id}")
def delete_registry_item(
    item_id: int,
    db: Session = Depends(database.get_db)
):
    item = db.query(models.RegistryItem).filter(models.RegistryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return RedirectResponse(url=f"/admin", status_code=303)
