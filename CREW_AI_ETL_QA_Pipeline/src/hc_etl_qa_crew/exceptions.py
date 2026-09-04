"""Typed exceptions for the Healthcare ETL QA Crew pipeline.

Every failure surfaced to the UI is one of these. They carry a user-safe
message (``str(exc)``) that is guaranteed to have secrets redacted by the
callers in :mod:`hc_etl_qa_crew.config`.
"""

from __future__ import annotations


class HCETLQAError(Exception):
    """Base class for every error raised by this application."""


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
class ConfigurationError(HCETLQAError):
    """Configuration is missing or internally inconsistent."""


# --------------------------------------------------------------------------
# Data warehouse
# --------------------------------------------------------------------------
class DataError(HCETLQAError):
    """Base class for warehouse provider failures."""


class DataAuthError(DataError):
    """Credentials rejected or insufficient warehouse permissions."""


class DataNotFoundError(DataError):
    """A schema, table or column does not exist or is not visible."""


class DataTimeoutError(DataError):
    """The warehouse did not answer inside the configured timeout."""


class DataMalformedResponseError(DataError):
    """The warehouse answered, but the payload is not usable metadata."""


class AllDataProvidersFailedError(DataError):
    """Every provider allowed by the current mode failed.

    Carries the individual provider errors so the UI can explain both.
    """

    def __init__(self, message: str, provider_errors: dict[str, str] | None = None):
        super().__init__(message)
        self.provider_errors = provider_errors or {}


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------
class PipelineError(HCETLQAError):
    """A stage of the per-run pipeline failed."""


class StructuredOutputError(PipelineError):
    """An agent returned output that does not satisfy its Pydantic schema."""


class ValidationFailure(PipelineError):
    """Deterministic post-stage validation rejected an otherwise valid object."""


class RunInputError(HCETLQAError):
    """The submitted run input could not be parsed into valid pipeline names."""
