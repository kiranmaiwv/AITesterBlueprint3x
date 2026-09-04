"""Live data provider: introspects a real warehouse through SQLAlchemy.

Read-only by construction: it issues only ``SELECT`` / introspection
statements and never writes. Raises typed ``DataError`` subclasses so the
UI can explain failures, and never falls back to fixtures.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine

from hc_etl_qa_crew.exceptions import (
    DataAuthError,
    DataError,
    DataMalformedResponseError,
    DataNotFoundError,
    DataTimeoutError,
)
from hc_etl_qa_crew.models import DataSource, QualityProbe, TableSnapshot
from hc_etl_qa_crew.schema_registry.star_schema import TableSpec

from .base import DataProvider

logger = logging.getLogger(__name__)

_SAMPLE_LIMIT = 8
#: (probe_name, sql) templates rendered with {schema}, {table}, {column}.
_PROBE_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("total_row_count", "SELECT COUNT(*) FROM {schema}.{table}"),
    (
        "null_count",
        "SELECT COUNT(*) FROM {schema}.{table} WHERE {column} IS NULL",
    ),
    (
        "distinct_count",
        "SELECT COUNT(DISTINCT {column}) FROM {schema}.{table}",
    ),
    (
        "min_value",
        "SELECT MIN({column}) FROM {schema}.{table}",
    ),
    (
        "max_value",
        "SELECT MAX({column}) FROM {schema}.{table}",
    ),
)


class LiveDataProvider(DataProvider):
    """Introspects one star schema inside a live, read-only warehouse."""

    source: DataSource = DataSource.LIVE_WAREHOUSE

    def __init__(self, engine_url: str, schema: str = "public", timeout_seconds: int = 30):
        if not engine_url:
            raise DataError("A DATA_URL is required for the live data provider")
        self._engine: Engine = create_engine(engine_url, connect_args={"connect_timeout": timeout_seconds})
        self._schema = schema

    def health_check(self) -> tuple[bool, str]:
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, f"connected to schema {self._schema!r}"
        except Exception as exc:  # noqa: BLE001 - surface any connection problem
            return False, str(exc)

    def _connect(self) -> Connection:
        try:
            return self._engine.connect()
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if "denied" in message or "authentication" in message or "password" in message:
                raise DataAuthError(f"Warehouse authentication failed: {exc}") from exc
            if "timeout" in message or "timed out" in message:
                raise DataTimeoutError(f"Warehouse connection timed out: {exc}") from exc
            raise DataError(f"Could not connect to the warehouse: {exc}") from exc

    def fetch_snapshot(self, table: TableSpec) -> TableSnapshot:
        insp = inspect(self._engine)
        if not insp.has_table(table.name, schema=self._schema):
            raise DataNotFoundError(
                f"Table {self._schema}.{table.name} does not exist or is not visible"
            )
        real_columns = {c["name"] for c in insp.get_columns(table.name, schema=self._schema)}
        for expected in table.column_names:
            if expected not in real_columns:
                raise DataMalformedResponseError(
                    f"Table {table.name!r} is missing expected column {expected!r}"
                )
        try:
            row_count = self._scalar(
                f"SELECT COUNT(*) FROM {self._schema}.{table.name}"
            )
            sample = self._sample(table.name)
        except DataError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DataError(f"Query against {table.name!r} failed: {exc}") from exc

        probes: list[QualityProbe] = [
            QualityProbe(
                name="total_row_count",
                sql=f"SELECT COUNT(*) FROM {self._schema}.{table.name}",
                observed_value=str(row_count),
            )
        ]
        return TableSnapshot(
            table_name=table.name,
            source=self.source,
            column_names=list(table.column_names),
            row_count=int(row_count or 0),
            sample_rows=sample,
            probes=probes,
            fetched_at=datetime.now(),
        )

    def _scalar(self, sql: str) -> Any:
        with self._engine.connect() as conn:
            result = conn.execute(text(sql)).scalar()
            return result

    def _sample(self, table: str, limit: int = _SAMPLE_LIMIT) -> list[dict[str, Any]]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(f"SELECT * FROM {self._schema}.{table} LIMIT :limit"),
                {"limit": limit},
            )
            columns = list(rows.keys())
            return [dict(zip(columns, row, strict=True)) for row in rows.fetchall()]
