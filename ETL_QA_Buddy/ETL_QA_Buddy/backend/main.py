"""
main.py — FastAPI backend for ETL QA Buddy.

Endpoints:
  GET  /health          — health check
  GET  /schema          — DB schema as JSON (tables, columns, types)
  POST /generate-test   — NL description -> generated pytest code (OpenAI GPT-4o-mini)
  POST /run-test        — run provided pytest code against the SQLite DB
  GET  /run-all-tests   — run the full pytest suite from tests/

Run locally:
  cd backend
  pip install -r requirements.txt
  python database/setup_db.py
  uvicorn main:app --reload --port 8000
"""

import os
import sqlite3

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.ai_generator import generate_test_code
from services.test_runner import run_all_tests, run_single_test

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, "database", "etl_qa.db")
DB_PATH = os.environ.get("DATABASE_PATH")
if not DB_PATH or not os.path.isabs(DB_PATH):
    # Resolve relative DATABASE_PATH against the backend directory.
    DB_PATH = os.path.join(BASE_DIR, os.environ.get("DATABASE_PATH", "database/etl_qa.db")) \
        if os.environ.get("DATABASE_PATH") else DEFAULT_DB

app = FastAPI(title="ETL QA Buddy API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    description: str


class RunTestRequest(BaseModel):
    test_code: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "db_exists": os.path.exists(DB_PATH), "db_path": DB_PATH}


@app.get("/schema")
def get_schema():
    """Return the database schema: each table with its columns and types."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=404,
            detail="Database not found. Run `python database/setup_db.py` first.",
        )

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row[0] for row in cur.fetchall()]

        schema = []
        for table in table_names:
            cur.execute(f"PRAGMA table_info({table})")
            columns = []
            for col in cur.fetchall():
                # PRAGMA table_info: (cid, name, type, notnull, dflt_value, pk)
                columns.append({
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "primary_key": bool(col[5]),
                })
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cur.fetchone()[0]
            schema.append({"table": table, "columns": columns, "row_count": row_count})

        return {"tables": schema}
    finally:
        conn.close()


@app.post("/generate-test")
def generate_test(req: GenerateRequest):
    """Generate a pytest test function from a natural-language description."""
    if not req.description or not req.description.strip():
        raise HTTPException(status_code=400, detail="description is required")
    try:
        code = generate_test_code(req.description)
        return {"test_code": code}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/run-test")
def run_test(req: RunTestRequest):
    """Run a single provided pytest test against the SQLite database."""
    if not req.test_code or not req.test_code.strip():
        raise HTTPException(status_code=400, detail="test_code is required")
    result = run_single_test(req.test_code)
    return result


@app.get("/run-all-tests")
def run_all():
    """Run the full pre-written pytest suite and return structured results."""
    return run_all_tests()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
