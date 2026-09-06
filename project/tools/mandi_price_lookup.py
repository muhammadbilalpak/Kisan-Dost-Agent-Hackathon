"""
Kisan Dost — Mandi Price Lookup Tool
=======================================
Returns wholesale prices from nearby grain markets (mandis).
Returns typed MandiPriceInfo Pydantic model.
Validates inputs and references data/mandi_prices_sample.csv.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime

from agents import function_tool
from models.schemas import MandiPriceInfo

SAMPLE_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mandi_prices_sample.csv")

# Built-in fallback database in case CSV is missing or item not listed
FALLBACK_PRICES = {
    "wheat": {"mandi": "Ghalla Mandi Multan", "rate": 3950.0, "rec": "Support price is ~PKR 4,000. Sell in phases or store in dry aeration for post-harvest surge."},
    "gandum": {"mandi": "Ghalla Mandi Multan", "rate": 3950.0, "rec": "Support price is ~PKR 4,000. Sell in phases or store in dry aeration for post-harvest surge."},
    "cotton": {"mandi": "Multan Phutti Mandi", "rate": 8650.0, "rec": "Current rates are attractive. Check moisture levels (<8%) before taking harvest to mandi."},
    "kapas": {"mandi": "Multan Phutti Mandi", "rate": 8650.0, "rec": "Current rates are attractive. Check moisture levels (<8%) before taking harvest to mandi."},
    "rice": {"mandi": "Gujranwala Grain Market", "rate": 5100.0, "rec": "Basmati demand is steady. Premium offered for low-broken kernel lots."},
    "chawal": {"mandi": "Gujranwala Grain Market", "rate": 5100.0, "rec": "Basmati demand is steady. Premium offered for low-broken kernel lots."},
    "maize": {"mandi": "Sahiwal Mandi", "rate": 2500.0, "rec": "Feed mill procurement active. Ensure moisture is below 14% to avoid deductions."},
    "makki": {"mandi": "Sahiwal Mandi", "rate": 2500.0, "rec": "Feed mill procurement active. Ensure moisture is below 14% to avoid deductions."},
    "sugarcane": {"mandi": "Rahim Yar Khan Mill Gate", "rate": 440.0, "rec": "Deliver promptly to sugar mills with official CPR receipts to secure government floor price."},
    "ganna": {"mandi": "Rahim Yar Khan Mill Gate", "rate": 440.0, "rec": "Deliver promptly to sugar mills with official CPR receipts to secure government floor price."},
    "mustard": {"mandi": "Khanewal Mandi", "rate": 6100.0, "rec": "Oil mill demand strong. High oil content fetches premium."},
    "sarson": {"mandi": "Khanewal Mandi", "rate": 6100.0, "rec": "Oil mill demand strong. High oil content fetches premium."},
    "gram": {"mandi": "Bhakkar Mandi", "rate": 6500.0, "rec": "Dal mills buying steadily. Safe storage recommended to avoid pulse beetle damage."},
    "chana": {"mandi": "Bhakkar Mandi", "rate": 6500.0, "rec": "Dal mills buying steadily. Safe storage recommended to avoid pulse beetle damage."},
}


@function_tool
def mandi_price_lookup(commodity: str, district: str) -> MandiPriceInfo:
    """Lookup mandi wholesale rates for a commodity in a district.

    Args:
        commodity: Agricultural commodity name (e.g. 'Wheat', 'Cotton', 'Rice').
        district: Farmer's district to search nearby grain markets.
    """
    # ── Validation ──
    comm_clean = commodity.strip().lower() if commodity else "wheat"
    dist_clean = district.strip().title() if district else "Multan"
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Attempt lookup in sample CSV first
    matched_row = None
    if os.path.exists(SAMPLE_CSV_PATH):
        try:
            with open(SAMPLE_CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c_name = row.get("commodity", "").lower()
                    d_name = row.get("district", "").lower()
                    if comm_clean in c_name:
                        matched_row = row
                        if dist_clean.lower() in d_name:
                            break  # exact district match found
        except Exception:
            pass

    if matched_row:
        rate = float(matched_row.get("modal_price_pkr_per_maund", 4000.0))
        mandi = matched_row.get("mandi", f"{dist_clean} Mandi")
        date_val = matched_row.get("arrival_date", today_str)
        rec = f"Modal wholesale rate in {matched_row.get('district', dist_clean)}. Clean and grade produce for top market rate."
        return MandiPriceInfo(
            commodity=matched_row.get("commodity", comm_clean.title()),
            mandi_name=mandi,
            price_per_maund_pkr=rate,
            price_date=date_val,
            recommendation=rec,
        )

    # Fallback lookup
    for key, data in FALLBACK_PRICES.items():
        if key in comm_clean:
            return MandiPriceInfo(
                commodity=comm_clean.title(),
                mandi_name=f"{dist_clean} / {data['mandi']}",
                price_per_maund_pkr=data["rate"],
                price_date=today_str,
                recommendation=data["rec"],
            )

    # Default general fallback
    return MandiPriceInfo(
        commodity=comm_clean.title(),
        mandi_name=f"{dist_clean} Grain Market",
        price_per_maund_pkr=3800.0,
        price_date=today_str,
        recommendation=f"Current market rate for {comm_clean.title()} in {dist_clean}. Check with local commission agent (Aarthi) before dispatch.",
    )
