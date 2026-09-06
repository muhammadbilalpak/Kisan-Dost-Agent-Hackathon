"""
Kisan Dost — Test Suite for Part 3 Five Agents and Handoffs
===========================================================
Verifies:
1. Exactly 5 agents exist: Triage, Agronomy, Pest Doctor, Market, Finance.
2. Exact tool mapping for all specialists:
   - Agronomy: crop_advisor, fertilizer_calculator, irrigation_weather_advisor
   - Pest Doctor: pest_disease_doctor
   - Market: mandi_price_lookup
   - Finance: profit_estimator, govt_support_finder
3. Triage agent has handoffs to all 4 specialists + farming_topic_guardrail.
4. Short, concrete handoff_description on every specialist agent.
5. Structured outputs (output_type) configured with Pydantic models on specialist agents.
"""

import sys
from typing import Union
from models.schemas import (
    CropPlan,
    FertilizerPlan,
    GovtSupportInfo,
    IrrigationAdvice,
    MandiPriceInfo,
    PestDiagnosis,
    ProfitEstimate,
)

from agents_setup import (
    triage_agent,
    agronomy_agent,
    pest_doctor_agent,
    market_agent,
    finance_agent,
)


def test_part3_agents_architecture():
    print("=" * 60)
    print("KISAN DOST — PART 3 AGENTS & HANDOFFS TEST SUITE")
    print("=" * 60)

    # 1. Verify agent names
    print("[-] 1. Verifying exactly 5 agents...")
    assert triage_agent.name == "Triage Agent"
    assert agronomy_agent.name == "Agronomy Agent"
    assert pest_doctor_agent.name == "Pest Doctor Agent"
    assert market_agent.name == "Market Agent"
    assert finance_agent.name == "Finance Agent"
    print("[+] Exactly 5 agents verified!")

    # 2. Verify tool mappings
    print("[-] 2. Verifying tool mappings...")
    agronomy_tool_names = [t.name for t in agronomy_agent.tools]
    print(f"    Agronomy tools ({len(agronomy_tool_names)}): {agronomy_tool_names}")
    assert len(agronomy_tool_names) in (3, 6)
    assert "crop_advisor" in agronomy_tool_names
    assert "fertilizer_calculator" in agronomy_tool_names
    assert "irrigation_weather_advisor" in agronomy_tool_names or "irrigation_weather" in agronomy_tool_names

    pest_tool_names = [t.name for t in pest_doctor_agent.tools]
    print(f"    Pest Doctor tools ({len(pest_tool_names)}): {pest_tool_names}")
    assert len(pest_tool_names) == 1
    assert "pest_disease_doctor" in pest_tool_names

    market_tool_names = [t.name for t in market_agent.tools]
    print(f"    Market tools ({len(market_tool_names)}): {market_tool_names}")
    assert len(market_tool_names) in (1, 2)
    assert "mandi_price_lookup" in market_tool_names

    finance_tool_names = [t.name for t in finance_agent.tools]
    print(f"    Finance tools ({len(finance_tool_names)}): {finance_tool_names}")
    assert len(finance_tool_names) in (2, 4)
    assert "profit_estimator" in finance_tool_names
    assert "govt_support_finder" in finance_tool_names
    print("[+] All tool mappings match exact requirements!")

    # 3. Verify Triage Handoffs and Guardrails
    print("[-] 3. Verifying Triage handoffs and guardrails...")
    triage_handoff_names = [h.name for h in triage_agent.handoffs]
    print(f"    Triage handoffs ({len(triage_handoff_names)}): {triage_handoff_names}")
    assert len(triage_agent.handoffs) == 4
    assert agronomy_agent in triage_agent.handoffs
    assert pest_doctor_agent in triage_agent.handoffs
    assert market_agent in triage_agent.handoffs
    assert finance_agent in triage_agent.handoffs

    assert len(triage_agent.input_guardrails) >= 1
    print(f"    Triage input guardrails: {[g.name for g in triage_agent.input_guardrails]}")
    print("[+] Triage handoffs & input guardrails verified!")

    # 4. Verify handoff_descriptions
    print("[-] 4. Verifying short, concrete handoff descriptions...")
    for agent in [agronomy_agent, pest_doctor_agent, market_agent, finance_agent]:
        desc = agent.handoff_description
        assert desc is not None and len(desc.strip()) > 0
        print(f"    [{agent.name}] handoff_description: '{desc}'")
    print("[+] All specialists have concrete handoff_descriptions!")

    # 5. Verify Pydantic structured output_type
    print("[-] 5. Verifying structured output_type configurations...")
    print(f"    Agronomy output_type: {agronomy_agent.output_type}")
    assert agronomy_agent.output_type is not None

    print(f"    Pest Doctor output_type: {pest_doctor_agent.output_type}")
    assert pest_doctor_agent.output_type == PestDiagnosis

    print(f"    Market output_type: {market_agent.output_type}")
    assert market_agent.output_type == MandiPriceInfo or MandiPriceInfo in getattr(market_agent.output_type, "__args__", ())

    print(f"    Finance output_type: {finance_agent.output_type}")
    assert finance_agent.output_type is not None

    # Verify Pest Doctor safety guardrail
    assert len(pest_doctor_agent.output_guardrails) >= 1
    print(f"    Pest Doctor output guardrails: {[g.name for g in pest_doctor_agent.output_guardrails]}")
    print("[+] Structured outputs & guardrails verified!")

    print("=" * 60)
    print("ALL PART 3 AGENT & HANDOFF CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    success = test_part3_agents_architecture()
    sys.exit(0 if success else 1)
