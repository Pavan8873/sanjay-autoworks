# AutoCare — Automobile Service Management

A full-stack Django + PostgreSQL web application for car and bike service workshops. Manage customers, vehicles, inspection-based job cards, QR-coded inventory, GST billing, and renewal reminders end-to-end.

---

## Features

### 1. Customer & Vehicle Management
- Quick registration form captures customer + vehicle + first inspection in a single step
- Customer profile with multiple vehicles, full service history, and GSTIN field
- Vehicle profile tracks make, model, year, color, odometer, engine/chassis numbers
- Insurance, RC, and Pollution certificate expiry tracking

### 2. Inspection-driven Job Cards
- Auto-created from quick registration with inspection notes
- Mechanic assignment, work-to-do list, labor hours and rate
- Status workflow: Open → In Progress → Completed → Billed → Cancelled
- Auto-generated job number (e.g. `JC-202604-00007`)

### 3. QR-Coded Inventory
- Every part automatically gets a printable QR code on creation
- Built-in browser camera scanner (`html5-qrcode`) for instant SKU lookup
- Adding parts to a job card automatically deducts stock and records movement
- Removing a part restores stock and logs a reverse movement
- Low-stock alerts on the dashboard, restock workflow, supplier directory

### 4. GST Billing
- One-click "Complete & Bill" generates an invoice from the job card
- Auto-calculates parts subtotal, labor, manual charges, and GST (default 18%)
- Manual charge presets (General Service ₹500, Diagnostics ₹200, Wash ₹300, Pickup & Drop ₹250)
- Payment recording (Cash / UPI / Card / Bank / Pending)
- Printable tax invoice with shop branding

### 5. Reminders
- Auto-scheduled on job completion:
  - Annual service (1 year from completion)
  - Insurance renewal (15 days before expiry)
  - Pollution certificate renewal (15 days before expiry)
  - RC renewal (30 days before expiry)
- Channel selection: Email / SMS / WhatsApp
- Pending / Sent / Dismissed status tracking

### 6. Dashboard
- Customers, vehicles, open jobs, completed-today counters
- Monthly revenue and pending payment totals
- Low-stock parts panel
- Upcoming reminders for the next 30 days

---

## Tech Stack

| Layer        | Technology                                  |
|--------------|---------------------------------------------|
| Language     | Python 3.11                                 |
| Framework    | Django 5.0                                  |
| Database     | PostgreSQL                                  |
| Static files | WhiteNoise                                  |
| QR codes     | `qrcode` + Pillow (server) · `html5-qrcode` (client scan) |
| Forms        | `django-widget-tweaks`                      |
| Production   | Gunicorn                                    |

---

## Project Structure

```
django_app/
├── autoservice/        # Project settings, root URLs, WSGI
├── core/               # Dashboard, base template, seed command
├── customers/          # Customer + Vehicle models, quick-register flow
├── inventory/          # Part, Supplier, StockMovement, QR generation
├── jobcards/           # JobCard + JobCardPart, status workflow
├── billing/            # Invoice + ManualCharge, GST recalc, print view
├── reminders/          # Auto-scheduled service / insurance / RC / PUC reminders
├── templates/          # base.html + per-app templates
├── static/css/         # app.css
├── media/qrcodes/      # Generated QR images
└── manage.py
```

---

## Setup (Local)

### 1. Requirements
- Python 3.11+
- PostgreSQL 13+

### 2. Install dependencies
```bash
pip install Django==5.0.6 psycopg2-binary Pillow qrcode \
            django-widget-tweaks gunicorn whitenoise python-dotenv twilio
```

### 3. Environment variables
Set these (or export them in your shell):
```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DBNAME"
export SESSION_SECRET="change-me-to-a-long-random-string"
export DJANGO_DEBUG=1
export PGSSLMODE=disable        # only if your PG doesn't accept SSL
# Optional shop branding
export SHOP_NAME="AutoCare Service Center"
export SHOP_ADDRESS="123 Workshop Road, Bengaluru, KA 560001"
export SHOP_PHONE="+91 98765 43210"
export SHOP_GSTIN="29ABCDE1234F1Z5"
export GST_RATE=18
```

If `DATABASE_URL` is not set the app falls back to SQLite (`db.sqlite3`).

### 4. Migrate, seed, run
```bash
cd django_app
python manage.py migrate
python manage.py seed                       # creates admin/admin123 + sample data
python manage.py runserver 0.0.0.0:5000
```

Open http://localhost:5000/ and log in with **admin / admin123**.

---

## Running on Replit

The repo is pre-configured to run on Replit:
- Workflow `Django` runs the dev server on port 5000
- Production deployment runs Gunicorn (`autoservice.wsgi:application`)
- Build step runs `collectstatic` + `migrate`
- PostgreSQL is provisioned automatically via `DATABASE_URL`

Click **Run** to start the dev server, then click **Publish** to deploy.

---

## End-to-End Workflow

1. Customer arrives → **+ Quick Register** captures everything in one form, creating Job Card `JC-YYYYMM-XXXXX`.
2. Mechanic opens the job card, scans parts via QR or types SKUs (stock auto-decrements), logs labor hours.
3. Click **Complete & Bill** → invoice is generated, GST is computed, reminders are auto-scheduled.
4. Add manual charges from preset chips, record payment method, **Print** the tax invoice.
5. Reminders appear on the dashboard 30 days before due — send via Email / SMS / WhatsApp.

---

## Default Credentials

| Username | Password   |
|----------|-----------|
| admin    | admin123  |

Change them via Django admin (`/admin/`) or `python manage.py changepassword admin`.

---

## Customisation

| What            | Where                                         |
|-----------------|-----------------------------------------------|
| Shop branding   | Env vars (`SHOP_NAME`, `SHOP_ADDRESS`, etc.)  |
| GST rate        | Env var `GST_RATE` (default 18)               |
| Manual charges  | `billing/models.py` → `ManualCharge.PRESETS`  |
| Reminder rules  | `jobcards/views.py` → `complete()`            |
| Send channel    | `reminders/views.py` → `send()` (wire Twilio / SMTP / WhatsApp here) |

---

## License

MIT — use freely for commercial workshops.
