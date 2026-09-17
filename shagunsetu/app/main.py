import io
import re
import base64
from datetime import datetime, date
from urllib.parse import quote

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models
from .database import engine, get_db, Base

import qrcode

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShagunSetu")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def slugify(bride: str, groom: str, db: Session) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", f"{groom}-weds-{bride}".lower()).strip("-")
    slug = base
    i = 2
    while db.query(models.Wedding).filter(models.Wedding.slug == slug).first():
        slug = f"{base}-{i}"
        i += 1
    return slug


def get_wedding_or_404(slug: str, db: Session) -> models.Wedding:
    wedding = db.query(models.Wedding).filter(models.Wedding.slug == slug).first()
    if not wedding:
        raise HTTPException(status_code=404, detail="Wedding not found")
    return wedding


def days_until(d: str):
    try:
        target = datetime.strptime(d, "%Y-%m-%d").date()
        return (target - date.today()).days
    except Exception:
        return None


THEMES = ["classic", "royal", "minimal", "floral"]
EVENT_TEMPLATES = ["Haldi & Mehendi", "Sangeet Night", "Pheras", "Reception"]
CATEGORIES = ["Home & Living", "Electronics", "Kitchen", "Honeymoon", "Experiences", "Other"]
PRESET_AMOUNTS = [501, 1101, 2101, 5001]


# ---------------------------------------------------------------- landing --
@app.get("/", response_class=HTMLResponse)
def landing(request: Request, db: Session = Depends(get_db)):
    recent = (
        db.query(models.Wedding)
        .order_by(models.Wedding.created_at.desc())
        .limit(6)
        .all()
    )
    return templates.TemplateResponse(
        "landing.html", {"request": request, "recent": recent}
    )


# ----------------------------------------------------------- create wizard --
@app.get("/create", response_class=HTMLResponse)
def create_wizard(request: Request):
    return templates.TemplateResponse(
        "wizard.html",
        {
            "request": request,
            "event_templates": EVENT_TEMPLATES,
            "categories": CATEGORIES,
        },
    )


@app.post("/api/weddings")
async def api_create_wedding(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    couple = payload.get("couple", {})
    settings = payload.get("settings", {})
    events_in = payload.get("events", [])
    registry_in = payload.get("registry", [])

    bride = couple.get("bride_name", "").strip()
    groom = couple.get("groom_name", "").strip()
    wdate = couple.get("wedding_date", "").strip()

    if not bride or not groom or not wdate:
        raise HTTPException(status_code=400, detail="Bride, groom and wedding date are required.")

    slug = slugify(bride, groom, db)

    wedding = models.Wedding(
        slug=slug,
        bride_name=bride,
        groom_name=groom,
        bride_family=couple.get("bride_family", ""),
        groom_family=couple.get("groom_family", ""),
        wedding_date=wdate,
        venue=couple.get("venue", ""),
        city=couple.get("city", ""),
        description=couple.get("description", ""),
        cover_image=couple.get("cover_image", ""),
        invitation_title=settings.get("invitation_title", f"{bride} & {groom}"),
        invocation=settings.get("invocation") or "|| \u0936\u094d\u0930\u0940 \u0917\u0923\u0947\u0936\u093e\u092f \u0928\u092e\u0903 ||",
        upi_id=settings.get("upi_id", ""),
        upi_name=settings.get("upi_name", "") or f"{bride} & {groom}",
        whatsapp_contact=settings.get("whatsapp_contact", ""),
        enable_shagun=bool(settings.get("enable_shagun", True)),
        enable_token=bool(settings.get("enable_token", True)),
        theme=settings.get("theme", "classic"),
    )
    db.add(wedding)
    db.flush()

    for ev in events_in:
        if not ev.get("name"):
            continue
        db.add(models.Event(
            wedding_id=wedding.id,
            name=ev.get("name", ""),
            date=ev.get("date", ""),
            time=ev.get("time", ""),
            venue=ev.get("venue", ""),
            dress_code=ev.get("dress_code", ""),
            muhurat=ev.get("muhurat", ""),
            maps_url=ev.get("maps_url", ""),
        ))

    for item in registry_in:
        if not item.get("title"):
            continue
        db.add(models.WishlistItem(
            wedding_id=wedding.id,
            title=item.get("title", ""),
            target_amount=float(item.get("target_amount") or 0),
            category=item.get("category", "Other"),
            gift_type=item.get("gift_type", "Exclusive Gift"),
        ))

    db.commit()
    db.refresh(wedding)

    return {"slug": wedding.slug, "admin_url": f"/admin/{wedding.slug}", "public_url": f"/w/{wedding.slug}"}


# ------------------------------------------------------------------- admin --
@app.get("/admin/{slug}", response_class=HTMLResponse)
def admin_dashboard(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)

    rsvp_count = db.query(func.count(models.RSVP.id)).filter(models.RSVP.wedding_id == wedding.id).scalar()
    attending = db.query(func.count(models.RSVP.id)).filter(
        models.RSVP.wedding_id == wedding.id, models.RSVP.attending == True  # noqa: E712
    ).scalar()
    expected_guests = db.query(
        func.coalesce(func.sum(models.RSVP.adult_count + models.RSVP.child_count), 0)
    ).filter(models.RSVP.wedding_id == wedding.id, models.RSVP.attending == True).scalar()  # noqa: E712
    registry_count = db.query(func.count(models.WishlistItem.id)).filter(
        models.WishlistItem.wedding_id == wedding.id
    ).scalar()
    shagun_count = db.query(func.count(models.Shagun.id)).filter(models.Shagun.wedding_id == wedding.id).scalar()
    shagun_total = db.query(func.coalesce(func.sum(models.Shagun.amount), 0)).filter(
        models.Shagun.wedding_id == wedding.id
    ).scalar()

    rsvps = db.query(models.RSVP).filter(models.RSVP.wedding_id == wedding.id).order_by(
        models.RSVP.created_at.desc()
    ).all()
    shaguns = db.query(models.Shagun).filter(models.Shagun.wedding_id == wedding.id).order_by(
        models.Shagun.created_at.desc()
    ).all()
    blessings = db.query(models.Blessing).filter(models.Blessing.wedding_id == wedding.id).order_by(
        models.Blessing.created_at.desc()
    ).all()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "wedding": wedding,
            "rsvp_count": rsvp_count,
            "attending": attending,
            "expected_guests": int(expected_guests or 0),
            "registry_count": registry_count,
            "shagun_count": shagun_count,
            "shagun_total": shagun_total,
            "rsvps": rsvps,
            "shaguns": shaguns,
            "blessings": blessings,
            "categories": CATEGORIES,
        },
    )


