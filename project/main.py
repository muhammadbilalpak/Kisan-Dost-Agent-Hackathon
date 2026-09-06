"""
Kisan Dost (کسان دوست) — Terminal-Based AI Agronomy Assistant
==============================================================
Main Entry Point & Interactive Terminal Loop.
Uses SQLiteSession for persistent cross-restart conversation memory,
FarmerContext for typed farmer profile context, and max_turns=10.

Supports stretch UX options:
- Default terminal loop
- --whatsapp: WhatsApp-style formatted terminal chat flow
- --urdu: Urdu language output preference
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Step 1: Load environment variables
load_dotenv()

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)

from agents_setup import setup_llm_provider, triage_agent
from context.farmer_context import FarmerContext


async def main() -> None:
    parser = argparse.ArgumentParser(description="Kisan Dost Interactive Terminal Loop")
    parser.add_argument(
        "--whatsapp",
        action="store_true",
        help="Enable WhatsApp-style formatted chat UI in the terminal.",
    )
    parser.add_argument(
        "--urdu",
        action="store_true",
        help="Request agent answers in Urdu script (اردو).",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default="farmer_1",
        help="Session ID for SQLiteSession persistence (default: 'farmer_1').",
    )
    args, _ = parser.parse_known_args()

    # Configure LLM provider (OpenAI / Groq / Gemini fallback)
    setup_llm_provider()

    farmer_ctx = FarmerContext()
    session = SQLiteSession(
        session_id=args.session_id,
        db_path="data/sessions.db",
    )

    if args.whatsapp:
        print("╔" + "═" * 62 + "╗")
        print("║          KISAN DOST (کسان دوست) — WHATSAPP CHAT FLOW         ║")
        print("║  🟢 Online • Type 'exit' to quit • SQLite Persistent Session ║")
        print("╚" + "═" * 62 + "╝\n")
    else:
        print("Assalam-o-Alaikum! Main Kisan Dost hoon. (type 'exit' to quit)")

    while True:
        timestamp = datetime.datetime.now().strftime("%I:%M %p")
        prompt_label = f"[{timestamp}] 👨‍🌾 Aap: " if args.whatsapp else "Aap: "

        try:
            user_input = input(prompt_label).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nKhuda Hafiz!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            break

        # Append Urdu preference instruction if requested
        query_to_run = user_input
        if args.urdu:
            query_to_run = f"{user_input}\n[Note: Please reply in Urdu script (اردو).]"

        agent_label = f"[{timestamp}] 🤖 Kisan Dost: " if args.whatsapp else "Kisan Dost: "

        try:
            result = await Runner.run(
                triage_agent,
                query_to_run,
                session=session,
                context=farmer_ctx,
                max_turns=10,
            )
            print(f"{agent_label}{result.final_output}\n")

        except InputGuardrailTripwireTriggered:
            print(
                f"{agent_label}Ye sawal mere scope se bahar hai — "
                "kheti-baari ke baare mein pochain.\n"
            )

        except OutputGuardrailTripwireTriggered:
            print(
                f"{agent_label}Is jawab ki safety verify nahi ho saki — "
                "qareebi agri-expert se rabta karein.\n"
            )

        except Exception as e:
            print(f"{agent_label}Error - {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
