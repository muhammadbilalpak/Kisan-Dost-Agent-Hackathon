"""
Kisan Dost — Fertilizer Calculator Tool
==========================================
Calculates Urea and DAP bag requirements and total cost in PKR.
Returns typed FertilizerPlan Pydantic model.
Uses crop-specific fertilizer recommendations for Pakistan agriculture.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import FertilizerPlan

# Current prevailing prices per 50kg bag in Pakistan (PKR)
PRICE_UREA_PKR = 3500
PRICE_DAP_PKR = 12000

# Standard fertilizer dosage per acre in 50kg bags
CROP_FERTILIZER_RATES = {
    "wheat": {"urea_per_acre": 2.0, "dap_per_acre": 1.0},
    "gandum": {"urea_per_acre": 2.0, "dap_per_acre": 1.0},
    "cotton": {"urea_per_acre": 3.0, "dap_per_acre": 1.5},
    "kapas": {"urea_per_acre": 3.0, "dap_per_acre": 1.5},
    "rice": {"urea_per_acre": 2.5, "dap_per_acre": 1.0},
    "chawal": {"urea_per_acre": 2.5, "dap_per_acre": 1.0},
    "sugarcane": {"urea_per_acre": 4.0, "dap_per_acre": 2.0},
    "ganna": {"urea_per_acre": 4.0, "dap_per_acre": 2.0},
    "maize": {"urea_per_acre": 3.0, "dap_per_acre": 1.5},
    "makki": {"urea_per_acre": 3.0, "dap_per_acre": 1.5},
    "mustard": {"urea_per_acre": 1.5, "dap_per_acre": 1.0},
    "sarson": {"urea_per_acre": 1.5, "dap_per_acre": 1.0},
    "canola": {"urea_per_acre": 1.5, "dap_per_acre": 1.0},
    "gram": {"urea_per_acre": 0.5, "dap_per_acre": 1.0},
    "chana": {"urea_per_acre": 0.5, "dap_per_acre": 1.0},
    "potato": {"urea_per_acre": 3.5, "dap_per_acre": 2.0},
    "aalu": {"urea_per_acre": 3.5, "dap_per_acre": 2.0},
}


@function_tool
def fertilizer_calculator(crop: str, acres: float) -> FertilizerPlan:
    """Return bags of Urea/DAP and total cost for a crop and land size.

    Args:
        crop: The crop name (e.g. 'wheat', 'cotton', 'rice').
        acres: Total land in acres.
    """
    # ── Validation ──
    if acres <= 0:
        return FertilizerPlan(
            urea_bags=0.0,
            dap_bags=0.0,
            total_cost_pkr=0,
        )

    crop_clean = crop.lower().strip() if crop else "wheat"
    matched_rate = None

    for key, rate in CROP_FERTILIZER_RATES.items():
        if key in crop_clean:
            matched_rate = rate
            break

    # Default fallback rate if crop is unspecified or unknown
    if not matched_rate:
        matched_rate = {"urea_per_acre": 2.0, "dap_per_acre": 1.0}

    urea_total = round(matched_rate["urea_per_acre"] * acres, 2)
    dap_total = round(matched_rate["dap_per_acre"] * acres, 2)

    total_cost = int(round((urea_total * PRICE_UREA_PKR) + (dap_total * PRICE_DAP_PKR)))

    return FertilizerPlan(
        urea_bags=urea_total,
        dap_bags=dap_total,
        total_cost_pkr=total_cost,
    )
