"""
Kisan Dost — LLM Provider Configuration (OpenRouter)
=====================================================
Configures the OpenAI Agents SDK using OpenRouter as the unified, robust
LLM provider for all agents, tools, and guardrails.
"""

from __future__ import annotations

import os
from typing import Any
from openai import AsyncOpenAI
from agents import (
    OpenAIChatCompletionsModel,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)


def setup_llm_provider() -> tuple[str, str]:
    """
    Configures OpenRouter as the primary LLM provider for the OpenAI Agents SDK.

    Returns:
        tuple[provider_name, model_name]
    """
    # Always disable tracing when using OpenRouter to avoid connection timeouts
    set_tracing_disabled(True)

    api_key = (
        os.getenv("OPENROUTER_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini").strip()
    provider = "openrouter"

    if api_key:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/m-rehan-k/kisan-dost-multi-agent-ai",
                "X-Title": "Kisan Dost Agronomy Assistant",
            },
        )
        set_default_openai_client(client)
        set_default_openai_api("chat_completions")

        model_instance = OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=client,
        )
        _assign_model_to_agents(model_instance)
    else:
        set_tracing_disabled(True)

    return provider, model_name


def _assign_model_to_agents(model_instance: Any) -> None:
    """Assigns the configured model instance across all active agents."""
    try:
        from agents_setup.triage_agent import triage_agent
        from agents_setup.agronomy_agent import agronomy_agent
        from agents_setup.pest_doctor_agent import pest_doctor_agent
        from agents_setup.market_agent import market_agent
        from agents_setup.finance_agent import finance_agent
        from guardrails.input_guardrail import topic_checker_agent

        for agent in [
            triage_agent,
            agronomy_agent,
            pest_doctor_agent,
            market_agent,
            finance_agent,
            topic_checker_agent,
        ]:
            agent.model = model_instance
    except Exception:
        pass
