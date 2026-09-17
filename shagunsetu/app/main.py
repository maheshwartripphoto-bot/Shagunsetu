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

# Ensure tables exist
models.Base.metadata.create_all(bind=database.engine)

# Static & Template mounting with absolute paths to prevent 404s
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
def page_landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/wizard", response_class=HTMLResponse)
def page_wizard(request: Request):
    return templates.TemplateResponse("wizard.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
def page_admin(request: Request, db: Session = Depends(database.get_db)):
    events = db.query(models.Event).order_by(models.Event.id.desc()).all()
    return templates.TemplateResponse("admin.html", {"request": request, "events": events})

@app.get("/card/{event_id}", response_class=HTMLResponse)
def page_card(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Wedding invitation not found")
    return templates.TemplateResponse("card.html", {"request": request, "event": event})

@app.get("/epatrika/{event_id}", response_class=HTMLResponse)
def page_epatrika(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="E-Patrika not found")
    return templates.TemplateResponse("epatrika.html", {"request": request, "event": event})

# --- Form Action Endpoints ---

@app.post("/create")
def create_event(
    groom_name: str = Form(...),
    bride_name: str = Form(...),
    event_date: str = Form(...),
    muhurat_time: str = Form(None),
    venue: str = Form(...),
    host_family: str = Form(None),
    db: Session = Depends(database.get_db)
):
    event = models.Event(
        groom_name=groom_name.strip(),
        bride_name=bride_name.strip(),
        event_date=str(event_date),
        muhurat_time=muhurat_time.strip() if muhurat_time else None,
        venue=venue.strip(),
        host_family=host_family.strip() if host_family else None
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return RedirectResponse(url=f"/card/{event.id}", status_code=303)

@app.post("/rsvp/{event_id}")
def submit_rsvp(
    event_id: int,
    guest_name: str = Form(...),
    phone: str = Form(None),
    attending: str = Form("Yes"),
    guest_count: int = Form(1),
    message: str = Form(None),
    db: Session = Depends(database.get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Wedding event does not exist")

    rsvp = models.RSVP(
        event_id=event.id,
        guest_name=guest_name.strip(),
        phone=phone.strip() if phone else None,
        attending=attending,
        guest_count=guest_count if attending == "Yes" else 0,
        message=message.strip() if message else None
    )
    db.add(rsvp)
    db.commit()
    return RedirectResponse(url=f"/card/{event_id}?rsvp_success=1", status_code=303)
