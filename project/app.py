"""
Kisan Dost (کسان دوست) — Chainlit Web Application
===================================================
Web-based multi-agent agronomy extension system for Pakistani farmers.
Connects the existing OpenAI Agents SDK triage orchestrator, specialist agents,
dual-layer guardrails, and persistent SQLite session to a modern browser UI.
"""

from __future__ import annotations

import os
import sys
from dotenv import load_dotenv

# Ensure environment is loaded first
load_dotenv()

import chainlit as cl

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)
from agents_setup import setup_llm_provider, triage_agent
from context.farmer_context import FarmerContext
from models.schemas import (
    CropPlan,
    PestDiagnosis,
    MandiPriceInfo,
    FertilizerPlan,
    IrrigationAdvice,
    ProfitEstimate,
    GovtSupportInfo,
    SeedVarietyRecommendation,
    RotationAdvice,
    IrrigationCostEstimate,
    LabourMachineryCost,
    LoanEmiPlan,
    StorageAdvice,
)

# Initialize LLM provider on server launch
setup_llm_provider()


def format_agent_output(output: object) -> str:
    """Formats structured Pydantic models or strings into clean, readable Markdown."""
    if isinstance(output, str):
        return output

    if isinstance(output, CropPlan):
        lines = [
            "### 🌾 Fasal Ki Sifarish (Crop Plan)",
            f"**Season:** {output.season} | **Reasoning:** {output.reasoning}\n",
            "| # | Crop | Expected Yield | Profit / Acre | Water Need | Special Notes |",
            "|---|---|---|---|---|---|",
        ]
        for idx, crop in enumerate(output.top_crops, 1):
            lines.append(
                f"| {idx} | **{crop.crop_name}** | {crop.expected_yield_kg_per_acre:,.0f} kg/acre "
                f"| PKR {crop.expected_profit_pkr_per_acre:,.0f} | `{crop.water_requirement}` "
                f"| {crop.notes} |"
            )
        return "\n".join(lines)

    if isinstance(output, PestDiagnosis):
        expert_tag = "⚠️ **Consult Local Extension Officer**" if output.requires_expert_consultation else "✅ Routine Farm Management"
        return (
            f"### 🐛 Fasal Ke Keere / Beemari Ki Tashkhees\n\n"
            f"- **Likely Pest / Disease:** **{output.likely_pest_or_disease}**\n"
            f"- **Confidence:** `{output.confidence.upper()}`\n"
            f"- **Recommended Treatment:** {output.treatment}\n"
            f"- **Safe Dosage:** **{output.dosage_ml_per_liter} ml/L** (Certified Safety Cap: `{output.max_safe_dosage_ml_per_liter} ml/L`)\n"
            f"- **Expert Consultation:** {expert_tag}"
        )

    if isinstance(output, MandiPriceInfo):
        return (
            f"### 📊 Mandi Wholesale Rates\n\n"
            f"- **Commodity:** **{output.commodity}**\n"
            f"- **Mandi / Benchmark:** {output.mandi_name}\n"
            f"- **Rate:** **PKR {output.price_per_maund_pkr:,.0f} per maund (40 kg)**\n"
            f"- **Benchmark Date:** {output.price_date}\n"
            f"- **Market Advice:** {output.recommendation}"
        )

    if isinstance(output, FertilizerPlan):
        lines = [
            f"### 🌱 Fertilizer Application Plan ({output.crop})",
            f"- **Land Area:** {output.land_size_acres} acres",
            f"- **Urea Bags Needed:** {output.urea_bags_needed} bags",
            f"- **DAP Bags Needed:** {output.dap_bags_needed} bags",
            f"- **Potash Bags Needed:** {output.potash_bags_needed} bags",
            f"- **Estimated Total Cost:** **PKR {output.estimated_total_cost_pkr:,.0f}**\n",
            "**Application Schedule:**",
        ]
        for stage, rec in output.application_schedule.items():
            lines.append(f"- **{stage.title()}:** {rec}")
        return "\n".join(lines)

    if isinstance(output, IrrigationAdvice):
        return (
            f"### 💧 Irrigation & Weather Guidance\n\n"
            f"- **Crop:** {output.crop} | **District:** {output.district}\n"
            f"- **Water Source:** {output.water_source}\n"
            f"- **Next Irrigation Needed:** In **{output.next_irrigation_days} days**\n"
            f"- **Weather Summary:** {output.weather_summary}\n"
            f"- **Frost Risk Alert:** {'🚨 YES' if output.frost_risk else 'None'}\n"
            f"- **Heatwave Risk Alert:** {'🚨 YES' if output.heatwave_risk else 'None'}"
        )

    if isinstance(output, ProfitEstimate):
        lines = [
            f"### 💰 Enterprise Crop Budget ({output.crop})",
            f"- **Acreage:** {output.land_size_acres} acres",
            f"- **Gross Revenue:** PKR {output.gross_revenue_pkr:,.0f}",
            f"- **Total Production Cost:** PKR {output.total_cost_pkr:,.0f}",
            f"- **Net Expected Profit:** **PKR {output.net_profit_pkr:,.0f}**",
            f"- **Break-Even Yield:** {output.break_even_yield_maund_per_acre:.1f} maund/acre\n",
            "**Cost Breakdown per Acre:**",
        ]
        for item, cost in output.cost_breakdown.items():
            lines.append(f"- {item.title()}: PKR {cost:,.0f}")
        return "\n".join(lines)

    if isinstance(output, GovtSupportInfo):
        lines = [
            f"### 🏛️ Government Agricultural Subsidies & Schemes ({output.province})",
            f"Matching farmer profile with {len(output.applicable_schemes)} active scheme(s):\n",
        ]
        for s in output.applicable_schemes:
            lines.append(
                f"- **{s.scheme_name}**\n"
                f"  - Details: {s.details}\n"
                f"  - Eligibility: {s.eligibility}\n"
                f"  - Application: {s.how_to_apply}\n"
            )
        return "\n".join(lines)

    if isinstance(output, SeedVarietyRecommendation):
        return (
            f"### 🌾 Approved Seed Cultivars ({output.crop})\n\n"
            f"- **Recommended Varieties:** {', '.join(output.recommended_varieties)}\n"
            f"- **Regional Ecological Notes:** {output.region_notes}"
        )

    if isinstance(output, RotationAdvice):
        return (
            f"### 🔄 Crop Rotation Recommendation\n\n"
            f"- **Previous Season Crop:** {output.last_crop}\n"
            f"- **Recommended Next Crop(s):** {', '.join(output.recommended_next_crop)}\n"
            f"- **Agronomic Rationale:** {output.reasoning}"
        )

    if isinstance(output, IrrigationCostEstimate):
        return (
            f"### ⚡ Irrigation Operational Cost ({output.source.title()})\n\n"
            f"- **Cost per Irrigation:** PKR {output.cost_per_irrigation_pkr:,.0f}\n"
            f"- **Required Irrigations:** {output.irrigations_needed}\n"
            f"- **Total Water Cost:** **PKR {output.total_water_cost_pkr:,.0f}**"
        )

    if isinstance(output, LabourMachineryCost):
        return (
            f"### 🚜 Labour & Machinery Rental Cost\n\n"
            f"- **Land Preparation:** PKR {output.land_prep_cost_pkr:,.0f}\n"
            f"- **Sowing / Seeding:** PKR {output.sowing_cost_pkr:,.0f}\n"
            f"- **Harvesting / Threshing:** PKR {output.harvesting_cost_pkr:,.0f}\n"
            f"- **Total Operations Cost:** **PKR {output.total_cost_pkr:,.0f}**"
        )

    if isinstance(output, LoanEmiPlan):
        return (
            f"### 🏦 Agricultural Loan Installment Plan\n\n"
            f"- **Loan Principal:** PKR {output.loan_amount_pkr:,.0f}\n"
            f"- **Tenure:** {output.tenure_months} months\n"
            f"- **Interest Rate:** {output.interest_rate_percent}%\n"
            f"- **Monthly Installment:** **PKR {output.monthly_installment_pkr:,.0f}**"
        )

    if isinstance(output, StorageAdvice):
        return (
            f"### 📦 Grain Preservation & Post-Harvest Storage\n\n"
            f"- **Recommended Practice:** {output.recommended_practice}\n"
            f"- **Estimated Preservation Life:** **{output.estimated_shelf_life_days} days**"
        )

    # Fallback to string representation
    return str(output)


