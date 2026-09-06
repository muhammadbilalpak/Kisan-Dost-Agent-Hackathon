"""
Kisan Dost — Market Agent
==========================
Specialist agent for:
- Mandi Price Lookup (wholesale rates & selling advice)
- [Extra] Storage & Post-Harvest Advisor (grain storage and shelf-life guidance)
"""

from __future__ import annotations

from typing import Union

from agents import Agent
from models.schemas import MandiPriceInfo, StorageAdvice
from tools.mandi_price_lookup import mandi_price_lookup
from tools.extra.storage_advisor import storage_advisor

MARKET_INSTRUCTIONS = """You are the Market Agent for Kisan Dost, serving Pakistani farmers.
Your job is to provide wholesale commodity rates across Pakistani mandis and practical selling advice.

CORE TOOLS:
- Use `mandi_price_lookup` to check nearby mandi wholesale prices for crops.

EXTRA TOOLS:
- Use `storage_advisor` to advise on post-harvest grain storage, moisture limits, fumigation, and shelf life.

Always output structured Pydantic output using the corresponding model.
Provide practical market tips (e.g. commission agent fees, transportation, storage moisture).
"""

market_agent = Agent(
    name="Market Agent",
    handoff_description="Mandi wholesale rates, fasal ke taaza daam, aur bechne ke mashware ke liye.",
    instructions=MARKET_INSTRUCTIONS,
    tools=[
        mandi_price_lookup,
        storage_advisor,
    ],
    output_type=Union[MandiPriceInfo, StorageAdvice],
)
