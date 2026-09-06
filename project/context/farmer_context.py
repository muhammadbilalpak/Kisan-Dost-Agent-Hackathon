"""
Kisan Dost — Farmer Context & Profile
=====================================
Typed farmer-profile context for session memory across conversation turns.
Passed to Runner.run() so all tools, guardrails, and agents can access farmer info.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class FarmerContext(BaseModel):
    """
    Shared typed farmer-profile context.

    Fields:
      farmer_name: Name of the farmer (e.g., 'Ahmad')
      district: Farming district (e.g., 'Multan')
      province: Province in Pakistan (e.g., 'Punjab')
      land_size_acres: Total agricultural land under cultivation (e.g., 5.0)
      soil_type: Soil characteristics (e.g., 'clay loam')
      season: Cultivation cycle (e.g., 'Rabi' or 'Kharif')
      water_availability: Water source / status (e.g., 'limited', 'canal', 'tubewell')
      last_crop: Previous crop harvested, specifically present for Crop Rotation Advisor
    """

    farmer_name: str | None = None
    district: str | None = None
    province: str | None = None
    land_size_acres: float | None = None
    soil_type: str | None = None
    season: str | None = None
    water_availability: str | None = None
    last_crop: str | None = None


class FarmerProfile(FarmerContext):
    """
    Backward-compatible alias and helper for FarmerContext.
    Provides property bridges for legacy field names ('name', 'land_acres')
    and helper methods like 'summary()'.
    """

    budget_pkr: float | None = None
    crops_grown: list[str] = Field(default_factory=list)
    conversation_history: list[str] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        # Handle backward-compatible alias keywords
        if "name" in data and "farmer_name" not in data:
            data["farmer_name"] = data.pop("name")
        if "land_acres" in data and "land_size_acres" not in data:
            data["land_size_acres"] = data.pop("land_acres")
        super().__init__(**data)

    @property
    def name(self) -> str | None:
        return self.farmer_name

    @name.setter
    def name(self, value: str | None) -> None:
        self.farmer_name = value

    @property
    def land_acres(self) -> float | None:
        return self.land_size_acres

    @land_acres.setter
    def land_acres(self, value: float | None) -> None:
        self.land_size_acres = value

    def update_from_input(self, user_input: str) -> None:
        """Record input in conversational history."""
        self.conversation_history.append(user_input)

    def summary(self) -> str:
        """Human-readable summary of known farmer details."""
        parts: list[str] = []
        if self.farmer_name:
            parts.append(f"Naam: {self.farmer_name}")
        if self.district:
            parts.append(f"District: {self.district}")
        if self.province:
            parts.append(f"Province: {self.province}")
        if self.land_size_acres:
            parts.append(f"Land: {self.land_size_acres} acres")
        if self.soil_type:
            parts.append(f"Soil: {self.soil_type}")
        if self.season:
            parts.append(f"Season: {self.season}")
        if self.water_availability:
            parts.append(f"Water: {self.water_availability}")
        if self.last_crop:
            parts.append(f"Last Crop: {self.last_crop}")
        return " | ".join(parts) if parts else "No farmer info collected yet."
