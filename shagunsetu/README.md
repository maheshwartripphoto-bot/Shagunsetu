# ShagunSetu — Digital Wedding Registry & E-Patrika (Prototype)

A working end-to-end prototype: create a wedding, share an invitation, and let guests RSVP,
send digital Shagun via UPI, claim gifts, and leave blessings.

## Run locally

```bash
cd shagunsetu
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000**

- Landing page → **✨ Create Your Wedding** to run the 5-step wizard
- After creation you land on `/admin/{slug}` (the couple's dashboard)
- The public invitation lives at `/w/{slug}`
- A shareable Save-the-Date card lives at `/w/{slug}/card`

Data is stored in a local SQLite file (`shagunsetu.db`), created automatically on first run.

## Deploying to Render

1. Push this folder to a GitHub repo.
2. Create a new **Web Service** on Render, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Persistence**: Render's free tier has an ephemeral filesystem, so the default
   SQLite file (`shagunsetu.db`) is wiped on every redeploy/restart. Two options:
   - **Persistent Disk** (paid instance, ≥ Starter): Settings → Disks → add a disk
     mounted at the project directory. SQLite then survives restarts.
   - **Render Postgres** (works on the free plan): create a free Postgres instance,
     copy its Internal Database URL, and set it as the `DATABASE_URL` environment
     variable on the web service. `app/database.py` already auto-detects
     `DATABASE_URL` and switches from SQLite to Postgres automatically — no code
     changes needed, `psycopg2-binary` is already in `requirements.txt`.
   - If you skip both, the app still works fine for a live demo — data just resets
     whenever the service redeploys or restarts, not on its own otherwise.

## What's implemented

- **Wizard**: couple details → settings (UPI, invocation, Shagun toggles, theme) →
  events (with quick-add templates) → gift registry → preview → create.
- **Admin dashboard**: overview stats, event/registry management, RSVP list, Shagun
  intents, blessings, Share Invitation modal, Edit Wedding modal.
- **Public E-Patrika**: hero, live countdown, story, events, RSVP form (duplicate-phone
  protected), digital Shagun (preset/custom amounts, ₹1 token, UPI deep link + QR),
  gift registry (exclusive claim + group-gift contribution with progress bar),
  blessings wall, share section (WhatsApp, copy link, native share).
- **Share Card**: 4 layout variants (Classic / Royal / Minimal / Floral) with an
  embedded QR back to the E-Patrika, downloadable as PNG via html2canvas.
- **UPI**: `upi://pay?...` deep link generated per transaction; Shagun is recorded as
  an *initiated/unverified* payment intent, matching the prototype's scope (no payment
  gateway integration).

## Not implemented (by design, for prototype scope)

- Real authentication (a `admin_pin` field exists on the Wedding model as a placeholder
  for a future login flow; the dashboard is currently reachable by anyone with the slug)
- Payment verification / webhook confirmation of UPI transactions
- Image upload (cover photo is a URL field, not a file upload)
- Add-to-calendar buttons

## Project structure

```
shagunsetu/
├── app/
│   ├── main.py            # FastAPI routes
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # DB session/engine
│   ├── templates/         # Jinja2 templates (landing, wizard, admin, epatrika, card)
│   └── static/             # CSS, JS
├── requirements.txt
└── README.md
```
