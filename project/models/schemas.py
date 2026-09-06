"""
Kisan Dost — Pydantic Structured Output Models
===============================================
All schema definitions for the seven core PDF tools,
the extended PDF-Se-Aagay tools, and safety guardrails.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────
#  1. Core 7 Tool Return Models
# ──────────────────────────────────────────────


class CropRecommendation(BaseModel):
    """Recommendation for a single crop."""
    crop_name: str
    expected_yield_kg_per_acre: float
    expected_profit_pkr_per_acre: float
    water_requirement: str
    notes: str


class CropPlan(BaseModel):
    """Return model for crop_advisor."""
    top_crops: list[CropRecommendation]
    season: str
    reasoning: str


class FertilizerPlan(BaseModel):
    """Return model for fertilizer_calculator."""
    urea_bags: float
    dap_bags: float
    total_cost_pkr: int


class PestDiagnosis(BaseModel):
    """Return model for pest_disease_doctor."""
    likely_pest_or_disease: str
    confidence: str
    treatment: str
    dosage_ml_per_liter: float
    max_safe_dosage_ml_per_liter: float
    requires_expert_consultation: bool


class IrrigationAdvice(BaseModel):
    """Return model for irrigation_weather_advisor."""
    next_irrigation_in_days: int
    weather_summary: str
    frost_risk: bool
    heatwave_risk: bool


class MandiPriceInfo(BaseModel):
    """Return model for mandi_price_lookup."""
    commodity: str
    mandi_name: str
    price_per_maund_pkr: float
    price_date: str
    recommendation: str


class ProfitEstimate(BaseModel):
    """Return model for profit_estimator."""
    total_input_cost_pkr: float
    expected_revenue_pkr: float
    net_margin_pkr: float
    break_even_yield_kg_per_acre: float


class SchemeInfo(BaseModel):
    """Single agricultural support scheme details."""
    scheme_name: str
    eligibility: str
    how_to_apply: str


class GovtSupportInfo(BaseModel):
    """Return model for govt_support_finder."""
    applicable_schemes: list[SchemeInfo]


# ──────────────────────────────────────────────
#  2. Extended Tools Return Models (PDF-Se-Aagay)
# ──────────────────────────────────────────────


class SeedVarietyRecommendation(BaseModel):
    """Return model for seed_variety_advisor."""
    crop: str
    recommended_varieties: list[str]
    region_notes: str


class LabourMachineryCost(BaseModel):
    """Return model for labour_machinery_cost."""
    land_prep_cost_pkr: float
    sowing_cost_pkr: float
    harvesting_cost_pkr: float
    total_cost_pkr: float


class IrrigationCostEstimate(BaseModel):
    """Return model for irrigation_cost."""
    source: str
    cost_per_irrigation_pkr: float
    irrigations_needed: int
    total_water_cost_pkr: float


class LoanEmiPlan(BaseModel):
    """Return model for loan_emi_calculator."""
    loan_amount_pkr: float
    tenure_months: int
    interest_rate_percent: float
    monthly_installment_pkr: float


class StorageAdvice(BaseModel):
    """Return model for storage_advisor."""
    recommended_practice: str
    estimated_shelf_life_days: int


class RotationAdvice(BaseModel):
    """Return model for crop_rotation_advisor."""
    last_crop: str
    recommended_next_crop: list[str]
    reasoning: str

    @field_validator("recommended_next_crop", mode="before")
    @classmethod
    def _coerce_to_list(cls, v: object) -> object:
        if isinstance(v, str):
            return [v]
        return v


# ──────────────────────────────────────────────
#  3. Safety Guardrail Models
# ──────────────────────────────────────────────


class TopicSafetyCheck(BaseModel):
    """Output for the topic_checker_agent input guardrail."""
    is_farming_related: bool
    is_safe: bool
    reasoning: str


class PesticideSafetyCheck(BaseModel):
    """Output for the pesticide dosage output guardrail."""
    dosage_within_safe_limit: bool
    contains_human_medical_advice: bool
    reasoning: str


# Aliases for backward compatibility
GuardrailCheck = TopicSafetyCheck
DosageSafetyCheck = PesticideSafetyCheck


# ──────────────────────────────────────────────
#  4. Farmer Context & Profile Models
# ──────────────────────────────────────────────


class FarmerContext(BaseModel):
    """
    Shared typed farmer-profile context across conversation turns.

    Used directly by Runner.run(..., context=farmer_ctx) so agents,
    tools, and guardrails have access to the farmer's state.
    """

    farmer_name: str | None = None
    district: str | None = None
    province: str | None = None
    land_size_acres: float | None = None
    soil_type: str | None = None
    season: str | None = None
    water_availability: str | None = None
    last_crop: str | None = None
