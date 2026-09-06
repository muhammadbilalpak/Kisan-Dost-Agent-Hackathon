"""
Kisan Dost — Test Suite for Part 2 Core 7 Tools & Pydantic Schemas
===================================================================
Tests all 7 mandatory tools and the Pydantic models:
1. crop_advisor -> CropPlan
2. fertilizer_calculator -> FertilizerPlan
3. pest_disease_doctor -> PestDiagnosis
4. irrigation_weather_advisor -> IrrigationAdvice
5. mandi_price_lookup -> MandiPriceInfo
6. profit_estimator -> ProfitEstimate
7. govt_support_finder -> GovtSupportInfo
Also validates input handling and edge cases (negative acres, invalid season, empty symptoms, etc.)
"""

import sys
from models.schemas import (
    CropPlan,
    CropRecommendation,
    FertilizerPlan,
    PestDiagnosis,
    IrrigationAdvice,
    MandiPriceInfo,
    ProfitEstimate,
    GovtSupportInfo,
    SchemeInfo,
    SeedVarietyRecommendation,
    LabourMachineryCost,
    IrrigationCostEstimate,
    LoanEmiPlan,
    StorageAdvice,
    RotationAdvice,
)

from tools.crop_advisor import crop_advisor
from tools.fertilizer_calculator import fertilizer_calculator
from tools.pest_disease_doctor import pest_disease_doctor
from tools.irrigation_weather import irrigation_weather_advisor
from tools.mandi_price_lookup import mandi_price_lookup
from tools.profit_estimator import profit_estimator
from tools.govt_support_finder import govt_support_finder


def get_tool_fn(tool):
    """Extract underlying python function from openai-agents FunctionTool."""
    if hasattr(tool, "on_invoke_tool") and hasattr(tool.on_invoke_tool, "_invoke_tool_impl"):
        return getattr(tool.on_invoke_tool._invoke_tool_impl, "__agents_function_tool_wrapped_callable__", tool)
    return tool


# Underlying callable functions
crop_advisor_fn = get_tool_fn(crop_advisor)
fertilizer_calculator_fn = get_tool_fn(fertilizer_calculator)
pest_disease_doctor_fn = get_tool_fn(pest_disease_doctor)
irrigation_weather_fn = get_tool_fn(irrigation_weather_advisor)
mandi_price_lookup_fn = get_tool_fn(mandi_price_lookup)
profit_estimator_fn = get_tool_fn(profit_estimator)
govt_support_finder_fn = get_tool_fn(govt_support_finder)


def test_tool_crop_advisor():
    print("[-] Testing Tool 1: crop_advisor...")
    # Normal case - Rabi
    res_rabi = crop_advisor_fn("Multan", "loamy", "Rabi", "canal", 5.0)
    assert isinstance(res_rabi, CropPlan), f"Expected CropPlan, got {type(res_rabi)}"
    assert res_rabi.season == "Rabi"
    assert len(res_rabi.top_crops) > 0
    assert any("Wheat" in c.crop_name for c in res_rabi.top_crops)
    first_crop = res_rabi.top_crops[0]
    assert isinstance(first_crop, CropRecommendation)
    assert first_crop.expected_yield_kg_per_acre > 0
    assert first_crop.expected_profit_pkr_per_acre > 0

    # Normal case - Kharif
    res_kharif = crop_advisor_fn("Multan", "clay loam", "Kharif", "tubewell", 10.0)
    assert isinstance(res_kharif, CropPlan)
    assert res_kharif.season == "Kharif"
    assert any("Cotton" in c.crop_name for c in res_kharif.top_crops)

    # Validation: negative or zero acres
    res_zero_acres = crop_advisor_fn("Multan", "loamy", "Rabi", "canal", 0.0)
    assert isinstance(res_zero_acres, CropPlan)
    assert len(res_zero_acres.top_crops) == 0
    assert "Invalid land size" in res_zero_acres.reasoning

    res_neg_acres = crop_advisor_fn("Multan", "loamy", "Rabi", "canal", -5.0)
    assert isinstance(res_neg_acres, CropPlan)
    assert len(res_neg_acres.top_crops) == 0
    assert "Invalid land size" in res_neg_acres.reasoning

    # Validation: invalid season
    res_inv_season = crop_advisor_fn("Multan", "loamy", "Spring", "canal", 5.0)
    assert isinstance(res_inv_season, CropPlan)
    assert len(res_inv_season.top_crops) == 0
    assert "Invalid season" in res_inv_season.reasoning

    print("[+] Tool 1 (crop_advisor) passed all tests!")


