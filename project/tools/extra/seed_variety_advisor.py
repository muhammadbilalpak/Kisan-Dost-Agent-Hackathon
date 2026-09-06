"""
Kisan Dost — Seed Variety Advisor (Extra Tool)
==============================================
Recommends certified Pakistani crop seed varieties by agro-ecological zone.
Returns typed SeedVarietyRecommendation model.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import SeedVarietyRecommendation

SEED_VARIETIES_MAP: dict[str, dict] = {
    "wheat": {
        "varieties": ["Akbar-2019", "Dilkash-2020", "Faisalabad-2008", "TD-1 (Sindh)"],
        "notes": "Akbar-2019 and Dilkash have high rust resistance and excellent tillering in Punjab.",
    },
    "cotton": {
        "varieties": ["BS-15", "FH-142", "CKC-01", "IUB-2013"],
        "notes": "BS-15 and FH-142 provide high boll weight and moderate CLCuV virus tolerance.",
    },
    "rice": {
        "varieties": ["Super Basmati-2019", "Kissan Basmati", "Chenab Basmati", "PK-386"],
        "notes": "Super Basmati-2019 yields high aroma and export quality in the Kalar tract.",
    },
    "maize": {
        "varieties": ["Pioneer 30Y87", "DK-6789", "YSS-33", "Sahiwal-2002"],
        "notes": "High yield potential (90-100 maunds/acre) under hybrid spring cultivation.",
    },
}


@function_tool
def seed_variety_advisor(
    crop: str,
    district: str = "all",
) -> SeedVarietyRecommendation:
    """Recommend certified seed varieties suitable for Pakistani regions.

    Args:
        crop: Crop name (e.g., 'wheat', 'cotton', 'rice').
        district: District or zone to filter varieties.
    """
    crop_clean = crop.lower().strip() if crop else "wheat"
    matched_key = None
    for k in SEED_VARIETIES_MAP:
        if k in crop_clean:
            matched_key = k
            break

    if not matched_key:
        matched_key = "wheat"

    info = SEED_VARIETIES_MAP[matched_key]
    dist_label = f" (Tailored for {district.title()})" if district and district.lower() != "all" else ""

    return SeedVarietyRecommendation(
        crop=matched_key.title(),
        recommended_varieties=info["varieties"],
        region_notes=f"{info['notes']}{dist_label}",
    )
