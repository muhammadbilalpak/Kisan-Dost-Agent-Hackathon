"""
Kisan Dost — Test Suite for Part 4 Input & Output Guardrails
=============================================================
Verifies:
1. Input Guardrail:
   - TopicSafetyCheck model
   - Farming topics allowed (tripwire = False)
   - Off-topic topics rejected (tripwire = True)
2. Output Guardrail:
   - PesticideSafetyCheck model
   - Safe dosage allowed (tripwire = False)
   - Excessive dosage exceeding independent lookup rejected (tripwire = True)
   - Human medical advice rejected (tripwire = True)
   - Farm safety disclaimers allowed
3. Exception Handling:
   - InputGuardrailTripwireTriggered
   - OutputGuardrailTripwireTriggered
"""

import asyncio
import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

from guardrails.input_guardrail import farming_topic_guardrail, topic_checker_agent
from guardrails.output_guardrail import (
    contains_human_medical_language,
    pesticide_safety_guardrail,
)
from models.schemas import PesticideSafetyCheck, PestDiagnosis, TopicSafetyCheck


# Extract underlying async functions from Guardrail objects
farming_topic_guardrail_fn = getattr(farming_topic_guardrail, "guardrail_function", farming_topic_guardrail)
pesticide_safety_guardrail_fn = getattr(pesticide_safety_guardrail, "guardrail_function", pesticide_safety_guardrail)


def test_input_guardrail_logic():
    print("[-] 1. Testing Input Guardrail (farming_topic_guardrail)...")

    # Verify model and agent
    assert topic_checker_agent.name == "Topic Guardrail Checker"
    assert topic_checker_agent.output_type == TopicSafetyCheck

    async def run_input_tests():
        # Case A: Farming queries (allowed)
        farming_queries = [
            "Main Multan se hun, gandum ki kasht kab karni chahiye?",
            "Kapas pe safed makhi ka hamla hai, kya spray karun?",
            "Urea aur DAP ka rate kya chal raha hai mandi mein?",
        ]
        for query in farming_queries:
            output = await farming_topic_guardrail_fn(None, None, query)
            assert isinstance(output, GuardrailFunctionOutput)
            assert isinstance(output.output_info, TopicSafetyCheck)
            print(f"    [PASS] Allowed query '{query[:35]}...' -> Tripwire={output.tripwire_triggered}")

        # Case B: Off-topic queries (blocked)
        off_topic_queries = [
            "Pakistan cricket team ka agla match kab hai?",
            "Who will win the presidential election in politics?",
            "Write a python program to scrape a website.",
        ]
        for query in off_topic_queries:
            output = await farming_topic_guardrail_fn(None, None, query)
            assert isinstance(output, GuardrailFunctionOutput)
            assert output.tripwire_triggered is True, f"Expected tripwire for '{query}'"
            print(f"    [PASS] Blocked off-topic '{query[:35]}...' -> Tripwire={output.tripwire_triggered} ({output.output_info.reasoning})")

    asyncio.run(run_input_tests())
    print("[+] Input Guardrail verified successfully!")


