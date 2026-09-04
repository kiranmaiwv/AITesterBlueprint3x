"""Regenerate the demo fixtures and the demo SQLite database.

The CSVs under ``fixtures/datasets`` are derived from the canonical schema
registry, and the SQLite database under ``outputs/`` is derived from the same
rows. Run this after changing anything in ``star_schema.py`` or
``demo_loader/dataset.py``.
"""

from __future__ import annotations

from pathlib import Path

from hc_etl_qa_crew.demo_loader.dataset import build_sqlite, write_fixtures

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    csv_dir = write_fixtures(repo_root)
    db_path = build_sqlite(repo_root / "outputs" / "hc_etl_demo.db")
    print(f"CSV fixtures -> {csv_dir}")
    print(f"SQLite demo db -> {db_path}")
