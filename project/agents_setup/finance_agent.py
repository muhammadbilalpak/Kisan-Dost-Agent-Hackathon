"""
Kisan Dost — Finance Agent
===========================
Specialist agent for:
- Profit Estimator (seasonal crop budgets & break-even analysis)
- Govt Support Finder (subsidies, Kisan Card, and agri-loans)
- [Extra] Labour & Machinery Cost Estimator (tractor/harvester rental + daily wage)
- [Extra] Loan EMI Calculator (installment calculation for agri-loans)
"""

from __future__ import annotations

from typing import Union

from agents import Agent
from models.schemas import (
    GovtSupportInfo,
    LabourMachineryCost,
    LoanEmiPlan,
    ProfitEstimate,
)
from tools.govt_support_finder import govt_support_finder
from tools.profit_estimator import profit_estimator
from tools.extra.labour_machinery_cost import labour_machinery_cost
from tools.extra.loan_emi_calculator import loan_emi_calculator

FINANCE_INSTRUCTIONS = """You are the Finance Agent for Kisan Dost, serving Pakistani farmers.
Your job is to optimize farm economics, evaluate crop profitability, and guide farmers to government subsidies.

CORE TOOLS:
- Use `profit_estimator` to calculate expected revenue, net margin, and break-even yield in kg/acre.
- Use `govt_support_finder` to find applicable provincial and federal government schemes (Punjab Kissan Card, Solar Tubewell, Green Tractor, ZTBL loans).

EXTRA TOOLS:
- Use `labour_machinery_cost` to estimate tractor machinery operations and agricultural labor costs.
- Use `loan_emi_calculator` to calculate repayment schedules for agricultural production or machinery loans.

Always return structured Pydantic output using the corresponding model.
"""

finance_agent = Agent(
    name="Finance Agent",
    handoff_description="Fasal ka kharcha, munafa andaza (profit estimate), sarkari subsidy (Kissan Card, Solar), ya bank loan ke liye.",
    instructions=FINANCE_INSTRUCTIONS,
    tools=[
        profit_estimator,
        govt_support_finder,
        labour_machinery_cost,
        loan_emi_calculator,
    ],
    output_type=Union[ProfitEstimate, GovtSupportInfo, LabourMachineryCost, LoanEmiPlan],
)
