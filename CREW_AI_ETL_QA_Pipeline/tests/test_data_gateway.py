"""Tests for the deterministic demo (fixture) data provider and gateway fallback rules."""

from __future__ import annotations

import pytest

from hc_etl_qa_crew.config import DataSourceMode, Settings
from hc_etl_qa_crew.data_gateway.fixture_provider import FixtureDataProvider
from hc_etl_qa_crew.data_gateway.gateway import DataGateway
from hc_etl_qa_crew.exceptions import AllDataProvidersFailedError
from hc_etl_qa_crew.schema_registry.star_schema import (
    DIMENSION_TABLES,
    FACT_TABLE,
    REGISTRY,
)


class _FailingProvider(FixtureDataProvider):
    """A fixture provider that always raises, for fallback tests."""

    name = "AlwaysFailingFixtureProvider"

    def fetch_snapshot(self, table):  # noqa: ARG002
        from hc_etl_qa_crew.exceptions import DataError

        raise DataError("boom")


def test_fixture_provider_serves_every_registered_table() -> None:
    provider = FixtureDataProvider()
    for table in REGISTRY:
        snapshot = provider.fetch_snapshot(table)
        assert snapshot.table_name == table.name
        assert snapshot.source.value == "DEMO_FIXTURE"
        assert snapshot.row_count >= 100
        assert set(table.column_names) <= set(snapshot.column_names)
        assert len(snapshot.sample_rows) >= 1


def test_fixture_provider_has_expected_row_counts() -> None:
    provider = FixtureDataProvider()
    snapshot = provider.fetch_snapshot(FACT_TABLE)
    assert snapshot.row_count == 100
    member = provider.fetch_snapshot(next(t for t in DIMENSION_TABLES if t.name == "dim_member"))
    assert member.row_count == 100


def test_gateway_in_fixture_mode_serves_snapshots() -> None:
    settings = Settings.load()
    assert settings.data_source_mode is DataSourceMode.FIXTURE
    gateway = DataGateway(settings)
    snapshot = gateway.fetch_snapshot(FACT_TABLE)
    assert snapshot.source.value == "DEMO_FIXTURE"
    assert snapshot.row_count == 100


def test_fixture_provider_health_check_is_ok() -> None:
    provider = FixtureDataProvider()
    ok, detail = provider.health_check()
    assert ok is True
    assert detail


def test_gateway_raises_when_all_providers_fail() -> None:
    settings = Settings.load()
    gateway = DataGateway(settings)
    gateway.providers = [_FailingProvider()]
    with pytest.raises(AllDataProvidersFailedError) as exc_info:
        gateway.fetch_snapshot(FACT_TABLE)
    assert "demo dataset is never an automatic fallback" in str(exc_info.value)
    assert exc_info.value.provider_errors
