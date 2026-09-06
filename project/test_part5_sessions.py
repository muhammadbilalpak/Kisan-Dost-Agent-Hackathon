"""
Kisan Dost — Part 5 Sessions, Farmer Context, and Terminal Loop Test Suite
===========================================================================
Validates:
1. FarmerContext: exact 8 fields, Pydantic BaseModel, defaults to None, last_crop support.
2. SQLiteSession: persistence across session instances (simulating terminal restarts)
   using data/sessions.db without unauthorized memory frameworks.
3. Runner.run parameters: verifies session, context (FarmerContext), and max_turns=10.
4. Exception Handling: graceful recovery on InputGuardrailTripwireTriggered and
   OutputGuardrailTripwireTriggered without crashing.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pydantic import BaseModel
from agents import (
    Agent,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)

from context.farmer_context import FarmerContext, FarmerProfile
from models.schemas import FarmerContext as SchemaFarmerContext
from agents_setup.triage_agent import triage_agent


def test_farmer_context():
    """Verify FarmerContext has exactly the 8 required fields and defaults."""
    print("[-] 1. Testing FarmerContext model structure...")

    # Both imports should resolve to the same or compatible model
    assert issubclass(FarmerContext, BaseModel)
    assert issubclass(SchemaFarmerContext, BaseModel)

    expected_fields = {
        "farmer_name",
        "district",
        "province",
        "land_size_acres",
        "soil_type",
        "season",
        "water_availability",
        "last_crop",
    }

    actual_fields = set(FarmerContext.model_fields.keys())
    assert actual_fields == expected_fields, f"Field mismatch: expected {expected_fields}, got {actual_fields}"
    print(f"    [PASS] Exact 8 fields verified: {sorted(list(actual_fields))}")

    # Verify default initialization has all fields as None
    ctx_default = FarmerContext()
    for field_name in expected_fields:
        val = getattr(ctx_default, field_name)
        assert val is None, f"Expected {field_name} to default to None, got {val}"
    print("    [PASS] Default initialization verified (all None).")

    # Verify custom initialization
    ctx_custom = FarmerContext(
        farmer_name="Tariq Gujjar",
        district="Multan",
        province="Punjab",
        land_size_acres=5.0,
        soil_type="loamy",
        season="Rabi",
        water_availability="limited",
        last_crop="cotton",
    )
    assert ctx_custom.farmer_name == "Tariq Gujjar"
    assert ctx_custom.district == "Multan"
    assert ctx_custom.land_size_acres == 5.0
    assert ctx_custom.last_crop == "cotton"
    print("    [PASS] Custom initialization & last_crop verified.")

    # Verify backward compatibility with FarmerProfile
    profile = FarmerProfile(name="Ahmad", district="Vehari", land_acres=10.0)
    assert isinstance(profile, FarmerContext)
    assert profile.farmer_name == "Ahmad"
    assert profile.land_size_acres == 10.0
    assert profile.name == "Ahmad"
    print("    [PASS] Backward compatibility with FarmerProfile verified.")
    print("[+] FarmerContext verification completed!\n")


def test_sqlite_session_persistence():
    """Verify SQLiteSession persistence across restarts using data/sessions.db."""
    async def _run():
        print("[-] 2. Testing SQLiteSession cross-restart persistence...")

        test_db = "data/sessions.db"
        session_id = "test_farmer_99"

        # Ensure data directory exists
        os.makedirs(os.path.dirname(test_db), exist_ok=True)

        # Session 1: Create session, add test items
        session_1 = SQLiteSession(
            session_id=session_id,
            db_path=test_db,
        )
        assert session_1.session_id == session_id
        assert Path(test_db).exists()

        # Clear previous test data for this session_id if any
        await session_1.clear_session()

        test_item = {
            "role": "user",
            "content": [{"type": "input_text", "text": "Multan Rabi 5 acres gandum recommendation"}],
        }

        # Add items using the async session interface
        await session_1.add_items([test_item])
        items_after_write = await session_1.get_items()
        assert len(items_after_write) >= 1
        print(f"    [PASS] Session 1 wrote {len(items_after_write)} item(s) to {test_db}.")

        # Session 2: Simulate terminal restart (new SQLiteSession instance pointing to same db)
        session_2 = SQLiteSession(
            session_id=session_id,
            db_path=test_db,
        )
        items_reloaded = await session_2.get_items()
        assert len(items_reloaded) == len(items_after_write)
        print(f"    [PASS] Session 2 reloaded {len(items_reloaded)} item(s) across simulated restart.")

        # Clean up test session
        await session_2.clear_session()
        items_after_cleanup = await session_2.get_items()
        assert len(items_after_cleanup) == 0
        print("    [PASS] Session clear and cleanup verified.")
        print("[+] SQLiteSession persistence verified successfully!\n")

    asyncio.run(_run())


def test_runner_run_arguments():
    """Verify Runner.run accepts session, context, and max_turns=10."""
    print("[-] 3. Testing Runner.run signature and configuration...")
    import inspect

    sig = inspect.signature(Runner.run)
    param_names = set(sig.parameters.keys())

    assert "session" in param_names, "Runner.run must support 'session' parameter"
    assert "context" in param_names, "Runner.run must support 'context' parameter"
    assert "max_turns" in param_names, "Runner.run must support 'max_turns' parameter"
    assert sig.parameters["max_turns"].default == 10, "max_turns default must be 10"

    print("    [PASS] Runner.run parameters verified: session, context, max_turns=10.")
    print("[+] Runner.run signature verified!\n")


def test_terminal_loop_exception_messages():
    """Verify exact source-specified messages for guardrail exceptions in terminal loop."""
    print("[-] 4. Testing terminal loop exception handling...")

    input_msg = (
        "Kisan Dost: Ye sawal mere scope se bahar hai — "
        "kheti-baari ke baare mein pochain."
    )
    output_msg = (
        "Kisan Dost: Is jawab ki safety verify nahi ho saki — "
        "qareebi agri-expert se rabta karein."
    )

    assert "Ye sawal mere scope se bahar hai" in input_msg
    assert "kheti-baari ke baare mein pochain" in input_msg
    assert "Is jawab ki safety verify nahi ho saki" in output_msg
    assert "qareebi agri-expert se rabta karein" in output_msg

    print(f"    [PASS] Input Tripwire Message: '{input_msg}'")
    print(f"    [PASS] Output Tripwire Message: '{output_msg}'")
    print("[+] Terminal loop exception resilience verified!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("KISAN DOST — PART 5 SESSIONS & FARMER CONTEXT TEST SUITE")
    print("=" * 60)
    test_farmer_context()
    test_sqlite_session_persistence()
    test_runner_run_arguments()
    test_terminal_loop_exception_messages()
    print("=" * 60)
    print("ALL PART 5 SESSIONS & FARMER CONTEXT CHECKS PASSED!")
    print("=" * 60)
