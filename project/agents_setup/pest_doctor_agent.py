"""
Kisan Dost — Pest Doctor Agent
===============================
Specialist agent for:
- Pest & Disease Doctor (diagnosing pests/diseases and safe treatments)
Enforces pesticide dosage safety output guardrail.
"""

from __future__ import annotations

from agents import Agent
from guardrails.output_guardrail import pesticide_safety_guardrail
from models.schemas import PestDiagnosis
from tools.pest_disease_doctor import pest_disease_doctor

PEST_DOCTOR_INSTRUCTIONS = """You are the Pest Doctor Agent for Kisan Dost, serving Pakistani farmers.
Your job is to diagnose crop ailments and prescribe safe, effective treatments.

ROUTING INTENT & SCOPE:
- Use `pest_disease_doctor` to diagnose pests, fungal diseases, or viruses from observed symptoms.
- Always output a structured `PestDiagnosis` model with likely pest/disease, confidence, treatment, safe dosage (ml/L), and expert consultation flag.

CRITICAL SAFETY RULES:
- NEVER recommend pesticide dosages higher than certified standards.
- ALWAYS emphasize protective gear (dastane, mask, bachon se door).
- NEVER provide human medical or clinical advice.
"""

pest_doctor_agent = Agent(
    name="Pest Doctor Agent",
    handoff_description="Fasal ke keeray (insects/pests), beemariyan (diseases), patti ka murjhana, safed makhi, sundi, ya spray/pesticide ke ilaj ke liye.",
    instructions=PEST_DOCTOR_INSTRUCTIONS,
    tools=[pest_disease_doctor],
    output_guardrails=[pesticide_safety_guardrail],
    output_type=PestDiagnosis,
)