@cl.on_chat_start
async def on_chat_start():
    """Initializes a farmer session with persistent SQLiteSession and FarmerContext."""
    setup_llm_provider()

    user_id = cl.user_session.get("id") or "web_farmer"
    session = SQLiteSession(
        session_id=f"chainlit_{user_id}",
        db_path="data/sessions.db",
    )
    farmer_ctx = FarmerContext()

    cl.user_session.set("session", session)
    cl.user_session.set("farmer_ctx", farmer_ctx)

    welcome_message = (
        "🌾 **Assalam-o-Alaikum! Main Kisan Dost (کسان دوست) hoon.**\n\n"
        "Main Pakistan ke kissano ke liye aik multi-agent agronomy assistant hoon. "
        "Aap mujhse Urdu ya English mein sawal pooch sakte hain:\n\n"
        "- 🌾 **Fasal ki sifarish:** *“Multan mein Rabi season, 5 acres, limited water — kya lagaun?”*\n"
        "- 🐛 **Keeray aur beemariyan:** *“Cotton ke pattay curl ho rahe hain, chotay safed keeray hain”*\n"
        "- 📊 **Mandi rates:** *“Faisalabad mandi mein gandum ka rate kya hai?”*\n"
        "- 🌱 **Khad ka hisaab:** *“Gandum ke liye Urea aur DAP ka hisaab lagao”*\n"
        "- 💰 **Munafa andaza:** *“5 acre par cotton ka kharcha aur munafa kitna hoga?”*\n"
        "- 🏛️ **Sarkari schemes:** *“Kissan Card ya Solar Tubewell subsidy ki maloomat do”*"
    )
    await cl.Message(content=welcome_message).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Processes incoming user questions through the Triage Agent and specialized agents."""
    farmer_ctx = cl.user_session.get("farmer_ctx")
    if not farmer_ctx:
        farmer_ctx = FarmerContext()
        cl.user_session.set("farmer_ctx", farmer_ctx)

    session = cl.user_session.get("session")
    if not session:
        user_id = cl.user_session.get("id") or "web_farmer"
        session = SQLiteSession(
            session_id=f"chainlit_{user_id}",
            db_path="data/sessions.db",
        )
        cl.user_session.set("session", session)

    user_query = message.content.strip()
    if not user_query:
        return

    # Send initial loading indicator
    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        result = await Runner.run(
            triage_agent,
            user_query,
            session=session,
            context=farmer_ctx,
            max_turns=10,
        )
        formatted_text = format_agent_output(result.final_output)
        response_msg.content = formatted_text
        await response_msg.update()

    except InputGuardrailTripwireTriggered:
        response_msg.content = (
            "⚠️ **Kisan Dost (Guardrail)**: Ye sawal mere scope se bahar hai — "
            "baraye meharbani kheti-baari, fasal, khad, keeray, mandi ya zaraati maliyat ke baare mein pochain."
        )
        await response_msg.update()

    except OutputGuardrailTripwireTriggered:
        response_msg.content = (
            "🛡️ **Kisan Dost (Safety Guardrail)**: Is jawab ki pesticide safety verify nahi ho saki — "
            "qareebi agriculture extension expert se rabta karein."
        )
        await response_msg.update()

    except Exception as exc:
        response_msg.content = f"⚠️ **Kisan Dost Error**: {exc}"
        await response_msg.update()
