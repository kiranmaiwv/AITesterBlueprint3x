"""Tests for structured-output helpers: schema compaction, JSON extraction, truncation."""

from __future__ import annotations

import json

from hc_etl_qa_crew.models import SchemaAnalysis, SchemaEntity
from hc_etl_qa_crew.services.structured import (
    compact_schema,
    extract_json,
    is_empty_response,
    json_mode_instruction,
    looks_truncated,
    parse_model,
    schema_rejected,
)


def test_schema_rejected_detects_response_format_error() -> None:
    exc = Exception('HTTP 400 "This response_format type is unavailable now"')
    assert schema_rejected(exc) is True


def test_schema_rejected_is_narrow() -> None:
    assert schema_rejected(Exception("HTTP 401 auth failed")) is False
    assert schema_rejected(Exception("HTTP 429 rate limited")) is False
    assert schema_rejected(Exception("HTTP 400 bad key")) is False
    assert schema_rejected(Exception("rate limit exceeded")) is False


def test_is_empty_response() -> None:
    assert is_empty_response(Exception("Invalid response from LLM call - None or empty")) is True
    assert is_empty_response(Exception("empty response")) is True
    assert is_empty_response(Exception("HTTP 500")) is False


def test_compact_schema_strips_noise_but_keeps_field_names() -> None:
    schema = {
        "title": "X",
        "type": "object",
        "description": "long",
        "properties": {
            "title": {"type": "string", "description": "a real field called title"},
            "id": {"type": "string", "default": "x", "examples": ["y"]},
        },
    }
    compact = compact_schema(schema)
    assert "title" not in compact
    assert "description" not in compact
    assert "default" not in compact
    # A field literally named `title` must survive.
    assert compact["properties"]["title"]["type"] == "string"
    assert compact["properties"]["id"] == {"type": "string"}


def test_json_mode_instruction_is_compact() -> None:
    instruction = json_mode_instruction(SchemaAnalysis)
    assert "OUTPUT FORMAT" in instruction
    # The embedded schema is compact JSON on one line.
    schema_start = instruction.index("{", instruction.index("OUTPUT FORMAT"))
    schema_text = instruction[schema_start:].split("Use only the field names")[0].rstrip(" \n")
    json.loads(schema_text)  # must still be valid JSON
    assert "\n" not in schema_text


def test_extract_json_bare_object() -> None:
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced() -> None:
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_prose() -> None:
    payload = extract_json('Here you go: {"a": 1} hope that helps')
    assert payload == {"a": 1}


def test_extract_json_returns_none_for_garbage() -> None:
    assert extract_json("no json here") is None
    assert extract_json("") is None
    assert extract_json(None) is None


def test_looks_truncated() -> None:
    assert looks_truncated('{"a": 1, "b": [1,2,') is True
    assert looks_truncated('{"a": "unterminated') is True
    assert looks_truncated('{"a": 1}') is False
    assert looks_truncated("plain prose") is False
    assert looks_truncated("") is False


def test_parse_model_validates() -> None:
    payload = {
        "pipeline_name": "claims_etl_v1",
        "summary": "demo",
        "fact_table": "fact_claim_line",
        "dimension_tables": ["dim_member"],
        "entities": [
            {"id": "REQ-001", "entity_type": "requirement", "text": "x"}
        ],
    }
    parsed = parse_model(json.dumps(payload), SchemaAnalysis)
    assert parsed is not None
    assert parsed.pipeline_name == "claims_etl_v1"


def test_parse_model_rejects_bad_ids() -> None:
    payload = {
        "pipeline_name": "claims_etl_v1",
        "entities": [
            {"id": "BAD-001", "entity_type": "requirement", "text": "x"}
        ],
    }
    assert parse_model(json.dumps(payload), SchemaAnalysis) is None


def test_parse_model_rejects_prose() -> None:
    assert parse_model("I cannot comply, here is prose", SchemaAnalysis) is None


def test_parse_model_round_trip_schema_entity() -> None:
    entity = SchemaEntity(id="REQ-001", entity_type="requirement", text="x")
    raw = entity.model_dump_json()
    again = parse_model(raw, SchemaEntity)
    assert again is not None and again.id == "REQ-001"
