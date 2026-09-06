"""
Kisan Dost — Storage & Post-Harvest Advisor (Extra Tool)
=======================================================
Advises on moisture thresholds, grain fumigation, and storage safety to prevent post-harvest loss.
Returns typed StorageAdvice model.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import StorageAdvice

STORAGE_PRACTICES = {
    "wheat": {
        "practice": "Dry grain to below 11% moisture. Store in clean bardana bags placed on raised wooden pallets 6 inches above floor and away from walls. Fumigate with 2-3 Aluminium Phosphide tablets per ton in airtight conditions.",
        "shelf_life_days": 365,
    },
    "rice": {
        "practice": "Ensure paddy moisture is below 12-13%. Avoid direct concrete contact. Use hermetic storage bags (e.g. SuperGrainbags) to eliminate insects without chemicals.",
        "shelf_life_days": 300,
    },
    "maize": {
        "practice": "Sun-dry kernels to below 13% moisture. Screen out broken grains before storage to prevent Aspergillus and aflatoxin contamination.",
        "shelf_life_days": 240,
    },
    "potato": {
        "practice": "Cure tubers for 10-14 days at 15°C for skin setting. Store in commercial cold storage at 3-4°C with 90-95% relative humidity.",
        "shelf_life_days": 180,
    },
}


@function_tool
def storage_advisor(
    crop: str = "wheat",
) -> StorageAdvice:
    """Provide post-harvest grain storage advice, moisture limits, and safe fumigation guidelines.

    Args:
        crop: Crop being stored (e.g. 'wheat', 'rice', 'maize', 'potato').
    """
    crop_clean = crop.lower().strip() if crop else "wheat"
    matched_key = None
    for k in STORAGE_PRACTICES:
        if k in crop_clean:
            matched_key = k
            break

    if not matched_key:
        matched_key = "wheat"

    info = STORAGE_PRACTICES[matched_key]

    return StorageAdvice(
        recommended_practice=info["practice"],
        estimated_shelf_life_days=info["shelf_life_days"],
    )
