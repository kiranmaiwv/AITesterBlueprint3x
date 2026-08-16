# 🧪 ETL QA Buddy

> **AI-powered ETL data-quality testing dashboard** — describe a data-quality
> check in plain English, let AI generate a runnable `pytest` test, execute it
> against a sample SQLite ETL database, and see PASS/FAIL results instantly.

---

## 📖 Project Title

**ETL QA Buddy** — an AI assistant for ETL / data-warehouse QA engineers.

---

## ❗ Problem Statement

ETL pipelines move millions of rows between systems every day. When data quality
breaks — NULLs in critical columns, duplicate keys, broken foreign-key
relationships, suspicious zero-value transactions, or partially-loaded pipeline
runs — the damage is silent and expensive.

Writing data-quality tests by hand is slow and repetitive:

- Every check (null check, duplicate check, referential integrity, row counts,
  business rules) has to be hand-coded as SQL + assertions.
- QA engineers spend more time writing boilerplate `pytest` than actually
  reasoning about data quality.
- Non-engineers (analysts, product owners) can describe what they want checked
  in plain English but can't turn it into an executable test.

**There is no fast bridge between "what should be true about my data" (English)
and "an executable, repeatable test" (pytest + SQL).**

---

## 💡 Solution

ETL QA Buddy closes that gap:

1. **Describe** a data-quality rule in plain English
   (e.g. *"check that all customer emails are unique"*).
2. **Generate** — the backend calls **OpenAI GPT-4o-mini** to produce a single,
   runnable `pytest` function that queries the database with `sqlite3`.
3. **Run** — the generated test is executed safely against a realistic sample
   SQLite ETL database and returns **PASS/FAIL** with full output.
4. **Regression suite** — a pre-written suite of 18 ETL QA tests
   (null, duplicate, referential-integrity, data-type, row-count and
   transformation checks) can be run with one click.

The sample database ships with **intentional data-quality defects**, so the suite
demonstrates real value out of the box — some tests **fail on purpose** to show
the tool catching genuine issues:

| Injected defect | Test that catches it |
| --- | --- |
| Order `#13` has `total_amount = 0.0` | `test_order_total_positive` ❌ |
| Two customers share `alice.johnson@example.com` | `test_customer_email_unique` ❌ |
| 2 customers with `NULL` phone | (visible in schema / null checks) |
| ETL log run marked `partial` (`rows_extracted != rows_loaded`) | inspectable via `/schema` + transformation checks |

> ✅ If no `OPENAI_API_KEY` is configured, the generator automatically falls back
> to a deterministic template so the app still works end-to-end.

---

## 🏗️ Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | Next.js 14 (App Router) · React 18 · TypeScript · dark-theme CSS — deployable to **Vercel** |
| **Backend** | FastAPI · Uvicorn · Pydantic (runs **locally**, no Docker) |
| **AI** | OpenAI `gpt-4o-mini` (with template fallback) |
| **Database** | **SQLite** (zero-setup, file-based — no external DB) |
| **Testing** | pytest · pytest-json-report |
| **Language** | Python 3.10+ · TypeScript |

### Architecture

```
                    ┌───────────────────────────────────────┐
                    │   Next.js Frontend (Vercel)            │
                    │   • Schema Explorer                    │
                    │   • AI Test Generator                  │
                    │   • Full Test Suite Results            │
                    └───────────────┬───────────────────────┘
                                    │  HTTP (NEXT_PUBLIC_BACKEND_URL)
                                    ▼
                    ┌───────────────────────────────────────┐
                    │   FastAPI Backend (local, no Docker)   │
                    │   GET  /health                         │
                    │   GET  /schema                         │
                    │   POST /generate-test  ── OpenAI ──►   │
                    │   POST /run-test       ── pytest ──►   │
                    │   GET  /run-all-tests  ── pytest ──►   │
                    └───────────────┬───────────────────────┘
                                    │  sqlite3
                                    ▼
                    ┌───────────────────────────────────────┐
                    │   SQLite DB  (backend/database/…)      │
                    │   customers · products · orders        │
                    │   order_items · etl_log                │
                    └───────────────────────────────────────┘
                                    ▲
                    ┌───────────────┴───────────────────────┐
                    │   tests/  (pre-written pytest suite)   │
                    └───────────────────────────────────────┘
```

---

## 🚀 How to Run

### Prerequisites
- Python **3.10+** and `pip`
- Node.js **18+** and `npm`

### 1. Backend + Database (local)

```bash
cd backend

# (recommended) create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# install dependencies (no Docker needed)
pip install -r requirements.txt

# configure environment
cp .env.example .env
#   → edit .env and add your OPENAI_API_KEY (optional; falls back to template)

# create and populate the SQLite database
python database/setup_db.py

# start the API on http://localhost:8000
uvicorn main:app --reload --port 8000
```

Quick smoke test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/schema
```

### 2. Run the test suite from the CLI

```bash
# from the project root
pytest tests/ -v
# Expected: 16 passed, 2 failed  (the 2 failures are intentional demo defects)
```

### 3. Frontend (local dev)

```bash
cd frontend
npm install
cp .env.example .env.local        # NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
npm run dev
# open http://localhost:3000
```

---

## 🌐 Demo (Vercel link)

The **frontend** is designed for one-click Vercel deployment. The **backend runs
locally** (Vercel hosts the UI only), so after deploying set the frontend's
`NEXT_PUBLIC_BACKEND_URL` to wherever your FastAPI server is reachable.

**Live demo:** `https://<your-project>.vercel.app`
_(replace with your Vercel URL after deploying — see steps below)_

