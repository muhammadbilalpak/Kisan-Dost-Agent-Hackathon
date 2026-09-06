"""
Kisan Dost — Agents Setup Package
=================================
Orchestrates Triage and Specialist agents for the multi-agent system.
"""

from agents_setup.provider_config import setup_llm_provider
from agents_setup.triage_agent import triage_agent
from agents_setup.agronomy_agent import agronomy_agent
from agents_setup.pest_doctor_agent import pest_doctor_agent
from agents_setup.market_agent import market_agent
from agents_setup.finance_agent import finance_agent

__all__ = [
    "setup_llm_provider",
    "triage_agent",
    "agronomy_agent",
    "pest_doctor_agent",
    "market_agent",
    "finance_agent",
]
