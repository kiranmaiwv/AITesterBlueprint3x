"""Demo (fixture) dataset for the claims_etl_v1 star schema.

Everything here is deterministic. ``100 rows`` for each of the six tables
(1 fact + 5 dims) is the contract the README advertises, so the fixtures are
built by the same code that the demo gateways read.

Why not hand-written CSVs? A CSV fixture that drifts from the canonical
registry (a column renamed, a code that no longer exists) silently corrupts
every downstream demo. Building the rows in code and writing them out means
the fixtures and the registry can never disagree.
"""

from __future__ import annotations

import csv
import hashlib
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from hc_etl_qa_crew.schema_registry.star_schema import REGISTRY

#: The six tables, in load order (dims before fact).
TABLE_NAMES = [spec.name for spec in REGISTRY]

#: Rows per table. The star-schema contract is 100 rows for EVERY table,
#: including the fact table, so reconciliation demos are easy to follow.
ROW_COUNT = 100

_FIRST = ["Ava", "Liam", "Noah", "Mia", "Ethan", "Sofia", "Lucas", "Isabella"]
_LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
_STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
_GENDERS = ["M", "F"]

_SPECIALTIES = ["Family Medicine", "Cardiology", "Pediatrics", "Orthopedics"]
_PROVIDER_TYPES = ["Physician", "Facility", "Pharmacy"]
_NETWORK = ["IN_NETWORK", "OUT_OF_NETWORK"]
_CHRONIC = ["Y", "N"]
_SERVICE_CATEGORIES = [
    "Evaluation & Management",
    "Procedure",
    "Radiology",
    "Laboratory",
]
_PLACES = ["Office", "Inpatient Hospital", "Outpatient Hospital", "Telehealth"]
_STATUSES = ["PAID", "DENIED", "PARTIAL", "PENDING"]
_DENIALS = ["", "", "", "AUTHORIZATION_REQUIRED", "NOT_COVERED", "COORDINATION_OF_BENEFITS"]

_Y1965 = date(1965, 1, 1)
_Y2019 = date(2019, 1, 1)
_Y2023 = date(2023, 1, 1)
_Y2024 = date(2024, 1, 1)
_Y2025 = date(2025, 1, 1)
_Y2026 = date(2026, 1, 1)

#: Rows the data-quality demo guarantees are present. The pytest suite that
#: ships with this repo asserts the ETL exposed these defects.
BAD_MEMBER_SK = 1002
BAD_PROVIDER_SK = 1005
BAD_DX_SK = 1009
BAD_SERVICE_SK = 1015
BAD_DATE_SK = 990001
NULL_GENDER_MEMBER_SK = 3
NULL_NETWORK_PROVIDER_SK = 5


def _mk_id(prefix: str, sk: int) -> str:
    """A stable natural key derived from the surrogate key."""
    digest = hashlib.sha1(f"{prefix}-{sk}".encode()).hexdigest()
    return f"{prefix}{int(digest[:8], 16) % 900000 + 100000}"


def _hash10(prefix: str, sk: int) -> str:
    digest = hashlib.sha1(f"{prefix}-{sk}".encode()).hexdigest()
    return digest[:10].upper()


def _rand_state(rng: random.Random) -> str:
    return _STATES[rng.randrange(len(_STATES))]


def _member_rows() -> list[dict]:
    rng = random.Random(42)
    rows: list[dict] = []
    for sk in range(1, ROW_COUNT + 1):
        state = _rand_state(rng)
        birth = _Y1965 + timedelta(days=rng.randrange(0, 55 * 365))
        enroll_start = _Y2023 + timedelta(days=rng.randrange(0, 730))
        enroll_end = enroll_start + timedelta(days=rng.randrange(180, 900))
        rows.append(
            {
                "member_sk": sk,
                "member_id": _mk_id("MEM", sk),
                "first_name": _FIRST[rng.randrange(len(_FIRST))],
                "last_name": _LAST[rng.randrange(len(_LAST))],
                "date_of_birth": birth,
                "gender": _GENDERS[rng.randrange(len(_GENDERS))],
                "state_code": state,
                "zip_code": f"{rng.randrange(10000, 99999):05d}",
                "enrollment_start_date": enroll_start,
                "enrollment_end_date": enroll_end,
                "etl_batch_id": "BATCH-2026-01-15-001",
                "etl_loaded_at": datetime(2026, 1, 15, 3, 0, 0),
            }
        )
    # Business rule 2: exactly one member is missing a gender at the source.
    target = next(r for r in rows if r["member_sk"] == NULL_GENDER_MEMBER_SK)
    target["gender"] = None
    return rows


