"""
Kisan Dost — Profit Estimator Tool
=====================================
Calculates crop revenue, net margin, and break-even yield per acre.
Returns typed ProfitEstimate Pydantic model.
Validates inputs and handles zero/negative acres or missing costs gracefully.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import ProfitEstimate

# Benchmark Pakistani agricultural economics (yields in kg/acre; price in PKR/maund [40kg])
CROP_ECONOMICS = {
    "wheat": {"yield_kg_per_acre": 1600.0, "price_per_maund": 4000.0, "default_cost_per_acre": 65000.0},
    "gandum": {"yield_kg_per_acre": 1600.0, "price_per_maund": 4000.0, "default_cost_per_acre": 65000.0},
    "cotton": {"yield_kg_per_acre": 1100.0, "price_per_maund": 8500.0, "default_cost_per_acre": 85000.0},
    "kapas": {"yield_kg_per_acre": 1100.0, "price_per_maund": 8500.0, "default_cost_per_acre": 85000.0},
    "rice": {"yield_kg_per_acre": 1800.0, "price_per_maund": 5200.0, "default_cost_per_acre": 80000.0},
    "chawal": {"yield_kg_per_acre": 1800.0, "price_per_maund": 5200.0, "default_cost_per_acre": 80000.0},
    "sugarcane": {"yield_kg_per_acre": 30000.0, "price_per_maund": 440.0, "default_cost_per_acre": 120000.0},
    "ganna": {"yield_kg_per_acre": 30000.0, "price_per_maund": 440.0, "default_cost_per_acre": 120000.0},
    "maize": {"yield_kg_per_acre": 3200.0, "price_per_maund": 2500.0, "default_cost_per_acre": 75000.0},
    "makki": {"yield_kg_per_acre": 3200.0, "price_per_maund": 2500.0, "default_cost_per_acre": 75000.0},
    "mustard": {"yield_kg_per_acre": 800.0, "price_per_maund": 6200.0, "default_cost_per_acre": 45000.0},
    "sarson": {"yield_kg_per_acre": 800.0, "price_per_maund": 6200.0, "default_cost_per_acre": 45000.0},
    "gram": {"yield_kg_per_acre": 600.0, "price_per_maund": 6500.0, "default_cost_per_acre": 35000.0},
    "chana": {"yield_kg_per_acre": 600.0, "price_per_maund": 6500.0, "default_cost_per_acre": 35000.0},
}


@function_tool
def profit_estimator(crop: str, acres: float, input_costs_pkr: float) -> ProfitEstimate:
    """Estimate seasonal profit, expected revenue, and break-even yield for a crop.

    Args:
        crop: Crop being cultivated (e.g. 'wheat', 'cotton', 'rice').
        acres: Total land in acres.
        input_costs_pkr: Total estimated or actual input costs in PKR (seed, fertilizer, irrigation, labor).
    """
    # ── Validation ──
    if acres <= 0:
        return ProfitEstimate(
            total_input_cost_pkr=0.0,
            expected_revenue_pkr=0.0,
            net_margin_pkr=0.0,
            break_even_yield_kg_per_acre=0.0,
        )

    crop_clean = crop.strip().lower() if crop else "wheat"
    matched_eco = None

    for key, data in CROP_ECONOMICS.items():
        if key in crop_clean:
            matched_eco = data
            break

    if not matched_eco:
        matched_eco = CROP_ECONOMICS["wheat"]

    # Calculate input costs: if user entered 0 or negative, estimate from benchmark
    total_cost = float(input_costs_pkr)
    if total_cost <= 0:
        total_cost = matched_eco["default_cost_per_acre"] * acres

    # 1 maund = 40 kg
    price_per_kg = matched_eco["price_per_maund"] / 40.0
    total_expected_yield_kg = matched_eco["yield_kg_per_acre"] * acres
    expected_rev = total_expected_yield_kg * price_per_kg

    net_margin = expected_rev - total_cost

    cost_per_acre = total_cost / acres
    break_even_yield = cost_per_acre / price_per_kg if price_per_kg > 0 else 0.0

    return ProfitEstimate(
        total_input_cost_pkr=round(total_cost, 2),
        expected_revenue_pkr=round(expected_rev, 2),
        net_margin_pkr=round(net_margin, 2),
        break_even_yield_kg_per_acre=round(break_even_yield, 2),
    )
