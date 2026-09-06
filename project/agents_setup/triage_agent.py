"""
Kisan Dost — Triage Agent
=========================
Main entry point and orchestrator.
Routes the farmer's question to the correct specialist agent:
  - crop / fertilizer / irrigation -> Agronomy Agent
  - pest / disease -> Pest Doctor Agent
  - mandi / market price -> Market Agent
  - profit / financial / government-support -> Finance Agent
Enforces the farming topic input guardrail.
"""
from __future__ import annotations
from agents import Agent
from agents_setup.agronomy_agent import agronomy_agent
from agents_setup.finance_agent import finance_agent
from agents_setup.market_agent import market_agent
from agents_setup.pest_doctor_agent import pest_doctor_agent
from guardrails.input_guardrail import farming_topic_guardrail

TRIAGE_INSTRUCTIONS = """Farmer ke sawal ko sahi specialist agent ko route karo.

ROUTING INTENT RULES:
1. crop / fertilizer / irrigation -> Handoff to Agronomy Agent:
   - Fasal ki sifarish (crop recommendation), zameen/soil, rabi/kharif season
   - Khad ka hisaab (Urea, DAP, NPK bags aur cost)
   - Pani aur aabpashi (irrigation scheduling, timing in days, weather alerts, frost/heatwave)

2. pest / disease -> Handoff to Pest Doctor Agent:
   - Keeray (whitefly, safed makhi, sundi, bollworm, tela, aphid, stem borer)
   - Fasal ki beemariyan (kundi, rust, leaf curl virus, patte peele, murjhana)
   - Keet-nashak spray aur safe pesticide treatment

3. mandi / market price -> Handoff to Market Agent:
   - Mandi wholesale rates, grain market prices across Punjab, Sindh, KPK, Balochistan
   - Fasal bechne ka waqt, rates barh rahe hain ya kam ho rahe hain

4. profit / financial / government-support -> Handoff to Finance Agent:
   - Fasal ka kharcha, expected revenue, munafa andaza (net margin, break-even yield)
   - Sarkari schemes aur subsidies (CM Punjab Kissan Card, Solar Tubewell, Green Tractor, ZTBL loans)

Handoff immediately to the appropriate specialist based on the farmer's core inquiry.
Do not answer farming domain questions directly in Triage; delegate to the specialist team.
"""

triage_agent = Agent(
    name="Triage Agent",
    instructions=TRIAGE_INSTRUCTIONS,
    handoffs=[
        agronomy_agent,
        pest_doctor_agent,
        market_agent,
        finance_agent,
    ],
    input_guardrails=[farming_topic_guardrail],
)
