"""
Kisan Dost — Government Support Finder Tool
==============================================
Finds applicable government agriculture schemes, subsidies, and loans.
Returns typed GovtSupportInfo Pydantic model with list[SchemeInfo].
References agripunjab.gov.pk and federal/provincial scheme datasets.
"""

from __future__ import annotations

import csv
import os

from agents import function_tool
from models.schemas import GovtSupportInfo, SchemeInfo

SCHEMES_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "govt_schemes.csv")

# Baseline schemes database
BUILTIN_SCHEMES = [
    {
        "scheme_name": "CM Punjab Kissan Card (agripunjab.gov.pk)",
        "province": "punjab",
        "category": ["subsidy", "loan", "kisan card", "fertilizer", "seed"],
        "eligibility": "Farmers holding up to 12.5 acres agricultural land with biometric CNIC verification.",
        "how_to_apply": "Send CNIC to 8070 via SMS or visit nearest Agriculture Extension Office / HBL Konnect shop.",
    },
    {
        "scheme_name": "Punjab Solar Tubewell Subsidy Scheme",
        "province": "punjab",
        "category": ["solar", "tubewell", "irrigation", "subsidy", "water"],
        "eligibility": "Owners of verified tubewells with land up to 25 acres in canal command or barani areas.",
        "how_to_apply": "Apply online at agripunjab.gov.pk portal or submit form to District Water Management Officer.",
    },
    {
        "scheme_name": "Punjab Green Tractor Scheme",
        "province": "punjab",
        "category": ["tractor", "machinery", "subsidy"],
        "eligibility": "Small farmers in Punjab cultivating 1 to 12.5 acres.",
        "how_to_apply": "Apply online via Punjab Agriculture Department portal; balloting based allocation.",
    },
    {
        "scheme_name": "Prime Minister Kissan Package",
        "province": "all",
        "category": ["subsidy", "fertilizer", "loan", "relief"],
        "eligibility": "Smallholders registered in National Land Record / Ehsaas database.",
        "how_to_apply": "Visit participating commercial banks (ZTBL, NBP, HBL, Bank of Punjab) branches.",
    },
    {
        "scheme_name": "ZTBL Asan Qarza Agri Production Loan",
        "province": "all",
        "category": ["loan", "credit", "production", "seeds"],
        "eligibility": "All Pakistani farmers possessing passbook or land ownership fard.",
        "how_to_apply": "Visit nearest Zarai Taraqiati Bank Limited (ZTBL) branch with CNIC and land title documents.",
    },
    {
        "scheme_name": "Sindh Hari Card Scheme",
        "province": "sindh",
        "category": ["subsidy", "kisan card", "hari", "cash"],
        "eligibility": "Small farmers (haris) holding up to 16 acres registered with Sindh Agriculture Department.",
        "how_to_apply": "Register at Union Council Hari Facilitation Desks or District Agriculture Office.",
    },
    {
        "scheme_name": "Khyber Pakhtunkhwa Kisan Card",
        "province": "kpk",
        "category": ["subsidy", "kisan card", "seed", "fertilizer"],
        "eligibility": "Farmers in KP registered on the provincial e-agri portal.",
        "how_to_apply": "Register on KP E-Agri portal or visit Tehsil Agriculture Extension Office.",
    },
    {
        "scheme_name": "Balochistan Tubewell Solarization Program",
        "province": "balochistan",
        "category": ["solar", "tubewell", "subsidy", "electricity"],
        "eligibility": "Registered agricultural tubewell power consumers in Balochistan.",
        "how_to_apply": "Apply via QESCO / Balochistan Energy Department tubewell conversion desks.",
    },
]


@function_tool
def govt_support_finder(province: str, need: str) -> GovtSupportInfo:
    """Find applicable government support schemes by province and farmer need.

    Args:
        province: Province name (e.g. 'Punjab', 'Sindh', 'KPK', 'Balochistan', or 'Federal'/'all').
        need: Farmer need or category (e.g. 'subsidy', 'loan', 'kisan card', 'solar', 'tractor').
    """
    # ── Validation ──
    prov_clean = province.strip().lower() if province else "all"
    need_clean = need.strip().lower() if need else "all"

    # Normalize province names
    prov_norm = {
        "punjab": "punjab",
        "sindh": "sindh",
        "kpk": "kpk",
        "khyber pakhtunkhwa": "kpk",
        "balochistan": "balochistan",
        "baluchistan": "balochistan",
        "federal": "all",
        "pakistan": "all",
        "all": "all",
        "": "all",
    }.get(prov_clean, "all")

    matched_schemes: list[SchemeInfo] = []

    # 1. Try reading from CSV
    csv_loaded = False
    if os.path.exists(SCHEMES_CSV_PATH):
        try:
            with open(SCHEMES_CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    p = row.get("province", "").lower()
                    cat = row.get("category", "").lower()

                    prov_ok = (prov_norm == "all") or (p in ("all", "federal", prov_norm))
                    need_ok = (need_clean in ("all", "any", "subsidy", "")) or (need_clean in cat)

                    if prov_ok and need_ok:
                        scheme = SchemeInfo(
                            scheme_name=row.get("title", "Agri Support Scheme"),
                            eligibility=row.get("eligibility", "Verified farmer with CNIC"),
                            how_to_apply=row.get("how_to_apply", "Visit nearest Agriculture Department office"),
                        )
                        matched_schemes.append(scheme)
                csv_loaded = len(matched_schemes) > 0
        except Exception:
            pass

    # 2. Fallback to builtin database if CSV yielded no results
    if not csv_loaded:
        for item in BUILTIN_SCHEMES:
            p = item["province"]
            prov_ok = (prov_norm == "all") or (p in ("all", prov_norm))
            need_ok = (need_clean in ("all", "any", "")) or any(need_clean in c for c in item["category"])

            if prov_ok and need_ok:
                matched_schemes.append(
                    SchemeInfo(
                        scheme_name=item["scheme_name"],
                        eligibility=item["eligibility"],
                        how_to_apply=item["how_to_apply"],
                    )
                )

    # 3. If still empty, return general federal/extension guidance
    if not matched_schemes:
        matched_schemes.append(
            SchemeInfo(
                scheme_name="General Agriculture Extension & ZTBL Credit",
                eligibility="All Pakistani farmers with valid CNIC and land records.",
                how_to_apply="Visit your local District Agriculture Extension Office or nearest ZTBL branch for active seasonal schemes.",
            )
        )

    return GovtSupportInfo(applicable_schemes=matched_schemes)
