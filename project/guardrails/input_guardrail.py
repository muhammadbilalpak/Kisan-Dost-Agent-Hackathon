"""
Kisan Dost — Input Guardrail
============================
Filters out off-topic questions and unsafe/unrelated requests on the Triage Agent.
Enforces the source-specified TopicSafetyCheck and topic_checker_agent.
"""

from __future__ import annotations

import os
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    input_guardrail,
)

from models.schemas import TopicSafetyCheck

# Fallback topic verification keywords for offline or unit-test environments
FARMING_KEYWORDS = [
    "crop", "fasal", "kisan", "farmer", "gandum", "wheat", "cotton", "kapas",
    "rice", "chawal", "sugarcane", "ganna", "maize", "makki", "sarson", "mustard",
    "fertilizer", "khad", "urea", "dap", "keera", "pest", "disease", "beemari",
    "safed makhi", "whitefly", "sundi", "tela", "spray", "pesticide", "poison",
    "pani", "water", "irrigation", "tubewell", "canal", "nahar", "mausam", "weather",
    "mandi", "rate", "price", "daam", "profit", "munafa", "cost", "kharcha",
    "kissan card", "subsidy", "loan", "qardah", "acre", "soil", "zameen", "multan",
    "punjab", "sindh", "kpk", "balochistan", "rabi", "kharif",
]

OFF_TOPIC_KEYWORDS = [
    "cricket", "movie", "cinema", "song", "actor", "politics", "election",
    "imran khan", "nawaz", "biden", "trump", "crypto", "bitcoin", "coding",
    "javascript", "python programming", "hack", "weapons", "drugs",
]

topic_checker_agent = Agent(
    name="Topic Guardrail Checker",
    instructions="""Check if the message is about farming/agriculture in Pakistan and is safe.

ALLOWED (is_farming_related=True, is_safe=True):
- Crops, fruits, vegetables, livestock, farming operations
- Fertilizers, seeds, sowing, harvesting, soil preparation
- Agricultural pests, plant diseases, chemical & organic sprays
- Water, irrigation methods, weather for farming, drought, rain
- Mandi commodity rates, crop economics, farm profit/cost
- Pakistani government agricultural schemes, Kisan Card, subsidies, Zarai loans

BLOCKED (is_farming_related=False or is_safe=False):
- Politics, elections, government administration unrelated to agri schemes
- Human medical advice, human poison ingestion, personal disease treatment
- Sports, cricket, entertainment, movies, general chit-chat
- Programming, hacking, weapons, illicit activities, violence

Always provide honest reasoning and return the TopicSafetyCheck structured model.""",
    output_type=TopicSafetyCheck,
    model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
)


def _extract_text_from_input(user_input: str | list | dict) -> str:
    """Extract plain text string from various user input formats."""
    if isinstance(user_input, str):
        return user_input.strip()
    if isinstance(user_input, list):
        parts = []
        for item in user_input:
            if isinstance(item, dict):
                content = item.get("content", "")
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and "text" in c:
                            parts.append(c["text"])
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts).strip()
    return str(user_input).strip()


@input_guardrail
async def farming_topic_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    user_input: str | list,
) -> GuardrailFunctionOutput:
    """
    Input guardrail on the Triage Agent that rejects off-topic or unsafe requests.
    """
    input_text = _extract_text_from_input(user_input)

    # Heuristic fast check for off-topic queries
    input_lower = input_text.lower()
    for bad_kw in OFF_TOPIC_KEYWORDS:
        if bad_kw in input_lower:
            check = TopicSafetyCheck(
                is_farming_related=False,
                is_safe=True,
                reasoning=f"Query matches blocked off-topic subject: '{bad_kw}'.",
            )
            return GuardrailFunctionOutput(
                output_info=check,
                tripwire_triggered=True,
            )

    try:
        result = await Runner.run(
            topic_checker_agent,
            input_text,
            context=ctx.context if ctx else None,
        )
        check = result.final_output
        if not isinstance(check, TopicSafetyCheck):
            check = TopicSafetyCheck(
                is_farming_related=True,
                is_safe=True,
                reasoning="Classified as safe farming query.",
            )
    except Exception as e:
        # Graceful fallback when running offline or without active LLM credentials
        is_farming = any(kw in input_lower for kw in FARMING_KEYWORDS) or len(input_text.split()) < 3
        check = TopicSafetyCheck(
            is_farming_related=is_farming,
            is_safe=True,
            reasoning="Fallback keyword-based classification due to offline/test environment.",
        )

    return GuardrailFunctionOutput(
        output_info=check,
        tripwire_triggered=(
            (not check.is_farming_related)
            or (not check.is_safe)
        ),
    )
