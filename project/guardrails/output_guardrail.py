"""
Kisan Dost — Output Guardrail (Pest Doctor)
===========================================
Ensures pesticide recommendations are within safe dosage limits and contain
no human-medical advice.
Uses the independent lookup table (data/safe_dosage_limits.csv) as the ground truth.
"""

from __future__ import annotations

import csv
import os
import re

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    output_guardrail,
)
from models.schemas import PesticideSafetyCheck, PestDiagnosis

SAFE_LIMITS_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "safe_dosage_limits.csv")

# Baseline hardcoded safety table as fallback / fast lookup
INDEPENDENT_SAFE_LIMITS = {
    "pyriproxyfen": 4.0,       # ml / liter
    "acetamiprid": 2.5,        # g or ml / liter
    "flonicamid": 1.5,         # g or ml / liter
    "diafenthiuron": 2.5,      # ml / liter
    "emamectin": 3.0,          # ml / liter
    "chlorpyrifos": 10.0,      # ml / liter
    "propiconazole": 3.0,      # ml / liter
    "tebuconazole": 3.0,       # ml / liter
    "imidacloprid": 4.0,       # ml / liter
    "confidor": 4.0,           # ml / liter
    "proclaim": 3.0,           # ml / liter
    "tilt": 3.0,               # ml / liter
    "mospilan": 2.5,           # g / liter
    "polo": 2.5,               # ml / liter
}

# Human-medical keywords that violate output safety
HUMAN_MEDICAL_PATTERNS = [
    r"\b(tablet|capsule|syrup|goli|pills?)\b",
    r"\b(paracetamol|panadol|aspirin|ibuprofen|antibiotic)\b",
    r"\b(swallow|drink|ingest|oral\s+consumption|khana|peena)\b",
    r"\b(human\s+fever|bukhar|human\s+infection|blood\s+pressure)\b",
    r"\b(inject|intravenous|drip|tika\s+lagayein)\b",
    r"\b(treat\s+wound|bandage|human\s+skin\s+cure)\b",
]


def _load_independent_dosage_limits() -> dict[str, float]:
    """Load independent safe limits from data/safe_dosage_limits.csv."""
    limits = dict(INDEPENDENT_SAFE_LIMITS)
    if os.path.exists(SAFE_LIMITS_CSV_PATH):
        try:
            with open(SAFE_LIMITS_CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chem = row.get("chemical_name", "").lower()
                    dose_str = row.get("max_safe_dosage_ml_per_liter", "")
                    if dose_str:
                        try:
                            val = float(dose_str)
                            # Store keywords
                            for part in chem.split():
                                clean_part = part.strip(",.()")
                                if len(clean_part) > 3:
                                    limits[clean_part] = val
                        except ValueError:
                            pass
        except Exception:
            pass
    return limits


def contains_human_medical_language(treatment_text: str) -> bool:
    """
    Check if the treatment advice contains human medical advice.
    Farming disclaimers ('Doctor se raabta karein') are allowed.
    """
    text_lower = treatment_text.lower()

    # Allowed disclaimers — remove them before checking for clinical advice
    safe_disclaimers = [
        "doctor se raabta karein",
        "doctor se ruju karein",
        "consult a doctor if exposed",
        "visit nearest hospital in case of accidental poisoning",
        "keep away from children",
        "bachon se door rakhein",
    ]
    cleaned_text = text_lower
    for disc in safe_disclaimers:
        cleaned_text = cleaned_text.replace(disc, "")

    for pattern in HUMAN_MEDICAL_PATTERNS:
        if re.search(pattern, cleaned_text):
            return True

    return False


def _get_independent_limit_for_text(text: str, fallback_limit: float = 5.0) -> float:
    """Find the certified maximum safe limit from the independent lookup table."""
    limits = _load_independent_dosage_limits()
    text_lower = text.lower()
    for chem, limit in limits.items():
        if chem in text_lower:
            return limit
    return fallback_limit


@output_guardrail
async def pesticide_safety_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output: PestDiagnosis | str | dict,
) -> GuardrailFunctionOutput:
    """
    Output guardrail on the Pest Doctor Agent that validates dosage limits
    against the independent lookup table and rejects human medical advice.
    """
    dosage = 0.0
    max_safe_dosage = 5.0
    treatment_text = ""
    pest_name = ""

    if isinstance(output, PestDiagnosis):
        dosage = float(output.dosage_ml_per_liter)
        max_safe_dosage = float(output.max_safe_dosage_ml_per_liter)
        treatment_text = output.treatment
        pest_name = output.likely_pest_or_disease
    elif isinstance(output, dict):
        dosage = float(output.get("dosage_ml_per_liter", 0.0))
        max_safe_dosage = float(output.get("max_safe_dosage_ml_per_liter", 5.0))
        treatment_text = str(output.get("treatment", ""))
        pest_name = str(output.get("likely_pest_or_disease", ""))
    else:
        treatment_text = str(output)
        pest_name = treatment_text

    # 1. Critical dosage check: Verify against independent lookup table
    independent_limit = _get_independent_limit_for_text(f"{pest_name} {treatment_text}", max_safe_dosage)
    # Effective upper safe bound is the strict minimum between model limit and certified DPP limit
    effective_limit = min(max_safe_dosage, independent_limit)

    is_safe_dosage = (dosage <= effective_limit) if dosage > 0 else True

    # 2. Human medical language check
    has_medical = contains_human_medical_language(treatment_text)

    # 3. Determine tripwire
    tripwire = (not is_safe_dosage) or has_medical

    reasoning_parts = []
    if not is_safe_dosage:
        reasoning_parts.append(
            f"Dosage ({dosage} ml/L) exceeds certified safe limit ({effective_limit} ml/L)."
        )
    if has_medical:
        reasoning_parts.append("Contains human medical treatment or prescription advice.")
    if not reasoning_parts:
        reasoning_parts.append("Dosage is within safe limits and no human medical advice found.")

    check = PesticideSafetyCheck(
        dosage_within_safe_limit=is_safe_dosage,
        contains_human_medical_advice=has_medical,
        reasoning=" ".join(reasoning_parts),
    )

    return GuardrailFunctionOutput(
        output_info=check,
        tripwire_triggered=tripwire,
    )
