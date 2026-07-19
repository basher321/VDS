# VDS — VAT Deduction at Source (Mushak-6.6 certificates)

A local, single-organization tool for tracking VAT-deducted-at-source on supplier invoices and
issuing Mushak-6.6 withholding tax certificates (Bangladesh NBR form) as PDFs.

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Next.js (React) + TypeScript

## Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) (includes npm)
- [PostgreSQL 14+](https://www.postgresql.org/download/), running locally

## 1. Clone

```
git clone https://github.com/basher321/VDS.git
cd VDS
```

## 2. Database

Create an empty PostgreSQL database for the app:

```
psql -U postgres -c "CREATE DATABASE vds_db;"
```

(Use whatever database name/user/password you like — you'll put them in `.env` in the next step.)

> **Note:** `backend/migrations/*.sql` are placeholder files and don't contain real SQL. The
> schema is created from the SQLAlchemy models instead, via `scripts/setup_db.py` in step 3 —
> don't try to run the `.sql` files.

## 3. Backend

```
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env` from the example and edit it to match your database:

```
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

```ini
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/vds_db
SECRET_KEY=change-this-to-a-long-random-string
DATA_DIR=./data
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

Create the tables and the first login user:

```
python scripts/setup_db.py
```

This is safe to re-run any time. By default it creates:

- **username:** `admin`
- **password:** `Admin123`

(Override with `python scripts/setup_db.py --username you --password yourpass`.)

Start the API:

```
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Check it's up: http://127.0.0.1:8000/api/health should return `{"status":"ok",...}`.

## 4. Frontend

In a second terminal:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and log in with the credentials from step 3.

## 5. First-time setup inside the app

A brand-new database has no issuer (withholding entity) yet, which will make **Settings** and
**Import** look stuck ("Loading…" / "Select an issuer first"). Fix this once:

1. Log in.
2. Go to **Settings → Issuers**, click **+ Add issuer**, and create your organization.
3. Fill in its address, BIN, officer/signatory details, and (optionally) upload its seal,
   letterhead logo, and signature image.
4. Go to **Import** and upload a Mushak-6.6 "Summary" workbook to start staging invoices.

## Windows convenience scripts

`start-backend.bat` and `start-frontend.bat` in the repo root create the venv / install deps
and start each server, if you'd rather not run the commands above by hand. Run
`scripts/setup_db.py` yourself first, though — the batch files don't do that.

## Deploying (Render + Supabase)

Database on [Supabase](https://supabase.com), backend and frontend as two separate
[Render](https://render.com) web services.

### A. Database (Supabase)

1. Create a new project at [supabase.com/dashboard/new](https://supabase.com/dashboard/new)
   and set a database password (save it).
2. Once it's provisioned: **Project Settings → Database → Connection string**, and switch the
   connection type dropdown to **Session pooler** (not "Direct connection" — Supabase's direct
   connections are IPv6-only, which fails to resolve from most external hosts including Render;
   the Session pooler is IPv4-compatible and works with SQLAlchemy's persistent connections).
   Copy that string — it looks like:
   `postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-<n>-<region>.pooler.supabase.com:5432/postgres`
3. Change the scheme from `postgresql://` to `postgresql+psycopg2://` (this app uses the
   `psycopg2` driver) and fill in your password. This is your production `DATABASE_URL`.
4. Create the tables and admin user by running the setup script **once**, pointed at Supabase.
   From your machine, with the backend venv active:
   ```
   cd backend
   # Windows (PowerShell): $env:DATABASE_URL = "postgresql+psycopg2://postgres.xxxx:...@aws-...pooler.supabase.com:5432/postgres"
   # macOS/Linux:          export DATABASE_URL="postgresql+psycopg2://postgres.xxxx:...@aws-...pooler.supabase.com:5432/postgres"
   python scripts/setup_db.py --password YOUR_OWN_ADMIN_PASSWORD
   ```
   Run this from your own machine rather than pasting the connection string to anyone else —
   it contains your database password.

### B. Backend (Render web service)

Easiest: **New +** → **Blueprint** → point at `https://github.com/basher321/VDS.git` → Render
reads `render.yaml` at the repo root and proposes both services at once. It'll prompt you for
the two secret values below since they're marked `sync: false` in that file.

Or by hand, via **New +** → **Web Service** → connect the repo:

| Field | Value |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/health` |

Environment variables:

| Key | Value |
|---|---|
| `DATABASE_URL` | the `postgresql+psycopg2://...` string from step A |
| `SECRET_KEY` | any long random string (e.g. generate one with `python -c "import secrets; print(secrets.token_hex(32))"`) — **not** the placeholder in `.env.example` |
| `DATA_DIR` | `./data` |
| `CORS_ORIGINS` | `https://vds-frontend.onrender.com,http://localhost:3000` (update the first URL once you know your actual frontend URL — see below) |

Once deployed, Render gives you a URL like `https://vds-backend.onrender.com`. Confirm it
works: `https://<your-backend>.onrender.com/api/health` should return `{"status":"ok",...}`.

### C. Frontend (Render web service)

Same repo, second service (or created automatically by the Blueprint above):

| Field | Value |
|---|---|
| Root Directory | `frontend` |
| Runtime | Node |
| Build Command | `npm install && npm run build` |
| Start Command | `npm run start` |

Environment variables:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE` | `https://<your-backend>.onrender.com` (the URL from step B — no trailing slash) |

`NEXT_PUBLIC_API_BASE` is baked in at **build time**, so set it before the first build; if you
change it later you need to trigger a new build, not just a restart.

### D. Wire the two together

Once both are deployed, go back to the **backend** service's `CORS_ORIGINS` env var and set it
to the frontend's actual URL (e.g. `https://vds-frontend.onrender.com`), then save — Render
will redeploy the backend with the updated value. Without this, the browser will block every
API call from the frontend with a CORS error.

### Caveats specific to this deployment

- **File storage is ephemeral.** Generated certificate PDFs, uploaded workbooks, and issuer
  seal/logo/signature images are stored on local disk (`backend/data/`). Render's free web
  services wipe local disk on every redeploy and when a free-tier instance spins down from
  inactivity. Fine for evaluation; for real use, either add a
  [Render persistent disk](https://render.com/docs/disks) to the backend service, or migrate
  file storage to Supabase Storage.
- **Certificate PDF font.** The renderer uses Garamond if it finds it at
  `C:\Windows\Fonts\GARA.TTF`; Render's Linux containers won't have that font, so certificates
  generated in production fall back to Times — layout and data are identical, just a different
  serif typeface than on a Windows machine with Garamond installed.
- **Free-tier cold starts.** Render's free web services spin down after ~15 minutes of
  inactivity; the first request after that takes 30–60 seconds to wake back up.

## Known limitations

- **Supplier email/WhatsApp contacts** have no UI yet — dispatch ("Send email"/"Send WhatsApp")
  is blocked for every supplier until a contact exists on that supplier's record.
- **Dispatch doesn't actually send anything** — even with a contact on file, "sent" just marks
  a status flag. There's no real SMTP or WhatsApp API call wired up yet.
- **Supplier BIN** can only be set via the import workbook's BIN column; there's no
  supplier-edit page.
- The **VDS rate master** (Settings) is a reference table only — the rate used per invoice
  always comes from the imported workbook's own "VAT Rate" column, not a lookup against it.
- Certificate PDFs use the **Garamond** font if it's installed on the machine generating them
  (`C:\Windows\Fonts\GARA.TTF`), falling back to Times otherwise.
