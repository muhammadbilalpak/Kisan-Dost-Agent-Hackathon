"""
Kisan Dost — Agronomy Agent
============================
Specialist agent for:
- Crop Advisor (crop recommendations)
- Fertilizer Calculator (Urea/DAP requirements & cost)
- Irrigation & Weather (watering schedule & weather risk alerts)
- [Extra] Seed Variety Advisor (certified resistant varieties by region)
- [Extra] Crop Rotation Advisor (multi-season rotation for soil health)
- [Extra] Irrigation Cost Calculator (tubewell/canal cost comparison)
"""

from __future__ import annotations

from typing import Union

from agents import Agent
from models.schemas import (
    CropPlan,
    FertilizerPlan,
    IrrigationAdvice,
    IrrigationCostEstimate,
    RotationAdvice,
    SeedVarietyRecommendation,
)
from tools.crop_advisor import crop_advisor
from tools.fertilizer_calculator import fertilizer_calculator
from tools.irrigation_weather import irrigation_weather_advisor
from tools.extra.seed_variety_advisor import seed_variety_advisor
from tools.extra.crop_rotation_advisor import crop_rotation_advisor
from tools.extra.irrigation_cost import irrigation_cost

AGRONOMY_INSTRUCTIONS = """You are the Agronomy Agent for Kisan Dost, serving Pakistani farmers.
Your job is to provide expert guidance on crop selection, fertilizer calculation, and irrigation scheduling.

CORE TOOLS:
- Use `crop_advisor` to recommend best crops based on district, soil, season, water, and land size.
- Use `fertilizer_calculator` to calculate bags of Urea and DAP along with total cost in PKR.
- Use `irrigation_weather_advisor` to provide irrigation timing in days and weather/frost/heatwave alerts.

EXTRA TOOLS:
- Use `seed_variety_advisor` to recommend certified approved/resistant seed varieties by crop and region.
- Use `crop_rotation_advisor` to suggest next-season crop rotation based on farmer's last crop (from context).
- Use `irrigation_cost` to calculate and compare tubewell/canal irrigation expenses.

Always return structured Pydantic output using the corresponding model.
Provide clear, practical reasoning in Urdu or English suitable for Pakistani farmers.
"""

agronomy_agent = Agent(
    name="Agronomy Agent",
    handoff_description="Fasal ki sifarish (crop recommendation), khad ka hisaab (fertilizer calculation), ya pani aur mausam (irrigation & weather) ke liye.",
    instructions=AGRONOMY_INSTRUCTIONS,
    tools=[
        crop_advisor,
        fertilizer_calculator,
        irrigation_weather_advisor,
        seed_variety_advisor,
        crop_rotation_advisor,
        irrigation_cost,
    ],
    output_type=Union[CropPlan, FertilizerPlan, IrrigationAdvice, SeedVarietyRecommendation, RotationAdvice, IrrigationCostEstimate],
)
