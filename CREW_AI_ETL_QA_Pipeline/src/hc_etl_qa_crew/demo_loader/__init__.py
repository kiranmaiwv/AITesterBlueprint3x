"""Demo dataset: deterministic healthcare star-schema fixtures (100 rows each)."""

from .dataset import (
    DEMO_SQLITE_PATH,
    ROW_COUNT,
    TABLE_NAMES,
    build_rows,
    build_sqlite,
    stamp,
    write_fixtures,
)

__all__ = [
    "DEMO_SQLITE_PATH",
    "ROW_COUNT",
    "TABLE_NAMES",
    "build_rows",
    "build_sqlite",
    "stamp",
    "write_fixtures",
]
