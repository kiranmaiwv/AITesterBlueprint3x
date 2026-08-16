"""
conftest.py — Shared pytest fixtures for the ETL QA Buddy test suite.

Provides a `db` fixture returning a live sqlite3 connection to the ETL database.
The database path is resolved from the DATABASE_PATH environment variable, and
falls back to the default location inside backend/database/.

If the database file does not exist yet, it is created automatically by invoking
the setup_db script — so the suite is runnable out of the box.
"""

import os
import sqlite3
import sys

import pytest

# tests/ -> repo root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(PROJECT_ROOT, "backend", "database", "etl_qa.db")


def _resolve_db_path() -> str:
    env_path = os.environ.get("DATABASE_PATH")
    if env_path:
        if os.path.isabs(env_path):
            return env_path
        # Resolve relative paths against the repo root for consistency.
        return os.path.normpath(os.path.join(PROJECT_ROOT, env_path))
    return DEFAULT_DB


def _ensure_db(db_path: str) -> None:
    if os.path.exists(db_path):
        return
    # Create the DB using the setup script.
    setup_dir = os.path.join(PROJECT_ROOT, "backend", "database")
    sys.path.insert(0, setup_dir)
    try:
        import setup_db  # type: ignore
        setup_db.create_database(db_path)
    finally:
        sys.path.pop(0)


@pytest.fixture(scope="session")
def db_path() -> str:
    path = _resolve_db_path()
    _ensure_db(path)
    return path


@pytest.fixture
def db(db_path):
    """Yield a sqlite3 connection to the ETL database."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()