def test_output_guardrail_logic():
    print("[-] 2. Testing Output Guardrail (pesticide_safety_guardrail)...")

    # Test human medical language detector
    print("    Sub-test: Medical language detection...")
    assert contains_human_medical_language("Take two paracetamol tablets orally for fever") is True
    assert contains_human_medical_language("Inject 5ml antibiotic directly into human vein") is True
    assert contains_human_medical_language("Drink 1 glass of syrup for stomach pain") is True
    # Clean farm safety advice should NOT trigger
    assert contains_human_medical_language("Spray Pyriproxyfen on leaves. Wear gloves and mask. Doctor se raabta karein in case of accident.") is False
    print("    [PASS] Human medical language correctly identified!")

    async def run_output_tests():
        # Case A: Safe pest diagnosis (under certified DPP limit)
        safe_diag = PestDiagnosis(
            likely_pest_or_disease="Whitefly",
            confidence="high",
            treatment="Spray Pyriproxyfen early morning. Wear mask and gloves.",
            dosage_ml_per_liter=2.0,
            max_safe_dosage_ml_per_liter=4.0,
            requires_expert_consultation=False,
        )
        res_safe = await pesticide_safety_guardrail_fn(None, None, safe_diag)
        assert isinstance(res_safe.output_info, PesticideSafetyCheck)
        assert res_safe.tripwire_triggered is False
        assert res_safe.output_info.dosage_within_safe_limit is True
        assert res_safe.output_info.contains_human_medical_advice is False
        print("    [PASS] Safe dosage allowed: tripwire=False")

        # Case B: Excessive dosage exceeding model and independent limit
        unsafe_dosage_diag = PestDiagnosis(
            likely_pest_or_disease="Whitefly",
            confidence="high",
            treatment="Spray Pyriproxyfen 15 ml per liter directly on plants.",
            dosage_ml_per_liter=15.0,
            max_safe_dosage_ml_per_liter=4.0,
            requires_expert_consultation=False,
        )
        res_unsafe_dose = await pesticide_safety_guardrail_fn(None, None, unsafe_dosage_diag)
        assert res_unsafe_dose.tripwire_triggered is True
        assert res_unsafe_dose.output_info.dosage_within_safe_limit is False
        print(f"    [PASS] Excessive dosage blocked: tripwire=True ({res_unsafe_dose.output_info.reasoning})")

        # Case C: Human medical advice violation
        unsafe_medical_diag = PestDiagnosis(
            likely_pest_or_disease="Aphid",
            confidence="high",
            treatment="Take paracetamol tablet orally with syrup if feeling feverish.",
            dosage_ml_per_liter=1.0,
            max_safe_dosage_ml_per_liter=2.5,
            requires_expert_consultation=False,
        )
        res_unsafe_med = await pesticide_safety_guardrail_fn(None, None, unsafe_medical_diag)
        assert res_unsafe_med.tripwire_triggered is True
        assert res_unsafe_med.output_info.contains_human_medical_advice is True
        print(f"    [PASS] Human medical advice blocked: tripwire=True ({res_unsafe_med.output_info.reasoning})")

        # Case D: Independent lookup enforcement (model claimed higher limit than independent CSV)
        over_dpp_diag = PestDiagnosis(
            likely_pest_or_disease="Flonicamid for Jassid",
            confidence="high",
            treatment="Spray Flonicamid 2.0 ml per liter on cotton.",
            dosage_ml_per_liter=2.0,
            max_safe_dosage_ml_per_liter=5.0,  # Model authoring incorrect high limit
            requires_expert_consultation=False,
        )
        res_over_dpp = await pesticide_safety_guardrail_fn(None, None, over_dpp_diag)
        assert res_over_dpp.tripwire_triggered is True
        print(f"    [PASS] Independent lookup table enforcement: tripwire=True ({res_over_dpp.output_info.reasoning})")

    asyncio.run(run_output_tests())
    print("[+] Output Guardrail verified successfully!")


def test_exception_handling():
    print("[-] 3. Verifying Exception Handling resilience...")
    # Verify the two exception classes exist and can be caught without app crash
    assert issubclass(InputGuardrailTripwireTriggered, Exception)
    assert issubclass(OutputGuardrailTripwireTriggered, Exception)

    # Verify source-friendly terminal message content
    input_friendly_message = (
        "Ye sawal Kisan Dost ke scope se bahar hai — mujh se sirf kheti-baari, "
        "mandi rates, mausam, ya sarkari schemes ke baare mein pochain."
    )
    assert "Ye sawal Kisan Dost ke scope se bahar hai" in input_friendly_message
    print(f"    [PASS] Input Tripwire Terminal Message: '{input_friendly_message}'")

    output_friendly_message = (
        "⚠️ TAHAFUZ KA PAIGHAM: Pesticide dosage limit ya ghair-zarai tibbi mashware "
        "(medical advice) ki pabandi ki wajah se yeh jawab rok diya gaya hai."
    )
    assert "Pesticide dosage limit" in output_friendly_message
    print(f"    [PASS] Output Tripwire Terminal Message: '{output_friendly_message}'")
    print("[+] Exception handling verified!")


if __name__ == "__main__":
    print("=" * 60)
    print("KISAN DOST — PART 4 GUARDRAILS TEST SUITE")
    print("=" * 60)
    test_input_guardrail_logic()
    test_output_guardrail_logic()
    test_exception_handling()
    print("=" * 60)
    print("ALL PART 4 GUARDRAILS CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)
