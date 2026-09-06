"""
Kisan Dost — Labour & Machinery Cost Estimator (Extra Tool)
==========================================================
Calculates land preparation, sowing, and combine harvesting expenses.
Returns typed LabourMachineryCost model.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import LabourMachineryCost


@function_tool
def labour_machinery_cost(
    crop: str = "wheat",
    acres: float = 1.0,
) -> LabourMachineryCost:
    """Estimate tractor machinery operations and agricultural labor costs.

    Args:
        crop: Crop being grown (e.g. 'wheat', 'cotton', 'rice').
        acres: Number of acres cultivated.
    """
    acres_val = max(0.5, float(acres))
    crop_clean = crop.lower().strip() if crop else "wheat"

    if "wheat" in crop_clean:
        prep = 6500.0 * acres_val
        sowing = 2000.0 * acres_val
        harvesting = 6000.0 * acres_val
    elif "cotton" in crop_clean:
        prep = 7500.0 * acres_val
        sowing = 2500.0 * acres_val
        harvesting = 10000.0 * acres_val
    elif "rice" in crop_clean:
        prep = 8500.0 * acres_val
        sowing = 5000.0 * acres_val
        harvesting = 7000.0 * acres_val
    else:
        prep = 6000.0 * acres_val
        sowing = 2200.0 * acres_val
        harvesting = 6500.0 * acres_val

    total = prep + sowing + harvesting

    return LabourMachineryCost(
        land_prep_cost_pkr=round(prep, 2),
        sowing_cost_pkr=round(sowing, 2),
        harvesting_cost_pkr=round(harvesting, 2),
        total_cost_pkr=round(total, 2),
    )