def test_tool_fertilizer_calculator():
    print("[-] Testing Tool 2: fertilizer_calculator...")
    # Normal case - Wheat 5 acres
    res = fertilizer_calculator_fn("wheat", 5.0)
    assert isinstance(res, FertilizerPlan)
    assert res.urea_bags == 10.0  # 2 bags/acre * 5
    assert res.dap_bags == 5.0    # 1 bag/acre * 5
    assert res.total_cost_pkr == int(10 * 3500 + 5 * 12000)
    assert isinstance(res.total_cost_pkr, int)

    # Normal case - Cotton 10 acres
    res_cotton = fertilizer_calculator_fn("cotton", 10.0)
    assert isinstance(res_cotton, FertilizerPlan)
    assert res_cotton.urea_bags == 30.0  # 3 bags/acre * 10
    assert res_cotton.dap_bags == 15.0   # 1.5 bags/acre * 10
    assert res_cotton.total_cost_pkr > 0

    # Validation: zero or negative acres
    res_zero = fertilizer_calculator_fn("wheat", 0.0)
    assert isinstance(res_zero, FertilizerPlan)
    assert res_zero.urea_bags == 0.0
    assert res_zero.dap_bags == 0.0
    assert res_zero.total_cost_pkr == 0

    res_neg = fertilizer_calculator_fn("wheat", -2.0)
    assert isinstance(res_neg, FertilizerPlan)
    assert res_neg.urea_bags == 0.0
    assert res_neg.total_cost_pkr == 0

    print("[+] Tool 2 (fertilizer_calculator) passed all tests!")


def test_tool_pest_disease_doctor():
    print("[-] Testing Tool 3: pest_disease_doctor...")
    # Normal case - Whitefly on cotton
    res_wf = pest_disease_doctor_fn("safed makhi aur patte peele ho rahe hain", "cotton")
    assert isinstance(res_wf, PestDiagnosis)
    assert "Whitefly" in res_wf.likely_pest_or_disease
    assert res_wf.confidence in ("high", "medium")
    assert res_wf.dosage_ml_per_liter > 0
    assert res_wf.max_safe_dosage_ml_per_liter >= res_wf.dosage_ml_per_liter
    assert isinstance(res_wf.requires_expert_consultation, bool)

    # Normal case - Rust on wheat
    res_rust = pest_disease_doctor_fn("kundi zangar orange powdery spots", "wheat")
    assert isinstance(res_rust, PestDiagnosis)
    assert "Rust" in res_rust.likely_pest_or_disease
    assert res_rust.dosage_ml_per_liter > 0

    # Validation: empty symptoms
    res_empty_sym = pest_disease_doctor_fn("", "wheat")
    assert isinstance(res_empty_sym, PestDiagnosis)
    assert res_empty_sym.confidence == "low"
    assert res_empty_sym.requires_expert_consultation is True

    # Validation: empty both
    res_empty_both = pest_disease_doctor_fn("", "")
    assert isinstance(res_empty_both, PestDiagnosis)
    assert res_empty_both.requires_expert_consultation is True

    print("[+] Tool 3 (pest_disease_doctor) passed all tests!")


