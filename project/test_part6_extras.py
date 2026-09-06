"""
Kisan Dost — Part 6 Extra Tools, Agent Wiring, and Open-Meteo API Test Suite
==============================================================================
Validates:
1. Six extra tools: schemas, typed returns, and invocations.
2. Agent wiring: extra tools correctly mapped to Agronomy, Finance, Market agents.
3. RotationAdvice schema: recommended_next_crop is list[str].
4. Open-Meteo real API: live weather fetch (graceful skip if offline).
5. Roadmap phase alignment is documented.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pydantic import BaseModel

from models.schemas import (
    CropPlan,
    FertilizerPlan,
    IrrigationAdvice,
    IrrigationCostEstimate,
    LabourMachineryCost,
    LoanEmiPlan,
    MandiPriceInfo,
    RotationAdvice,
    SeedVarietyRecommendation,
    StorageAdvice,
)

from tools.extra.seed_variety_advisor import seed_variety_advisor
from tools.extra.crop_rotation_advisor import crop_rotation_advisor
from tools.extra.irrigation_cost import irrigation_cost
from tools.extra.labour_machinery_cost import labour_machinery_cost
from tools.extra.loan_emi_calculator import loan_emi_calculator
from tools.extra.storage_advisor import storage_advisor

from agents_setup.agronomy_agent import agronomy_agent
from agents_setup.finance_agent import finance_agent
from agents_setup.market_agent import market_agent


def test_extra_tool_schemas():
    """Verify all 6 extra tool schemas match the Part 6 specification."""
    print("[-] 1. Testing extra tool Pydantic schemas...")

    # SeedVarietyRecommendation
    svr = SeedVarietyRecommendation(crop="Wheat", recommended_varieties=["Akbar-2019"], region_notes="Punjab")
    assert isinstance(svr.recommended_varieties, list)
    assert svr.crop == "Wheat"
    print("    [PASS] SeedVarietyRecommendation schema OK.")

    # RotationAdvice - must have list[str]
    ra = RotationAdvice(last_crop="Cotton", recommended_next_crop=["Wheat", "Berseem"], reasoning="Test")
    assert isinstance(ra.recommended_next_crop, list)
    assert len(ra.recommended_next_crop) == 2
    print("    [PASS] RotationAdvice.recommended_next_crop is list[str] OK.")

    # IrrigationCostEstimate
    ice = IrrigationCostEstimate(source="Diesel", cost_per_irrigation_pkr=3500.0, irrigations_needed=5, total_water_cost_pkr=17500.0)
    assert ice.total_water_cost_pkr == 17500.0
    print("    [PASS] IrrigationCostEstimate schema OK.")

    # LabourMachineryCost
    lmc = LabourMachineryCost(land_prep_cost_pkr=6500.0, sowing_cost_pkr=2000.0, harvesting_cost_pkr=6000.0, total_cost_pkr=14500.0)
    assert lmc.total_cost_pkr == 14500.0
    print("    [PASS] LabourMachineryCost schema OK.")

    # LoanEmiPlan
    lep = LoanEmiPlan(loan_amount_pkr=150000.0, tenure_months=6, interest_rate_percent=0.0, monthly_installment_pkr=25000.0)
    assert lep.monthly_installment_pkr == 25000.0
    print("    [PASS] LoanEmiPlan schema OK.")

    # StorageAdvice
    sa = StorageAdvice(recommended_practice="Dry grain to below 11%", estimated_shelf_life_days=365)
    assert sa.estimated_shelf_life_days == 365
    print("    [PASS] StorageAdvice schema OK.")

    print("[+] All 6 extra tool schemas verified!\n")


def test_extra_tool_invocations():
    """Verify each extra tool returns correct typed output."""
    print("[-] 2. Testing extra tool invocations...")

    # Access the underlying callable
    seed_fn = seed_variety_advisor.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__
    rotation_fn = crop_rotation_advisor.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__
    irrig_cost_fn = irrigation_cost.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__
    labour_fn = labour_machinery_cost.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__
    loan_fn = loan_emi_calculator.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__
    storage_fn = storage_advisor.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__

    # Seed Variety Advisor
    result_seed = seed_fn(crop="wheat", district="Multan")
    assert isinstance(result_seed, SeedVarietyRecommendation)
    assert len(result_seed.recommended_varieties) > 0
    print(f"    [PASS] seed_variety_advisor -> {result_seed.crop}: {result_seed.recommended_varieties}")

    # Crop Rotation Advisor
    result_rotation = rotation_fn(last_crop="cotton")
    assert isinstance(result_rotation, RotationAdvice)
    assert isinstance(result_rotation.recommended_next_crop, list)
    assert len(result_rotation.recommended_next_crop) >= 2
    print(f"    [PASS] crop_rotation_advisor -> last_crop=Cotton, next={result_rotation.recommended_next_crop}")

    # Irrigation Cost
    result_irrig = irrig_cost_fn(source="diesel", irrigations_needed=6)
    assert isinstance(result_irrig, IrrigationCostEstimate)
    assert result_irrig.total_water_cost_pkr > 0
    print(f"    [PASS] irrigation_cost -> {result_irrig.source}: PKR {result_irrig.total_water_cost_pkr}")

    # Labour & Machinery Cost
    result_labour = labour_fn(crop="wheat", acres=5.0)
    assert isinstance(result_labour, LabourMachineryCost)
    assert result_labour.total_cost_pkr > 0
    print(f"    [PASS] labour_machinery_cost -> 5 acres wheat: PKR {result_labour.total_cost_pkr}")

    # Loan EMI Calculator
    result_loan = loan_fn(loan_amount_pkr=150000.0, tenure_months=6, interest_rate_percent=0.0)
    assert isinstance(result_loan, LoanEmiPlan)
    assert result_loan.monthly_installment_pkr == 25000.0
    print(f"    [PASS] loan_emi_calculator -> PKR {result_loan.monthly_installment_pkr}/month (0% markup)")

    # Storage Advisor
    result_storage = storage_fn(crop="wheat")
    assert isinstance(result_storage, StorageAdvice)
    assert result_storage.estimated_shelf_life_days > 0
    print(f"    [PASS] storage_advisor -> wheat: {result_storage.estimated_shelf_life_days} days")

    print("[+] All 6 extra tool invocations verified!\n")


def test_agent_wiring():
    """Verify extra tools are wired to the correct specialist agents."""
    print("[-] 3. Testing extra tool -> agent wiring...")

    # Agronomy Agent: should have 6 tools (3 core + 3 extra)
    agronomy_tool_names = sorted([t.name for t in agronomy_agent.tools])
    expected_agronomy = sorted([
        "crop_advisor", "fertilizer_calculator", "irrigation_weather_advisor",
        "seed_variety_advisor", "crop_rotation_advisor", "irrigation_cost",
    ])
    assert agronomy_tool_names == expected_agronomy, f"Agronomy tools mismatch: {agronomy_tool_names}"
    print(f"    [PASS] Agronomy Agent tools (6): {agronomy_tool_names}")

    # Finance Agent: should have 4 tools (2 core + 2 extra)
    finance_tool_names = sorted([t.name for t in finance_agent.tools])
    expected_finance = sorted([
        "profit_estimator", "govt_support_finder",
        "labour_machinery_cost", "loan_emi_calculator",
    ])
    assert finance_tool_names == expected_finance, f"Finance tools mismatch: {finance_tool_names}"
    print(f"    [PASS] Finance Agent tools (4): {finance_tool_names}")

    # Market Agent: should have 2 tools (1 core + 1 extra)
    market_tool_names = sorted([t.name for t in market_agent.tools])
    expected_market = sorted(["mandi_price_lookup", "storage_advisor"])
    assert market_tool_names == expected_market, f"Market tools mismatch: {market_tool_names}"
    print(f"    [PASS] Market Agent tools (2): {market_tool_names}")

    print("[+] All extra tools correctly wired to agents!\n")


def test_open_meteo_api():
    """Test Open-Meteo real API integration (graceful skip if offline)."""
    print("[-] 4. Testing Open-Meteo real API integration...")

    from tools.irrigation_weather import _geocode_district, _fetch_open_meteo_weather

    # Test geocode with known district
    coords = _geocode_district("multan")
    assert coords is not None, "Local lookup for 'multan' should always succeed"
    lat, lon = coords
    assert abs(lat - 30.20) < 1.0
    assert abs(lon - 71.45) < 1.0
    print(f"    [PASS] Geocoded 'multan' -> lat={lat}, lon={lon}")

    # Test live weather fetch (may fail if offline)
    weather = _fetch_open_meteo_weather(lat, lon)
    if weather:
        assert "current" in weather
        temp = weather["current"].get("temperature_2m", "N/A")
        print(f"    [PASS] Open-Meteo LIVE weather for Multan: {temp}C")
    else:
        print("    [SKIP] Open-Meteo API unreachable (offline mode). Offline fallback will be used.")

    # Test tool invocation with real API
    from tools.irrigation_weather import irrigation_weather_advisor
    irrig_fn = irrigation_weather_advisor.on_invoke_tool._invoke_tool_impl.__agents_function_tool_wrapped_callable__
    result = irrig_fn(district="Multan", crop="wheat", crop_stage="tillering")
    assert isinstance(result, IrrigationAdvice)
    assert result.next_irrigation_in_days > 0
    assert len(result.weather_summary) > 0

    if "LIVE" in result.weather_summary:
        print(f"    [PASS] irrigation_weather_advisor used LIVE Open-Meteo data!")
    else:
        print(f"    [PASS] irrigation_weather_advisor used OFFLINE fallback data.")

    print(f"    [PASS] Weather summary: '{result.weather_summary[:80]}...'")
    print("[+] Open-Meteo integration verified!\n")


def test_rotation_advice_list_type():
    """Verify RotationAdvice.recommended_next_crop is list[str] per Part 6 spec."""
    print("[-] 5. Testing RotationAdvice schema type...")
    import typing

    field_info = RotationAdvice.model_fields["recommended_next_crop"]
    annotation = field_info.annotation

    # Check annotation is list[str]
    origin = getattr(annotation, "__origin__", None)
    assert origin is list, f"Expected list, got {origin}"
    print("    [PASS] RotationAdvice.recommended_next_crop type is list[str].")
    print("[+] Schema type verified!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("KISAN DOST — PART 6 EXTRA TOOLS & REAL API TEST SUITE")
    print("=" * 60)
    test_extra_tool_schemas()
    test_extra_tool_invocations()
    test_agent_wiring()
    test_open_meteo_api()
    test_rotation_advice_list_type()
    print("=" * 60)
    print("ALL PART 6 EXTRA TOOLS & REAL API CHECKS PASSED!")
    print("=" * 60)
