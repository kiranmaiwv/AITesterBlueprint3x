"""Shared pytest fixtures for the Healthcare ETL QA Crew tests."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("HC_ETL_QA_CREW_SKIP_DOTENV", "1")


@pytest.fixture()
def demo_rows():
    """The deterministic in-memory demo rows, shared across tests."""
    from hc_etl_qa_crew.demo_loader.dataset import build_rows

    return build_rows()


@pytest.fixture()
def demo_sqlite(tmp_path):
    """A freshly built demo SQLite database in a temp directory."""
    from hc_etl_qa_crew.demo_loader.dataset import build_sqlite

    return build_sqlite(tmp_path / "hc_etl_demo.db")
