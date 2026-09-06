"""
Kisan Dost — Crop Advisor Tool
================================
Recommends best crops based on district, soil, season, water, and land size.
Returns typed CropPlan Pydantic model.
Uses realistic Pakistan agricultural datasets and agronomy guidelines.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import CropPlan, CropRecommendation

# Pakistan Crop Knowledge Base (Yields in kg/acre; 1 maund = 40 kg)
CROP_DATA: dict[str, list[dict]] = {
    "rabi": [
        {
            "crop_name": "Wheat (Gandum)",
            "base_yield_kg": 1600.0,  # ~40 maunds
            "base_profit_pkr": 95000.0,
            "water_req": "medium",
            "suitable_soils": ["loamy", "clay", "clay loam", "alluvial", "silty loam"],
            "water_tolerance": ["canal", "tubewell", "limited"],
            "notes": "Optimal Rabi staple. Certified varieties Akbar-2019, Dilkash recommended.",
        },
        {
            "crop_name": "Mustard / Canola (Sarson)",
            "base_yield_kg": 800.0,   # ~20 maunds
            "base_profit_pkr": 80000.0,
            "water_req": "low",
            "suitable_soils": ["sandy", "sandy loam", "loamy"],
            "water_tolerance": ["limited", "tubewell", "rainfed"],
            "notes": "Excellent low-water oilseed option with strong market demand.",
        },
        {
            "crop_name": "Gram / Chickpea (Chana)",
            "base_yield_kg": 600.0,   # ~15 maunds
            "base_profit_pkr": 75000.0,
            "water_req": "low",
            "suitable_soils": ["sandy", "sandy loam", "loamy"],
            "water_tolerance": ["limited", "rainfed"],
            "notes": "Ideal for Thal/barani zones; fixes nitrogen for subsequent crops.",
        },
        {
            "crop_name": "Potato (Aalu)",
            "base_yield_kg": 10000.0, # ~250 maunds
            "base_profit_pkr": 160000.0,
            "water_req": "high",
            "suitable_soils": ["loamy", "sandy loam"],
            "water_tolerance": ["canal", "tubewell"],
            "notes": "High capital input and high return cash crop. Sensitive to frost.",
        },
    ],
    "kharif": [
        {
            "crop_name": "Cotton (Kapas)",
            "base_yield_kg": 1100.0,  # ~27.5 maunds
            "base_profit_pkr": 115000.0,
            "water_req": "medium",
            "suitable_soils": ["loamy", "clay loam", "alluvial"],
            "water_tolerance": ["canal", "tubewell", "limited"],
            "notes": "Silver fiber cash crop. Monitor whitefly and pink bollworm actively.",
        },
        {
            "crop_name": "Basmati Rice (Chawal)",
            "base_yield_kg": 1800.0,  # ~45 maunds
            "base_profit_pkr": 130000.0,
            "water_req": "high",
            "suitable_soils": ["clay", "clay loam", "heavy loam"],
            "water_tolerance": ["canal", "tubewell"],
            "notes": "Requires abundant standing water. Best suited for Kalar/canal zones.",
        },
        {
            "crop_name": "Maize (Makki)",
            "base_yield_kg": 3200.0,  # ~80 maunds
            "base_profit_pkr": 110000.0,
            "water_req": "medium",
            "suitable_soils": ["loamy", "sandy loam"],
            "water_tolerance": ["canal", "tubewell"],
            "notes": "High-yielding grain/silage crop popular with poultry and dairy feed mills.",
        },
        {
            "crop_name": "Mungbean (Moong)",
            "base_yield_kg": 500.0,   # ~12.5 maunds
            "base_profit_pkr": 60000.0,
            "water_req": "low",
            "suitable_soils": ["sandy loam", "loamy"],
            "water_tolerance": ["limited", "rainfed"],
            "notes": "Short duration (65-70 days) pulse, drought tolerant and enriches soil.",
        },
    ],
}


@function_tool
def crop_advisor(
    district: str,
    soil_type: str,
    season: str,
    water_availability: str,
    land_size_acres: float,
) -> CropPlan:
    """Recommend best crops for the given district, soil, season, water and land size.

    Args:
        district: Farmer's district (e.g. 'Multan').
        soil_type: e.g. 'loamy', 'clay', 'sandy'.
        season: 'Rabi' or 'Kharif'.
        water_availability: e.g. 'limited', 'canal', 'tubewell'.
        land_size_acres: Total cultivable land in acres.
    """
    # ── Validation ──
    # 1. Land size validation
    if land_size_acres <= 0:
        return CropPlan(
            top_crops=[],
            season=season if season else "Unknown",
            reasoning=f"Invalid land size: {land_size_acres} acres. Land size must be greater than 0.",
        )

    # 2. Season validation
    season_clean = season.strip().capitalize() if season else ""
    if season_clean not in {"Rabi", "Kharif"}:
        return CropPlan(
            top_crops=[],
            season=season if season else "Unknown",
            reasoning=f"Invalid season '{season}'. Allowed seasons are 'Rabi' (winter) or 'Kharif' (summer).",
        )

    # 3. Clean and sanitize other inputs
    dist_clean = district.strip().title() if district else "General Pakistan"
    soil_clean = soil_type.strip().lower() if soil_type else "loamy"
    water_clean = water_availability.strip().lower() if water_availability else "canal"

    season_key = season_clean.lower()
    candidates = CROP_DATA.get(season_key, [])

    recommended_list: list[CropRecommendation] = []

    for crop in candidates:
        # Check water compatibility
        water_match = (
            water_clean in crop["water_tolerance"]
            or any(w in water_clean for w in crop["water_tolerance"])
        )
        if not water_match and water_clean == "limited" and crop["water_req"] == "high":
            # Skip high water crops if farmer has limited water
            continue

        # Adjust yields and profits based on water and land
        water_factor = 0.85 if water_clean == "limited" else 1.05 if "canal" in water_clean else 1.0
        exp_yield = round(crop["base_yield_kg"] * water_factor, 1)
        exp_profit = round(crop["base_profit_pkr"] * water_factor, 1)

        notes_addon = f"For {dist_clean} conditions on {soil_clean} soil."
        if water_clean == "limited":
            notes_addon += " Water-saving bed planting or drip recommended."

        rec = CropRecommendation(
            crop_name=crop["crop_name"],
            expected_yield_kg_per_acre=exp_yield,
            expected_profit_pkr_per_acre=exp_profit,
            water_requirement=crop["water_req"],
            notes=f"{crop['notes']} {notes_addon}",
        )
        recommended_list.append(rec)

    # Sort crops by expected profit
    recommended_list.sort(key=lambda r: r.expected_profit_pkr_per_acre, reverse=True)

    reasoning_text = (
        f"Recommended {len(recommended_list)} crops for {dist_clean} in {season_clean} season "
        f"with {soil_clean} soil and {water_clean} water on {land_size_acres} acres."
    )

    return CropPlan(
        top_crops=recommended_list,
        season=season_clean,
        reasoning=reasoning_text,
    )