@app.post("/admin/{slug}/events/add")
async def admin_add_event(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    form = await request.form()
    db.add(models.Event(
        wedding_id=wedding.id,
        name=form.get("name", ""),
        date=form.get("date", ""),
        time=form.get("time", ""),
        venue=form.get("venue", ""),
        dress_code=form.get("dress_code", ""),
        muhurat=form.get("muhurat", ""),
        maps_url=form.get("maps_url", ""),
    ))
    db.commit()
    return RedirectResponse(f"/admin/{slug}", status_code=303)


@app.post("/admin/{slug}/events/{event_id}/delete")
def admin_delete_event(slug: str, event_id: str, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    ev = db.query(models.Event).filter(models.Event.id == event_id, models.Event.wedding_id == wedding.id).first()
    if ev:
        db.delete(ev)
        db.commit()
    return RedirectResponse(f"/admin/{slug}", status_code=303)


@app.post("/admin/{slug}/registry/add")
async def admin_add_gift(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    form = await request.form()
    db.add(models.WishlistItem(
        wedding_id=wedding.id,
        title=form.get("title", ""),
        target_amount=float(form.get("target_amount") or 0),
        category=form.get("category", "Other"),
        gift_type=form.get("gift_type", "Exclusive Gift"),
    ))
    db.commit()
    return RedirectResponse(f"/admin/{slug}", status_code=303)


@app.post("/admin/{slug}/registry/{item_id}/delete")
def admin_delete_gift(slug: str, item_id: str, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    item = db.query(models.WishlistItem).filter(
        models.WishlistItem.id == item_id, models.WishlistItem.wedding_id == wedding.id
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(f"/admin/{slug}", status_code=303)


@app.post("/admin/{slug}/edit")
async def admin_edit_wedding(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    form = await request.form()
    for field in [
        "bride_name", "groom_name", "bride_family", "groom_family", "wedding_date",
        "venue", "city", "description", "invitation_title", "invocation",
        "upi_id", "upi_name", "whatsapp_contact", "theme",
    ]:
        if field in form:
            setattr(wedding, field, form.get(field))
    wedding.enable_shagun = "enable_shagun" in form
    wedding.enable_token = "enable_token" in form
    db.commit()
    return RedirectResponse(f"/admin/{slug}", status_code=303)


# --------------------------------------------------------------- share card --
@app.get("/w/{slug}/card", response_class=HTMLResponse)
def share_card(slug: str, request: Request, layout: str = "classic", db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    if layout not in THEMES:
        layout = "classic"
    return templates.TemplateResponse(
        "card.html", {"request": request, "wedding": wedding, "layout": layout}
    )


# ------------------------------------------------------------------ public --
@app.get("/w/{slug}", response_class=HTMLResponse)
def public_epatrika(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    events = db.query(models.Event).filter(models.Event.wedding_id == wedding.id).all()
    registry = db.query(models.WishlistItem).filter(models.WishlistItem.wedding_id == wedding.id).all()
    blessings = db.query(models.Blessing).filter(models.Blessing.wedding_id == wedding.id).order_by(
        models.Blessing.created_at.desc()
    ).limit(12).all()

    return templates.TemplateResponse(
        "epatrika.html",
        {
            "request": request,
            "wedding": wedding,
            "events": events,
            "registry": registry,
            "blessings": blessings,
            "preset_amounts": PRESET_AMOUNTS,
            "days_left": days_until(wedding.wedding_date),
        },
    )


@app.post("/w/{slug}/rsvp")
async def submit_rsvp(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    data = await request.json()

    phone = (data.get("phone") or "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required.")

    existing = db.query(models.RSVP).filter(
        models.RSVP.wedding_id == wedding.id, models.RSVP.phone == phone
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="An RSVP already exists for this phone number.")

    rsvp = models.RSVP(
        wedding_id=wedding.id,
        guest_name=data.get("guest_name", ""),
        phone=phone,
        attending=bool(data.get("attending", True)),
        adult_count=int(data.get("adult_count") or 1),
        child_count=int(data.get("child_count") or 0),
        events=",".join(data.get("events") or []),
        diet=data.get("diet", "Pure Vegetarian"),
        message=data.get("message", ""),
    )
    db.add(rsvp)
    db.commit()
    return {"ok": True}


@app.post("/w/{slug}/shagun")
async def submit_shagun(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    data = await request.json()

    amount = float(data.get("amount") or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Enter a valid amount.")
    token = bool(data.get("token_included", False))
    total = amount + (1 if token else 0)

    shagun = models.Shagun(
        wedding_id=wedding.id,
        sender_name=data.get("sender_name") or "A well-wisher",
        amount=total,
        token_included=token,
        message=data.get("message", ""),
        payment_status="initiated",
    )
    db.add(shagun)
    db.commit()

    upi_link = ""
    if wedding.upi_id:
        upi_link = (
            f"upi://pay?pa={quote(wedding.upi_id)}&pn={quote(wedding.upi_name or 'Wedding')}"
            f"&am={total}&cu=INR&tn={quote('Wedding Shagun')}"
        )

    return {"ok": True, "upi_link": upi_link, "amount": total}


@app.get("/w/{slug}/upi-qr")
def upi_qr(slug: str, amount: float = 0, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    if not wedding.upi_id:
        raise HTTPException(status_code=400, detail="No UPI ID configured for this wedding.")
    upi_link = (
        f"upi://pay?pa={quote(wedding.upi_id)}&pn={quote(wedding.upi_name or 'Wedding')}"
        f"&am={amount}&cu=INR&tn={quote('Wedding Shagun')}"
    )
    img = qrcode.make(upi_link)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/w/{slug}/page-qr")
def page_qr(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    base = str(request.base_url).rstrip("/")
    url = f"{base}/w/{wedding.slug}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.post("/w/{slug}/gift/{item_id}/claim")
async def claim_gift(slug: str, item_id: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    data = await request.json()
    item = db.query(models.WishlistItem).filter(
        models.WishlistItem.id == item_id, models.WishlistItem.wedding_id == wedding.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gift not found.")

    if item.gift_type == "Group Gift":
        contribution = float(data.get("amount") or 0)
        if contribution <= 0:
            raise HTTPException(status_code=400, detail="Enter a contribution amount.")
        item.raised_amount = (item.raised_amount or 0) + contribution
        if item.raised_amount >= item.target_amount and item.target_amount > 0:
            item.is_claimed = True
        db.commit()
        return {"ok": True, "raised_amount": item.raised_amount, "target_amount": item.target_amount}
    else:
        if item.is_claimed:
            raise HTTPException(status_code=409, detail="This gift has already been claimed.")
        item.is_claimed = True
        item.claimed_by = data.get("name", "A guest")
        db.commit()
        return {"ok": True}


@app.post("/w/{slug}/blessing")
async def submit_blessing(slug: str, request: Request, db: Session = Depends(get_db)):
    wedding = get_wedding_or_404(slug, db)
    data = await request.json()
    message = (data.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Blessing message cannot be empty.")
    blessing = models.Blessing(
        wedding_id=wedding.id,
        name=data.get("name") or "A well-wisher",
        message=message,
    )
    db.add(blessing)
    db.commit()
    return {"ok": True}