def _provider_rows() -> list[dict]:
    rng = random.Random(7)
    rows: list[dict] = []
    for sk in range(1, ROW_COUNT + 1):
        contract_start = _Y2019 + timedelta(days=rng.randrange(0, 1200))
        contract_end = contract_start + timedelta(days=rng.randrange(365, 2500))
        rows.append(
            {
                "provider_sk": sk,
                "npi": _hash10("NPI", sk),
                "provider_name": f"{_LAST[rng.randrange(len(_LAST))]} Health {sk}",
                "provider_type": _PROVIDER_TYPES[rng.randrange(len(_PROVIDER_TYPES))],
                "specialty": _SPECIALTIES[rng.randrange(len(_SPECIALTIES))],
                "state_code": _rand_state(rng),
                "network_status": _NETWORK[rng.randrange(len(_NETWORK))],
                "contract_start_date": contract_start,
                "contract_end_date": contract_end,
                "etl_batch_id": "BATCH-2026-01-15-001",
                "etl_loaded_at": datetime(2026, 1, 15, 3, 0, 0),
            }
        )
    # Business rule 3: one provider row has no network_status at the source.
    target = next(r for r in rows if r["provider_sk"] == NULL_NETWORK_PROVIDER_SK)
    target["network_status"] = None
    return rows


def _diagnosis_rows() -> list[dict]:
    codes = [
        ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine", "Y"),
        ("I10", "Essential (primary) hypertension", "Circulatory", "Y"),
        ("J45.909", "Unspecified asthma", "Respiratory", "N"),
        ("M54.5", "Low back pain", "Musculoskeletal", "N"),
        ("F32.9", "Major depressive disorder, single episode", "Mental", "N"),
        ("Z00.00", "General adult medical examination", "Preventive", "N"),
    ]
    rows: list[dict] = []
    for sk in range(1, ROW_COUNT + 1):
        code, desc, category, chronic = codes[sk % len(codes)]
        rows.append(
            {
                "diagnosis_sk": sk,
                "icd10_code": code,
                "icd10_description": desc,
                "diagnosis_category": category,
                "chronic_flag": chronic,
                "etl_batch_id": "BATCH-2026-01-15-001",
                "etl_loaded_at": datetime(2026, 1, 15, 3, 0, 0),
            }
        )
    return rows


def _service_rows() -> list[dict]:
    cpts = [
        ("99213", "Office visit, established patient", "Evaluation & Management", "Office"),
        ("99214", "Office visit, established patient, high complexity", "Evaluation & Management", "Office"),
        ("93000", "Electrocardiogram complete", "Radiology", "Outpatient Hospital"),
        ("80053", "Comprehensive metabolic panel", "Laboratory", "Office"),
        ("71045", "Chest x-ray single view", "Radiology", "Outpatient Hospital"),
        ("J3420", "Vitamin B-12 injection", "Procedure", "Office"),
    ]
    rows: list[dict] = []
    for sk in range(1, ROW_COUNT + 1):
        cpt, desc, category, place = cpts[sk % len(cpts)]
        revenue = "" if sk % 3 == 0 else f"{300 + sk % 99:04d}"
        rows.append(
            {
                "service_sk": sk,
                "cpt_code": cpt,
                "cpt_description": desc,
                "service_category": category,
                "revenue_code": revenue or None,
                "place_of_service": place,
                "etl_batch_id": "BATCH-2026-01-15-001",
                "etl_loaded_at": datetime(2026, 1, 15, 3, 0, 0),
            }
        )
    return rows


def _time_rows() -> list[dict]:
    """One row per calendar date from 2023-01-01 .. 2025-12-31 (1096 rows)."""
    rows: list[dict] = []
    day = _Y2023
    end = date(2025, 12, 31)
    while day <= end:
        weekday = day.weekday()  # Monday=0
        rows.append(
            {
                "date_sk": int(day.strftime("%Y%m%d")),
                "full_date": day,
                "year": day.year,
                "month": day.month,
                "day": day.day,
                "quarter": (day.month - 1) // 3 + 1,
                "day_of_week_name": day.strftime("%A"),
                "is_weekend": "Y" if weekday >= 5 else "N",
                "is_holiday": "N",
                "etl_batch_id": "BATCH-2026-01-15-001",
                "etl_loaded_at": datetime(2026, 1, 15, 3, 0, 0),
            }
        )
        day += timedelta(days=1)
    return rows


