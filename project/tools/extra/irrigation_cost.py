"""
Kisan Dost — Irrigation Cost Calculator (Extra Tool)
===================================================
Calculates irrigation expenses across diesel, electric, solar tubewells, and canal.
Returns typed IrrigationCostEstimate model.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import IrrigationCostEstimate

RATES_PER_IRRIGATION_PKR = {
    "diesel": 3500.0,
    "electric": 1800.0,
    "solar": 150.0,
    "canal": 350.0,
}


@function_tool
def irrigation_cost(
    source: str = "diesel",
    irrigations_needed: int = 5,
) -> IrrigationCostEstimate:
    """Calculate and compare irrigation expenses for Pakistani farming operations.

    Args:
        source: 'diesel', 'electric', 'solar', or 'canal'.
        irrigations_needed: Total number of irrigations across the season (default 5).
    """
    src_clean = source.lower().strip() if source else "diesel"
    num_irrig = max(1, int(irrigations_needed))

    cost_per_irrig = RATES_PER_IRRIGATION_PKR.get(src_clean, 3500.0)
    total_water_cost = cost_per_irrig * num_irrig

    return IrrigationCostEstimate(
        source=src_clean.title(),
        cost_per_irrigation_pkr=round(cost_per_irrig, 2),
        irrigations_needed=num_irrig,
        total_water_cost_pkr=round(total_water_cost, 2),
    )