def test_tool_irrigation_weather():
    print("[-] Testing Tool 4: irrigation_weather_advisor...")
    # Normal case - Multan wheat CRI stage
    res = irrigation_weather_fn("Multan", "wheat", "CRI pehla pani")
    assert isinstance(res, IrrigationAdvice)
    assert isinstance(res.next_irrigation_in_days, int)
    assert res.next_irrigation_in_days <= 5  # Critical stage
    assert isinstance(res.frost_risk, bool)
    assert isinstance(res.heatwave_risk, bool)
    assert len(res.weather_summary) > 0

    # Normal case - Cotton reproductive stage
    res_cotton = irrigation_weather_fn("Bahawalpur", "cotton", "flowering and boll formation")
    assert isinstance(res_cotton, IrrigationAdvice)
    assert res_cotton.next_irrigation_in_days > 0
    assert res_cotton.heatwave_risk is True

    # Validation: empty inputs
    res_empty = irrigation_weather_fn("", "", "")
    assert isinstance(res_empty, IrrigationAdvice)
    assert res_empty.next_irrigation_in_days > 0

    print("[+] Tool 4 (irrigation_weather_advisor) passed all tests!")


def test_tool_mandi_price_lookup():
    print("[-] Testing Tool 5: mandi_price_lookup...")
    # Normal case - Wheat in Multan
    res = mandi_price_lookup_fn("wheat", "Multan")
    assert isinstance(res, MandiPriceInfo)
    assert res.commodity.lower() == "wheat"
    assert "Multan" in res.mandi_name or "Mandi" in res.mandi_name
    assert res.price_per_maund_pkr > 3000.0
    assert len(res.price_date) > 0
    assert len(res.recommendation) > 0

    # Normal case - Cotton in Bahawalpur
    res_cotton = mandi_price_lookup_fn("cotton", "Bahawalpur")
    assert isinstance(res_cotton, MandiPriceInfo)
    assert res_cotton.price_per_maund_pkr >= 7000.0

    # Validation: empty inputs
    res_empty = mandi_price_lookup_fn("", "")
    assert isinstance(res_empty, MandiPriceInfo)
    assert res_empty.price_per_maund_pkr > 0

    print("[+] Tool 5 (mandi_price_lookup) passed all tests!")


def test_tool_profit_estimator():
    print("[-] Testing Tool 6: profit_estimator...")
    # Normal case - Wheat 5 acres with 300,000 input cost
    res = profit_estimator_fn("wheat", 5.0, 300000.0)
    assert isinstance(res, ProfitEstimate)
    assert res.total_input_cost_pkr == 300000.0
    assert res.expected_revenue_pkr > 0
    assert res.net_margin_pkr == res.expected_revenue_pkr - res.total_input_cost_pkr
    assert res.break_even_yield_kg_per_acre > 0

    # Validation: zero or negative acres
    res_zero = profit_estimator_fn("wheat", 0.0, 100000.0)
    assert isinstance(res_zero, ProfitEstimate)
    assert res_zero.expected_revenue_pkr == 0.0
    assert res_zero.break_even_yield_kg_per_acre == 0.0

    res_neg = profit_estimator_fn("wheat", -5.0, 100000.0)
    assert isinstance(res_neg, ProfitEstimate)
    assert res_neg.expected_revenue_pkr == 0.0

    # Auto-cost estimation when input_costs_pkr <= 0
    res_autocost = profit_estimator_fn("cotton", 2.0, 0.0)
    assert isinstance(res_autocost, ProfitEstimate)
    assert res_autocost.total_input_cost_pkr > 0
    assert res_autocost.expected_revenue_pkr > 0

    print("[+] Tool 6 (profit_estimator) passed all tests!")


