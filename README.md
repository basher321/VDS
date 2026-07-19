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