def _claim_line_rows(member_rows: list[dict], provider_rows: list[dict]) -> list[dict]:
    """100 fact rows, each FK pointing at the demo members/providers.

    Purposely injects four defects so the shipped pytest suite has something
    to catch:
      * one claim line references a member_sk that does not exist (FK break)
      * one claim line references a provider_sk that does not exist
      * one claim line references a date_sk that is not in dim_time
      * one PAID claim line has a NULL allowed_amount (business rule break)
    """
    rng = random.Random(23)
    rows: list[dict] = []
    member_sks = [r["member_sk"] for r in member_rows]
    provider_sks = [r["provider_sk"] for r in provider_rows]
    sk = 1
    for idx in range(ROW_COUNT):
        member_sk = member_sks[rng.randrange(len(member_sks))]
        provider_sk = provider_sks[rng.randrange(len(provider_sks))]
        status = _STATUSES[rng.randrange(len(_STATUSES))]
        billed = round(rng.uniform(80.0, 2400.0), 2)
        if status == "PAID":
            allowed = billed
            paid = billed
        elif status == "PARTIAL":
            allowed = billed
            paid = round(billed * rng.uniform(0.5, 0.9), 2)
        else:  # DENIED or PENDING
            allowed = billed
            paid = 0.0
        denial = (
            _DENIALS[rng.randrange(len(_DENIALS))] or None
            if status == "DENIED"
            else None
        )
        if idx in (5, 17, 33, 61, 88):
            service_date = _Y2024 + timedelta(days=rng.randrange(0, 365))
        else:
            service_date = _Y2025 + timedelta(days=rng.randrange(0, 180))
        rows.append(
            {
                "claim_line_sk": sk,
                "claim_id": _mk_id("CLM", sk),
                "line_number": 1,
                "member_sk": member_sk,
                "provider_sk": provider_sk,
                "diagnosis_sk": rng.randrange(1, 7),
                "service_sk": rng.randrange(1, 7),
                "date_sk": int(service_date.strftime("%Y%m%d")),
                "service_date": service_date,
                "billed_amount": billed,
                "allowed_amount": allowed,
                "paid_amount": paid,
                "claim_status": status,
                "denial_reason": denial,
                "inserted_at": datetime(2026, 1, 15, 3, 0, 0),
                "etl_batch_id": "BATCH-2026-01-15-001",
                "etl_loaded_at": datetime(2026, 1, 15, 3, 0, 0),
            }
        )
        sk += 1
    rows[0]["member_sk"] = BAD_MEMBER_SK  # FK break: no such member
    rows[1]["provider_sk"] = BAD_PROVIDER_SK  # FK break: no such provider
    rows[2]["date_sk"] = BAD_DATE_SK  # FK break: not in dim_time
    rows[3]["allowed_amount"] = None  # business-rule break: PAID with no allowed
    rows[3]["claim_status"] = "PAID"
    return rows


# --------------------------------------------------------------------------
# Materialization
# --------------------------------------------------------------------------
def build_rows() -> dict[str, list[dict]]:
    """Return ``{table_name: [row, ...]}`` in registry load order."""
    members = _member_rows()
    providers = _provider_rows()
    return {
        "dim_member": members,
        "dim_provider": providers,
        "dim_diagnosis": _diagnosis_rows(),
        "dim_service": _service_rows(),
        "dim_time": _time_rows(),
        "fact_claim_line": _claim_line_rows(members, providers),
    }


def _clean_csv_cell(value):
    """Convert a row value for CSV/SQLite.

    None becomes a true NULL in SQLite; for the CSV it becomes an empty
    field. Dates render in ISO form, datetimes with a space separator.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


def write_fixtures(base_dir: Path | None = None) -> Path:
    """Write the deterministic CSV fixtures into ``<repo>/fixtures/datasets``."""
    target = (base_dir or Path(__file__).resolve().parents[3]) / "fixtures" / "datasets"
    target.mkdir(parents=True, exist_ok=True)
    rows_by_table = build_rows()
    for table_name, rows in rows_by_table.items():
        out = target / f"{table_name}.csv"
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {k: "" if v is None else _clean_csv_cell(v) for k, v in row.items()}
                )
    return target


def build_sqlite(target: Path | None = None) -> Path:
    """Materialize the demo star schema into a SQLite file for ``DATA_SOURCE_MODE=fixture``.

    The on-disk file lives under ``outputs/`` (gitignored). The fixture CSVs in
    ``fixtures/datasets`` remain the durable artifact; the SQLite database is a
    derived convenience.
    """
    db_path = target or (Path(__file__).resolve().parents[3] / "outputs" / "hc_etl_demo.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    try:
        rows_by_table = build_rows()
        for table_name, rows in rows_by_table.items():
            if not rows:
                continue
            columns = list(rows[0].keys())
            quoted = ", ".join(f'"{c}"' for c in columns)
            placeholders = ", ".join("?" for _ in columns)
            conn.execute(f'CREATE TABLE "{table_name}" ({quoted})')
            values = [
                [_clean_csv_cell(row[c]) for c in columns]
                for row in rows
            ]
            conn.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', values)
        conn.commit()
    finally:
        conn.close()
    return db_path

#: Convenience for scripts that want the demo SQLite path without building.
DEMO_SQLITE_PATH = Path(__file__).resolve().parents[3] / "outputs" / "hc_etl_demo.db"


def stamp() -> str:
    """One fixed timestamp used across the demo artifacts."""
    return "2026-01-15T03:00:00Z"
