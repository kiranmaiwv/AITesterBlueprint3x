"""Provider interface shared by the fixture and live gateway implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from hc_etl_qa_crew.models import DataSource, TableSnapshot
from hc_etl_qa_crew.schema_registry.star_schema import TableSpec


class DataProvider(ABC):
    """Produces a validated snapshot of one star-schema table.

    Implementations must raise a subclass of
    :class:`hc_etl_qa_crew.exceptions.DataError` on failure. They must never
    return partial or fabricated data, and never fall back to fixtures.
    """

    #: Recorded on every snapshot this provider returns.
    source: DataSource

    @property
    def name(self) -> str:
        return type(self).__name__

    @abstractmethod
    def health_check(self) -> tuple[bool, str]:
        """Cheap reachability probe. Returns ``(ok, human readable detail)``."""

    @abstractmethod
    def fetch_snapshot(self, table: TableSpec) -> TableSnapshot:
        """Return column names, row count, sample rows, and quality probes.

        Raises a ``DataError`` on failure. Never fabricates rows.
        """
