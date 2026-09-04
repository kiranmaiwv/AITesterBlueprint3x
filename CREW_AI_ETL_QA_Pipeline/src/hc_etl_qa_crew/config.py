"""Application configuration.

Everything is read from the environment (or ``st.secrets``, which the UI
copies into the environment before this module is used). Nothing here is
collected from ordinary UI text fields, and nothing secret is ever returned
by :meth:`Settings.status`.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .exceptions import ConfigurationError

# Minimum length before a value is worth redacting; shorter values are noise.
_MIN_SECRET_LENGTH = 8


def _bootstrap_trust_store() -> None:
    """Point SSL at a CA bundle when the interpreter has no system default.

    Some Python builds (notably python.org framework installs on macOS) ship
    without a usable default CA path, which makes every HTTPS call to an LLM
    provider fail with ``CERTIFICATE_VERIFY_FAILED`` (or hang retrying the
    handshake). When certifi is installed, export its bundle through the
    standard ``SSL_CERT_FILE`` variable before any HTTP client initialises.
    """
    if os.getenv("SSL_CERT_FILE") or os.getenv("REQUESTS_CA_BUNDLE"):
        return
    try:
        import certifi

        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    except Exception:  # noqa: BLE001 - certifi is optional; keep the default path
        return


_bootstrap_trust_store()


class DataSourceMode(StrEnum):
    """Where the pipeline reads its star-schema snapshot from."""

    FIXTURE = "fixture"
    LIVE = "live"


class StructuredOutputMode(StrEnum):
    """How the LLM is asked to return structured data.

    ``auto``   detect from the provider's own error, then remember
    ``schema``  always ask the provider to enforce the JSON schema
    ``prompt``  never ask; put the schema in the prompt and validate here
    """

    AUTO = "auto"
    SCHEMA = "schema"
    PROMPT = "prompt"


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    raw = _env(key)
    if not raw:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer, got {raw!r}") from exc


def _env_float(key: str, default: float) -> float:
    raw = _env(key)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be a number, got {raw!r}") from exc


def _env_json(key: str, default: Any) -> Any:
    raw = _env(key)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"{key} must be valid JSON, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the environment.

    Build it with :meth:`load`; never mutate it. The pipeline receives one
    instance so a run cannot be reconfigured halfway through.
    """

    # app
    app_name: str = "Healthcare ETL QA Crew"
    app_env: str = "development"
    output_dir: Path = Path("outputs")
    log_level: str = "INFO"
    demo_mode: bool = False
    data_source_mode: DataSourceMode = DataSourceMode.FIXTURE

    # llm
    llm_model: str = "deepseek/deepseek-v4-flash"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 8000
    llm_structured_output: StructuredOutputMode = StructuredOutputMode.AUTO
    #: Provider-only body keys forwarded on every request as ``extra_body``.
    #: DeepSeek reasoning models need ``{"thinking": {"type": "disabled"}}``.
    llm_extra_body: dict[str, Any] = field(default_factory=dict)

    # live warehouse
    data_engine: str = ""
    data_url: str = ""

    # pipeline
    pipeline_max_runs: int = 20
    pipeline_max_retries: int = 2
    pipeline_run_timeout_seconds: int = 600
    pipeline_max_input_chars: int = 4000

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, env_file: str | os.PathLike[str] | None = None) -> Settings:
        """Read the environment into a Settings instance.

        Raises :class:`ConfigurationError` only for values that are present
        but unusable. Missing credentials are NOT fatal here: the UI shows a
        readiness panel instead, so the app can start and be inspected
        without secrets.
        """
        # Set HC_ETL_QA_CREW_SKIP_DOTENV=1 to read the environment only. Tests
        # rely on this so a developer's local .env cannot change their result,
        # and containers can use it to keep configuration explicit.
        if os.getenv("HC_ETL_QA_CREW_SKIP_DOTENV") == "1":
            pass
        elif env_file:
            load_dotenv(env_file, override=False)
        else:
            load_dotenv(override=False)

        def _enum(enum_cls, key: str, default):
            raw = _env(key)
            if not raw:
                return default
            try:
                return enum_cls(raw.lower())
            except ValueError as exc:
                allowed = ", ".join(m.value for m in enum_cls)
                raise ConfigurationError(
                    f"{key} must be one of: {allowed}. Got {raw!r}"
                ) from exc

        temperature = _env_float("LLM_TEMPERATURE", 0.1)
        if not 0.0 <= temperature <= 2.0:
            raise ConfigurationError("LLM_TEMPERATURE must be between 0.0 and 2.0")

        max_runs = _env_int("PIPELINE_MAX_RUNS", 20)
        if max_runs < 1:
            raise ConfigurationError("PIPELINE_MAX_RUNS must be >= 1")

        data_url = _env("DATA_URL")
        data_engine = _env("DATA_ENGINE", "postgresql")
        if data_url and not data_engine:
            raise ConfigurationError("DATA_ENGINE must be set when DATA_URL is provided")

        extra_body = _env_json("LLM_EXTRA_BODY_JSON", {})
        if not isinstance(extra_body, dict):
            raise ConfigurationError("LLM_EXTRA_BODY_JSON must be a JSON object")

        return cls(
            app_name=_env("APP_NAME", "Healthcare ETL QA Crew"),
            app_env=_env("APP_ENV", "development"),
            output_dir=Path(_env("OUTPUT_DIR", "outputs")),
            log_level=_env("LOG_LEVEL", "INFO").upper(),
            demo_mode=_env_bool("DEMO_MODE", False),
            data_source_mode=_enum(
                DataSourceMode, "DATA_SOURCE_MODE", DataSourceMode.FIXTURE
            ),
            llm_model=_env("LLM_MODEL", "deepseek/deepseek-v4-flash"),
            llm_api_key=_env("LLM_API_KEY") or _env("DEEPSEEK_API_KEY"),
            llm_base_url=_env("LLM_BASE_URL") or _env("DEEPSEEK_BASE_URL"),
            llm_temperature=temperature,
            llm_max_tokens=_env_int("LLM_MAX_TOKENS", 8000),
            llm_structured_output=_enum(
                StructuredOutputMode, "LLM_STRUCTURED_OUTPUT", StructuredOutputMode.AUTO
            ),
            llm_extra_body=extra_body,
            data_engine=data_engine,
            data_url=data_url,
            pipeline_max_runs=max_runs,
            pipeline_max_retries=_env_int("PIPELINE_MAX_RETRIES", 2),
            pipeline_run_timeout_seconds=_env_int("PIPELINE_RUN_TIMEOUT_SECONDS", 600),
            pipeline_max_input_chars=_env_int("PIPELINE_MAX_INPUT_CHARS", 4000),
        )

    # ------------------------------------------------------------------
    @property
    def secrets(self) -> tuple[str, ...]:
        """Every value that must never appear in a log, error, or artifact."""
        candidates = (self.llm_api_key, self.data_url)
        return tuple(c for c in candidates if c and len(c) >= _MIN_SECRET_LENGTH)

    def redact(self, text: str) -> str:
        """Replace every known secret in ``text`` with a marker.

        Applied to all log lines and all error messages that reach the UI.
        """
        if not text:
            return text
        cleaned = text
        for secret in self.secrets:
            cleaned = cleaned.replace(secret, "***REDACTED***")
        # Basic-auth headers embed base64 credentials; drop the payload.
        cleaned = re.sub(
            r"(Basic|Bearer)\s+[A-Za-z0-9+/=_\-.]{8,}", r"\1 ***REDACTED***", cleaned
        )
        return cleaned

    # ------------------------------------------------------------------
    def llm_ready(self) -> bool:
        return bool(self.llm_model and self.llm_api_key)

    def live_data_ready(self) -> bool:
        return bool(self.data_url)

    def status(self) -> dict[str, dict[str, Any]]:
        """Redacted readiness report for the UI. Contains no secret values."""

        def mask(value: str) -> str:
            if not value:
                return "not set"
            if len(value) <= 4:
                return "set"
            return f"set (…{value[-4:]})"

        data_engine = self.data_engine or "not set"
        return {
            "llm": {
                "ready": self.llm_ready(),
                "model": self.llm_model or "not set",
                "api_key": mask(self.llm_api_key),
                "temperature": self.llm_temperature,
                "structured_output": self.llm_structured_output.value,
            },
            "data_source": {
                "ready": True,
                "mode": self.data_source_mode.value,
                "engine": data_engine,
                "url": mask(self.data_url) if self.data_url else "not set",
            },
            "pipeline": {
                "ready": True,
                "demo_mode": self.demo_mode,
                "output_dir": str(self.output_dir),
            },
        }

    def blocking_problems(self) -> list[str]:
        """Reasons a real run cannot start yet, in plain language."""
        problems: list[str] = []
        if self.demo_mode:
            return problems
        if self.data_source_mode is DataSourceMode.LIVE and not self.live_data_ready():
            problems.append(
                "Data source mode is 'live' but no DATA_URL is configured."
            )
        if not self.llm_ready():
            problems.append(
                "LLM is not configured. Set LLM_MODEL and LLM_API_KEY "
                "(or DEEPSEEK_API_KEY)."
            )
        return problems
