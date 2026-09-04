"""Tests for configuration loading, readiness and secret redaction."""

from __future__ import annotations

import os

import pytest

from hc_etl_qa_crew.config import DataSourceMode, Settings, StructuredOutputMode
from hc_etl_qa_crew.exceptions import ConfigurationError


@pytest.fixture()
def clean_env():
    old = dict(os.environ)
    os.environ["HC_ETL_QA_CREW_SKIP_DOTENV"] = "1"
    for key in (
        "DEMO_MODE",
        "DATA_SOURCE_MODE",
        "LLM_MODEL",
        "LLM_API_KEY",
        "DEEPSEEK_API_KEY",
        "LLM_BASE_URL",
        "LLM_STRUCTURED_OUTPUT",
        "DATA_ENGINE",
        "DATA_URL",
        "OUTPUT_DIR",
        "APP_NAME",
    ):
        os.environ.pop(key, None)
    yield
    os.environ.clear()
    os.environ.update(old)


def test_defaults(clean_env) -> None:
    settings = Settings.load()
    assert settings.app_name == "Healthcare ETL QA Crew"
    assert settings.demo_mode is False
    assert settings.data_source_mode is DataSourceMode.FIXTURE
    assert settings.llm_model == "deepseek/deepseek-v4-flash"
    assert settings.llm_ready() is False
    assert settings.live_data_ready() is False


def test_demo_mode_clears_blocking_problems(clean_env) -> None:
    os.environ["DEMO_MODE"] = "true"
    settings = Settings.load()
    assert settings.blocking_problems() == []


def test_live_mode_requires_data_url(clean_env) -> None:
    os.environ["DATA_SOURCE_MODE"] = "live"
    settings = Settings.load()
    problems = settings.blocking_problems()
    assert any("DATA_URL" in p for p in problems)


def test_structured_output_enum(clean_env) -> None:
    os.environ["LLM_STRUCTURED_OUTPUT"] = "prompt"
    settings = Settings.load()
    assert settings.llm_structured_output is StructuredOutputMode.PROMPT
    os.environ["LLM_STRUCTURED_OUTPUT"] = "bogus"
    with pytest.raises(ConfigurationError, match="must be one of"):
        Settings.load()


def test_invalid_temperature_raises(clean_env) -> None:
    os.environ["LLM_TEMPERATURE"] = "9"
    with pytest.raises(ConfigurationError, match="between 0.0 and 2.0"):
        Settings.load()


def test_redact_hides_secrets(clean_env) -> None:
    os.environ["LLM_API_KEY"] = "sk-super-secret-value-123456"
    settings = Settings.load()
    text = "key=sk-super-secret-value-123456 and a basic dXNlcjpwYXNz basic value"
    cleaned = settings.redact(text)
    assert "sk-super-secret-value-123456" not in cleaned
    assert "REDACTED" in cleaned
    # Short strings are not worth redacting.
    assert settings.redact("fine") == "fine"


def test_status_never_leaks_secret_values(clean_env) -> None:
    os.environ["LLM_API_KEY"] = "sk-super-secret-value-123456"
    settings = Settings.load()
    status = settings.status()
    serialized = str(status)
    assert "sk-super-secret-value-123456" not in serialized
    assert "…3456" in serialized  # masked tail only
    assert status["llm"]["ready"] is True
