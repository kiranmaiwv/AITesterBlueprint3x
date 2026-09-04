"""Tests for the deterministic demo dataset (100-row star schema + seeded defects)."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from hc_etl_qa_crew.demo_loader.dataset import (
    BAD_DATE_SK,
    BAD_MEMBER_SK,
    BAD_PROVIDER_SK,
    DEMO_SQLITE_PATH,
    NULL_GENDER_MEMBER_SK,
    NULL_NETWORK_PROVIDER_SK,
    ROW_COUNT,
    build_rows,
    write_fixtures,
)


def test_each_table_has_100_rows_except_calendar_dim(demo_rows) -> None:
    assert len(demo_rows["dim_member"]) == ROW_COUNT
    assert len(demo_rows["dim_provider"]) == ROW_COUNT
    assert len(demo_rows["dim_diagnosis"]) == ROW_COUNT
    assert len(demo_rows["dim_service"]) == ROW_COUNT
    assert len(demo_rows["fact_claim_line"]) == ROW_COUNT
    # The calendar dimension is generated at its natural grain.
    assert len(demo_rows["dim_time"]) >= 1095


def test_build_rows_is_deterministic() -> None:
    first = build_rows()
    second = build_rows()
    for table in ("dim_member", "fact_claim_line", "dim_service"):
        assert first[table] == second[table]


def test_fact_fk_defects_are_seeded(demo_rows) -> None:
    fact = demo_rows["fact_claim_line"]
    member_sks = {r["member_sk"] for r in demo_rows["dim_member"]}
    provider_sks = {r["provider_sk"] for r in demo_rows["dim_provider"]}
    date_sks = {r["date_sk"] for r in demo_rows["dim_time"]}
    assert any(r["member_sk"] not in member_sks for r in fact)
    assert any(r["provider_sk"] not in provider_sks for r in fact)
    assert any(r["date_sk"] not in date_sks for r in fact)
    assert BAD_MEMBER_SK not in member_sks
    assert BAD_PROVIDER_SK not in provider_sks
    assert BAD_DATE_SK not in date_sks


def test_business_rule_defects_are_seeded(demo_rows) -> None:
    fact = demo_rows["fact_claim_line"]
    paid_null_allowed = [r for r in fact if r["claim_status"] == "PAID" and r["allowed_amount"] is None]
    assert paid_null_allowed, "expected a PAID row with a NULL allowed_amount"
    member_gender_null = [
        r for r in demo_rows["dim_member"]
        if r["member_sk"] == NULL_GENDER_MEMBER_SK and r["gender"] is None
    ]
    assert member_gender_null
    provider_network_null = [
        r for r in demo_rows["dim_provider"]
        if r["provider_sk"] == NULL_NETWORK_PROVIDER_SK and r["network_status"] is None
    ]
    assert provider_network_null


def test_sqlite_database_is_buildable(demo_sqlite) -> None:
    assert demo_sqlite.exists()
    conn = sqlite3.connect(str(demo_sqlite))
    try:
        names = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    assert {"dim_member", "dim_provider", "dim_diagnosis", "dim_service", "dim_time", "fact_claim_line"} <= names


def test_sqlite_row_counts_match_demo(demo_sqlite) -> None:
    conn = sqlite3.connect(str(demo_sqlite))
    try:
        for table in ("dim_member", "dim_provider", "dim_diagnosis", "dim_service", "fact_claim_line"):
            count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            assert count == ROW_COUNT, table
    finally:
        conn.close()


def test_sqlite_stores_true_nulls(demo_sqlite) -> None:
    conn = sqlite3.connect(str(demo_sqlite))
    try:
        null_gender = conn.execute(
            "SELECT COUNT(*) FROM dim_member WHERE gender IS NULL"
        ).fetchone()[0]
        assert null_gender == 1
        null_allowed = conn.execute(
            "SELECT COUNT(*) FROM fact_claim_line WHERE claim_status='PAID' "
            "AND allowed_amount IS NULL"
        ).fetchone()[0]
        assert null_allowed == 1
    finally:
        conn.close()


def test_csv_fixtures_match_built_rows(tmp_path) -> None:
    from hc_etl_qa_crew.demo_loader.dataset import _clean_csv_cell

    target = write_fixtures(tmp_path)
    rows_by_table = build_rows()
    for table_name, rows in rows_by_table.items():
        csv_path = target / f"{table_name}.csv"
        assert csv_path.exists()
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            csv_rows = list(reader)
        assert len(csv_rows) == len(rows), table_name
        headers = list(rows[0].keys())
        for row, original in zip(csv_rows, rows, strict=True):
            for column in headers:
                expected = "" if original[column] is None else _clean_csv_cell(original[column])
                assert row[column] == expected, (table_name, column)


def test_fixture_csvs_are_committed_and_current(tmp_path) -> None:
    """The checked-in fixtures must match what the generator produces today."""
    repo_root = Path(__file__).resolve().parents[1]
    committed_dir = repo_root / "fixtures" / "datasets"
    assert committed_dir.exists()
    # Generate a fresh copy into a temp dir and compare file-for-file.
    fresh_dir = write_fixtures(tmp_path)
    for csv_path in sorted(committed_dir.glob("*.csv")):
        fresh = fresh_dir / csv_path.name
        assert fresh.exists(), csv_path.name
        assert csv_path.read_bytes() == fresh.read_bytes(), csv_path.name


def test_demo_sqlite_path_points_under_outputs() -> None:
    assert "outputs" in str(DEMO_SQLITE_PATH)


def test_fact_amounts_are_positive_floats(demo_rows) -> None:
    for row in demo_rows["fact_claim_line"]:
        assert float(row["billed_amount"]) >= 0
        assert float(row["paid_amount"]) >= 0
        if row["allowed_amount"] is not None:
            assert float(row["allowed_amount"]) >= 0