def test_tool_govt_support_finder():
    print("[-] Testing Tool 7: govt_support_finder...")
    # Normal case - Punjab subsidy
    res = govt_support_finder_fn("Punjab", "subsidy")
    assert isinstance(res, GovtSupportInfo)
    assert len(res.applicable_schemes) > 0
    first_scheme = res.applicable_schemes[0]
    assert isinstance(first_scheme, SchemeInfo)
    assert len(first_scheme.scheme_name) > 0
    assert len(first_scheme.eligibility) > 0
    assert len(first_scheme.how_to_apply) > 0
    assert any("Kissan Card" in s.scheme_name for s in res.applicable_schemes)

    # Normal case - Federal or loan
    res_loan = govt_support_finder_fn("all", "loan")
    assert isinstance(res_loan, GovtSupportInfo)
    assert len(res_loan.applicable_schemes) > 0

    # Validation: empty or unknown inputs
    res_unknown = govt_support_finder_fn("UnknownProvince", "xyz")
    assert isinstance(res_unknown, GovtSupportInfo)
    assert len(res_unknown.applicable_schemes) > 0

    print("[+] Tool 7 (govt_support_finder) passed all tests!")


def test_all_13_schemas_instantiation():
    print("[-] Testing all 13 Pydantic models existence & instantiation...")
    c_plan = CropPlan(
        top_crops=[CropRecommendation(crop_name="Wheat", expected_yield_kg_per_acre=1600, expected_profit_pkr_per_acre=90000, water_requirement="medium", notes="Good")],
        season="Rabi",
        reasoning="Suitable",
    )
    p_diag = PestDiagnosis(likely_pest_or_disease="Whitefly", confidence="high", treatment="Spray", dosage_ml_per_liter=2.5, max_safe_dosage_ml_per_liter=4.0, requires_expert_consultation=False)
    f_plan = FertilizerPlan(urea_bags=2.0, dap_bags=1.0, total_cost_pkr=19000)
    m_info = MandiPriceInfo(commodity="Wheat", mandi_name="Multan", price_per_maund_pkr=3950.0, price_date="2026-03-01", recommendation="Hold")
    i_adv = IrrigationAdvice(next_irrigation_in_days=5, weather_summary="Sunny", frost_risk=False, heatwave_risk=False)
    p_est = ProfitEstimate(total_input_cost_pkr=100000, expected_revenue_pkr=160000, net_margin_pkr=60000, break_even_yield_kg_per_acre=1000)
    g_info = GovtSupportInfo(applicable_schemes=[SchemeInfo(scheme_name="Kissan Card", eligibility="12.5 acres", how_to_apply="8070 SMS")])

    # Later models
    s_rec = SeedVarietyRecommendation(crop="Wheat", recommended_varieties=["Akbar-2019"], region_notes="Punjab")
    l_mach = LabourMachineryCost(land_prep_cost_pkr=6500, sowing_cost_pkr=2000, harvesting_cost_pkr=6000, total_cost_pkr=14500)
    i_cost = IrrigationCostEstimate(source="Diesel", cost_per_irrigation_pkr=3500, irrigations_needed=5, total_water_cost_pkr=17500)
    l_emi = LoanEmiPlan(loan_amount_pkr=150000, tenure_months=6, interest_rate_percent=0.0, monthly_installment_pkr=25000)
    st_adv = StorageAdvice(recommended_practice="Dry <11% moisture", estimated_shelf_life_days=365)
    rot_adv = RotationAdvice(last_crop="Cotton", recommended_next_crop="Wheat", reasoning="Breaks pest cycle")

    print("[+] All 13 Pydantic models instantiated cleanly!")


if __name__ == "__main__":
    print("=" * 60)
    print("KISAN DOST — PART 2 CORE TOOLS & SCHEMAS TEST SUITE")
    print("=" * 60)
    test_all_13_schemas_instantiation()
    test_tool_crop_advisor()
    test_tool_fertilizer_calculator()
    test_tool_pest_disease_doctor()
    test_tool_irrigation_weather()
    test_tool_mandi_price_lookup()
    test_tool_profit_estimator()
    test_tool_govt_support_finder()
    print("=" * 60)
    print("ALL 7 CORE TOOLS & 13 SCHEMAS PASSED SUCCESSFULLY!")
    print("=" * 60)
