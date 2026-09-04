"""Deterministic provider selection and fallback for data snapshots.

Mirrors the Jira gateway pattern: provider choice is application logic, never
an agent decision. The mode decides the ordered list of providers; the gateway
walks it and records which provider actually served each snapshot.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from hc_etl_qa_crew.config import DataSourceMode, Settings
from hc_etl_qa_crew.exceptions import AllDataProvidersFailedError, DataError
from hc_etl_qa_crew.models import TableSnapshot
from hc_etl_qa_crew.schema_registry.star_schema import TableSpec

from .base import DataProvider
from .fixture_provider import FixtureDataProvider
from .live_provider import LiveDataProvider

logger = logging.getLogger(__name__)


@dataclass
class DataGateway:
    """Walks the allowed providers and returns the first healthy snapshot."""

    settings: Settings
    providers: list[DataProvider] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.providers:
            return
        if self.settings.data_source_mode is DataSourceMode.FIXTURE:
            self.providers = [FixtureDataProvider()]
        else:
            live = LiveDataProvider(self.settings.data_url)
            self.providers = [live]
        # In 'auto', try the live warehouse first, then the demo dataset. The
        # demo is NEVER a silent fallback for a failed live read.
        if (
            self.settings.data_source_mode is not DataSourceMode.FIXTURE
            and self.settings.demo_mode
        ):
            self.providers = [FixtureDataProvider(), live]

    def fetch_snapshot(self, table: TableSpec) -> TableSnapshot:
        provider_errors: dict[str, str] = {}
        for provider in self.providers:
            try:
                return provider.fetch_snapshot(table)
            except DataError as exc:
                provider_errors[provider.name] = self.settings.redact(str(exc))
                logger.warning("provider %s failed for %s: %s", provider.name, table.name, exc)
            except Exception as exc:  # noqa: BLE001
                provider_errors[provider.name] = self.settings.redact(str(exc))
                logger.exception("provider %s raised for %s", provider.name, table.name)
        message = (
            f"Could not read {table.name!r} from any configured provider. "
            "The demo dataset is never an automatic fallback for a failed live "
            "read."
        )
        raise AllDataProvidersFailedError(message, provider_errors)
