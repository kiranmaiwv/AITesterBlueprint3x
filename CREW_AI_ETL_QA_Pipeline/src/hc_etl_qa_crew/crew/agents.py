"""The four CrewAI agents.

Only the Schema & Transform Analyst may receive the data tool. The other three
work from the validated output of the stage before them, so they have no way
to reach the warehouse even if a prompt injection asks them to.

Provider extras (``LLM_EXTRA_BODY_JSON``) reach the request through CrewAI's
``additional_params``: CrewAI merges that dict into the params of every
``chat.completions.create(**params)`` call. The OpenAI SDK accepts
``extra_body`` as a first-class kwarg and merges it into the JSON body, which
is how DeepSeek's ``{"thinking": {"type": "disabled"}}`` gets onto the wire.
Without that, reasoning models spend the whole token budget on chain-of-thought
and return empty content.
"""

from __future__ import annotations

from typing import Any

from crewai import LLM, Agent

from hc_etl_qa_crew.config import Settings
from hc_etl_qa_crew.tools.data_tool import InspectDataTool

from .prompts import agent_prompt


def build_llm(settings: Settings, max_tokens: int | None = None) -> LLM:
    """One LLM instance per agent so token budgets can differ per stage."""
    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "temperature": settings.llm_temperature,
        "max_tokens": max_tokens or settings.llm_max_tokens,
    }
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    if settings.llm_extra_body:
        # CrewAI forwards additional_params into create(**params); the OpenAI
        # SDK accepts extra_body and merges it into the JSON request body.
        kwargs["additional_params"] = {"extra_body": settings.llm_extra_body}
    return LLM(**kwargs)


def _agent(key: str, settings: Settings, **overrides: Any) -> Agent:
    prompt = agent_prompt(key)
    params: dict[str, Any] = {
        "role": prompt["role"],
        "goal": prompt["goal"],
        "backstory": prompt["backstory"],
        "llm": build_llm(settings),
        "verbose": False,
        "allow_delegation": False,  # sequential pipeline; nobody delegates
        "max_iter": 8,
        "max_retry_limit": 1,  # one controlled repair attempt, never a loop
    }
    params.update(overrides)
    return Agent(**params)


def build_schema_analyst(
    settings: Settings, data_tool: InspectDataTool | None
) -> Agent:
    return _agent(
        "schema_analyst",
        settings,
        tools=[data_tool] if data_tool else [],
    )


def build_recon_strategist(settings: Settings) -> Agent:
    return _agent("recon_strategist", settings)


def build_test_case_writer(settings: Settings) -> Agent:
    return _agent("test_case_writer", settings)


def build_pytest_coder(settings: Settings) -> Agent:
    return _agent("pytest_coder", settings)