### Deploy the frontend to Vercel

1. Push this repository to GitHub (repo name: **`ETL_QA_Buddy`**).
2. Go to **[vercel.com](https://vercel.com) → New Project → Import** your repo.
3. Vercel auto-detects Next.js. The included `vercel.json` sets:
   - Install: `cd frontend && npm install`
   - Build: `cd frontend && npm run build`
   - Output: `frontend/.next`
4. Add an environment variable in the Vercel dashboard:
   - `NEXT_PUBLIC_BACKEND_URL` = the URL where your local/remote FastAPI backend
     is reachable (e.g. an [ngrok](https://ngrok.com) tunnel to `localhost:8000`).
5. Click **Deploy**. Your UI goes live at `https://<your-project>.vercel.app`.

> Because the backend is local-only, use a tunnel (ngrok / Cloudflare Tunnel) to
> expose `http://localhost:8000` if you want the deployed Vercel UI to reach it.

---

## 🖥️ How to Use the AI Test Generator

1. Open the dashboard — the **Schema Explorer** (left) auto-loads all 5 tables
   and row counts from `GET /schema`.
2. In **AI Test Generator** (center), type a plain-English rule or click an
   example chip.
3. Click **Generate Test** → GPT-4o-mini returns a runnable `pytest` function,
   shown in a code block.
4. Click **Run This Test** → the test executes against the SQLite DB and shows
   **PASS/FAIL** with output.
5. Click **Run All Tests** (bottom) → the full pre-written suite runs and results
   appear as a PASS/FAIL table with a summary (Total / Passed / Failed).

### Sample test descriptions to try
- `Check all customer emails are unique`  *(will FAIL — soft duplicate injected)*
- `Verify no NULL values in order total_amount`
- `Ensure all order customer_ids exist in customers table`
- `Check ETL log has no failed pipeline runs`
- `Validate all product prices are greater than zero`

---

## 📸 Screenshots

### 1. Dashboard — Schema Explorer + AI Test Generator
![Dashboard](docs/01-dashboard.png)

### 2. AI-generated pytest test from a plain-English description
![Generate Test](docs/02-generate-test.png)

### 3. Full test suite results (16 passed, 2 intentional failures)
![Test Results](docs/03-test-results.png)

---

## 🔌 Backend API Reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET`  | `/health` | Health check + DB status |
| `GET`  | `/schema` | Returns all tables, columns, types, row counts |
| `POST` | `/generate-test` | `{ "description": "..." }` → `{ "test_code": "..." }` |
| `POST` | `/run-test` | `{ "test_code": "..." }` → `{ "passed", "output", "error" }` |
| `GET`  | `/run-all-tests` | Runs the full `tests/` suite → JSON summary + per-test results |

---

## 🗄️ Sample Database Schema

| Table | Rows | Purpose |
| --- | --- | --- |
| `customers` | 20 | Customer master data |
| `products` | 15 | Product catalog |
| `orders` | 30 | Customer orders |
| `order_items` | 50 | Line items per order |
| `etl_log` | 10 | Simulated ETL pipeline run metadata |

---

## 🧪 Pre-written Test Suite (`tests/`)

| File | Tests |
| --- | --- |
| `test_null_checks.py` | email / total_amount / country NOT NULL |
| `test_duplicate_checks.py` | unique customer_id, email, order_id |
| `test_referential_integrity.py` | order→customer, item→order, item→product FKs |
| `test_data_types.py` | positive prices / totals, non-negative stock |
| `test_row_counts.py` | min customers / products, every order has items |
| `test_transformations.py` | no failed ETL logs, valid statuses, valid flags |

---

## 🔐 Environment Variables Reference

### `backend/.env`
| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API key for AI test generation (optional — template fallback if unset) | — |
| `DATABASE_PATH` | Path to the SQLite database file | `./database/etl_qa.db` |

### `frontend/.env.local`
| Variable | Description | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_BACKEND_URL` | URL of the FastAPI backend | `http://localhost:8000` |

> ⚠️ Only `.env.example` files are committed. **Never commit real secrets** —
> `.env` files and the generated `etl_qa.db` are git-ignored.

---

## 📁 Project Structure

```
ETL_QA_Buddy/
├── frontend/                 # Next.js app → Vercel
│   ├── app/                  # App Router (layout, page, globals.css)
│   └── components/           # TestGenerator, TestResults, SampleSchema
├── backend/                  # FastAPI backend (local)
│   ├── main.py               # API endpoints
│   ├── database/setup_db.py  # Creates + populates SQLite DB
│   └── services/             # ai_generator.py, test_runner.py
├── tests/                    # Pre-written pytest ETL QA suite
├── docs/                     # Screenshots
├── vercel.json               # Vercel config (frontend)
├── .gitignore
└── README.md
```

---

## 📝 License

MIT — free to use, modify, and share.
