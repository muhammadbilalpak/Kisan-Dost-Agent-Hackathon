"""
Kisan Dost — Agri Loan & EMI Calculator (Extra Tool)
===================================================
Calculates interest/markup and repayment schedules for agricultural loans.
Returns typed LoanEmiPlan model.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import LoanEmiPlan


@function_tool
def loan_emi_calculator(
    loan_amount_pkr: float,
    tenure_months: int = 6,
    interest_rate_percent: float = 0.0,
) -> LoanEmiPlan:
    """Calculate repayments for agricultural production or machinery loans.

    Args:
        loan_amount_pkr: Total loan requested in PKR (e.g., 150000 for Kissan Card).
        tenure_months: Duration of loan in months (typical crop loan is 6 months).
        interest_rate_percent: Annual markup rate (0% for CM Punjab Kissan Card).
    """
    principal = max(1000.0, float(loan_amount_pkr))
    months = max(1, int(tenure_months))
    rate = max(0.0, float(interest_rate_percent))

    total_interest = principal * (rate / 100.0) * (months / 12.0)
    total_payable = principal + total_interest
    monthly_installment = total_payable / months

    return LoanEmiPlan(
        loan_amount_pkr=round(principal, 2),
        tenure_months=months,
        interest_rate_percent=round(rate, 2),
        monthly_installment_pkr=round(monthly_installment, 2),
    )
