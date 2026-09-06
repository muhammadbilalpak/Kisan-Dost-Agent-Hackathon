"""
Kisan Dost — Crop Rotation Advisor (Extra Tool)
================================================
Advises on multi-season crop rotation patterns for Pakistani farming systems.
Uses previous-season crop (from FarmerContext.last_crop via Session) to recommend
next crop(s), improve soil health, and avoid pest carryover.
Returns typed RotationAdvice model.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import RotationAdvice

ROTATION_GUIDELINES: dict[str, dict] = {
    "wheat": {
        "next": ["Cotton", "Mungbean", "Sesbania (Green Manure)"],
        "reasoning": "Cotton utilizes deep residual moisture. Sowing a quick leguminous catch crop (Mungbean) replenishes nitrogen before cotton. Sesbania as green manure enriches organic matter.",
    },
    "cotton": {
        "next": ["Wheat", "Berseem Clover", "Chickpea (Chana)"],
        "reasoning": "Breaks the insect pest cycle of cotton whitefly and pink bollworm. Wheat feeds on remaining nutrients. Berseem adds nitrogen for next Kharif.",
    },
    "rice": {
        "next": ["Wheat", "Chickpea (Barani)", "Potato"],
        "reasoning": "Rice-Wheat is the standard Punjab cropping system. Using Super Seeder to incorporate paddy straw enhances soil carbon. Potato is a high-value alternative.",
    },
    "maize": {
        "next": ["Potato", "Peas (Spring)", "Wheat"],
        "reasoning": "Intensive high-value cash crop rotation common in Sahiwal and Pakpattan belts. Potato or peas followed by maize maximizes returns.",
    },
    "sugarcane": {
        "next": ["Wheat", "Berseem Clover"],
        "reasoning": "After sugarcane ratoon (2-3 years), soil needs nitrogen replenishment. Wheat or Berseem is the standard follow-up.",
    },
    "mustard": {
        "next": ["Cotton", "Maize", "Mungbean"],
        "reasoning": "Mustard is a short-duration Rabi oilseed. Follow with Kharif crops like cotton or maize for optimal land use.",
    },
}


@function_tool
def crop_rotation_advisor(
    last_crop: str,
) -> RotationAdvice:
    """Recommend sustainable crop rotation sequence to break pest cycles and replenish soil.

    Args:
        last_crop: The farmer's previous or current crop (e.g. 'cotton', 'rice', 'wheat').
    """
    last_clean = last_crop.lower().strip() if last_crop else "wheat"
    matched_key = None
    for k in ROTATION_GUIDELINES:
        if k in last_clean:
            matched_key = k
            break

    if not matched_key:
        matched_key = "wheat"

    info = ROTATION_GUIDELINES[matched_key]

    return RotationAdvice(
        last_crop=last_clean.title(),
        recommended_next_crop=info["next"],
        reasoning=info["reasoning"],
    )
