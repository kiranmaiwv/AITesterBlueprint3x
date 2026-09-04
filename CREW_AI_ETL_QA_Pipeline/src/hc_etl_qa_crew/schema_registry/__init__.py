"""Schema registry: canonical star-schema contracts and table lookup."""

from .star_schema import (
    DIMENSION_NAMES,
    DIMENSION_TABLES,
    FACT_NAME,
    FACT_TABLE,
    NAME_ALIASES,
    PIPELINE_NAME,
    REGISTRY,
    ColumnSpec,
    TableKind,
    TableSpec,
    lookup_table,
)

__all__ = [
    "DIMENSION_NAMES",
    "DIMENSION_TABLES",
    "FACT_NAME",
    "FACT_TABLE",
    "NAME_ALIASES",
    "PIPELINE_NAME",
    "REGISTRY",
    "ColumnSpec",
    "TableKind",
    "TableSpec",
    "lookup_table",
]
