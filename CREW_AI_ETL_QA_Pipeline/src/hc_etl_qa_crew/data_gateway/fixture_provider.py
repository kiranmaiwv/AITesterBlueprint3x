"""Fixture (demo) data provider: reads the deterministic demo rows.

This provider is what makes ``DATA_SOURCE_MODE=fixture`` work without any
warehouse credentials. It reads the same rows the fixture CSVs are written
from, so what an agent "sees" is exactly what the demo runs on. The source is
always labelled ``DEMO_FIXTURE`` so no artifact can be mistaken for a live
warehouse read.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from hc_etl_qa_crew.exceptions import DataMalformedResponseError
from hc_etl_qa_crew.models import DataSource, QualityProbe, TableSnapshot
from hc_etl_qa_crew.schema_registry.star_schema import TableSpec

from .base import DataProvider

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = PROJECT_ROOT / "fixtures" / "datasets"


def _coerce(value: str) -> Any:
    """Best-effort CSV cell coercion for display; never used as source of truth."""
    value = value.strip()
    if value == "":
        return None
    try:
        if value.isdigit():
            return int(value)
        if value.startswith(("19", "20")) and "-" in value and len(value) == 10:
            return date.fromisoformat(value)
        if " " in value and value.split(" ")[0].startswith(("19", "20")):
            return datetime.fromisoformat(value.replace(" ", "T"))
        return float(value)
    except ValueError:
        return value


class FixtureDataProvider(DataProvider):
    """Reads deterministic rows straight from :mod:`demo_loader.dataset`."""

    source: DataSource = DataSource.DEMO_FIXTURE

    def __init__(self) -> None:
        # Imported lazily to keep the demo importable without a dataset build.
        from hc_etl_qa_crew.demo_loader.dataset import build_rows

        self._rows_by_table = build_rows()

    def health_check(self) -> tuple[bool, str]:
        return True, "demo fixture dataset is available"

    def fetch_snapshot(self, table: TableSpec) -> TableSnapshot:
        rows = self._rows_by_table.get(table.name)
        if not rows:
            raise DataMalformedResponseError(
                f"No demo rows registered for table {table.name!r}"
            )
        columns = [spec.name for spec in table.columns]
        for row in rows:
            missing = set(columns) - set(row)
            if missing:
                raise DataMalformedResponseError(
                    f"Demo rows for {table.name!r} are missing columns: "
                    f"{', '.join(sorted(missing))}"
                )
        return TableSnapshot(
            table_name=table.name,
            source=self.source,
            column_names=columns,
            row_count=len(rows),
            sample_rows=[{c: row[c] for c in columns} for row in rows[:8]],
            probes=[
                QualityProbe(
                    name="total_row_count",
                    sql=f'SELECT COUNT(*) AS row_count FROM "{table.name}"',
                    observed_value=str(len(rows)),
                ),
                QualityProbe(
                    name="null_column_count",
                    sql=f'SELECT COUNT(*) AS nulls FROM "{table.name}"',
                    observed_value="0",
                ),
            ],
            fetched_at=datetime.now(),
        )
