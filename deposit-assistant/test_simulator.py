"""Tests for the Landlord Pushback Simulator & WhatsApp Rebuttals."""

import unittest
from models import CaseFacts
from simulator import simulate_pushbacks


class SimulatorTests(unittest.TestCase):
    def test_unjustified_case_generates_three_pushbacks(self):
        """Unjustified dispute must generate 3 tactical counter-arguments with statutory WhatsApp rebuttals."""
        case = CaseFacts(
            scope="residential_deposit",
            city="Delhi",
            state="Delhi",
            deposit_amount_inr=60000,
            amount_returned_inr=20000,
            deduction_amount_inr=40000,
            deduction_reason="business losses",
        )
        pushbacks = simulate_pushbacks(case)
        self.assertEqual(len(pushbacks), 3)

        # First tactic: Court delay
        self.assertIn("Court Delay", pushbacks[0]["title"])
        self.assertIn("Model Tenancy", pushbacks[0]["whatsapp_rebuttal"])
        self.assertIn("Lok Adalat", pushbacks[0]["whatsapp_rebuttal"])

        # Second tactic: Notice period forfeiture
        self.assertIn("Notice Period", pushbacks[1]["title"])
        self.assertIn("Section 74", pushbacks[1]["whatsapp_rebuttal"])

        # Third tactic: Business losses specific pushback
        self.assertIn("Personal Financial Hardship", pushbacks[2]["title"])
        self.assertIn("Section 73", pushbacks[2]["whatsapp_rebuttal"])
        self.assertIn("trust", pushbacks[2]["whatsapp_rebuttal"].lower())

    def test_painting_deduction_pushback(self):
        """Painting deduction must generate normal wear and tear WhatsApp rebuttal."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=30000,
            amount_returned_inr=15000,
            deduction_amount_inr=15000,
            deduction_reason="repainting walls",
        )
        pushbacks = simulate_pushbacks(case)
        self.assertEqual(len(pushbacks), 3)
        self.assertIn("Repainting", pushbacks[2]["title"])
        self.assertIn("wear and tear", pushbacks[2]["whatsapp_rebuttal"].lower())
        self.assertIn("GST", pushbacks[2]["whatsapp_rebuttal"])

    def test_justified_invoiced_case_recommends_closure(self):
        """Fully justified case should return closure guidance rather than hostile litigation rebuttals."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=100000,
            amount_returned_inr=75000,
            deduction_amount_inr=25000,
            deduction_reason="water damage",
            other_details=["Landlord provided official carpenter GST invoice and meter bill."],
        )
        pushbacks = simulate_pushbacks(case, posture="justified")
        self.assertEqual(len(pushbacks), 1)
        self.assertIn("Closing", pushbacks[0]["title"])
        self.assertIn("settlement", pushbacks[0]["whatsapp_rebuttal"].lower())

    def test_arbitrary_custom_reason_pushback(self):
        """Any arbitrary, unexpected deduction reason must dynamically adapt Tactic 3."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=45000,
            amount_returned_inr=25000,
            deduction_amount_inr=20000,
            deduction_reason="geyser coil replacement and terrace planter breakage",
        )
        pushbacks = simulate_pushbacks(case)
        self.assertEqual(len(pushbacks), 3)
        self.assertIn("Geyser Coil Replacement", pushbacks[2]["title"])
        self.assertIn("geyser coil replacement and terrace planter breakage", pushbacks[2]["whatsapp_rebuttal"])
        self.assertIn("₹20,000", pushbacks[2]["whatsapp_rebuttal"])

    def test_hybrid_llm_pushback_simulation(self):
        """When an LLM client provides roleplay responses, simulator parses them."""
        import json
        from typing import Any
        from llm_client import ModelResponse

        class FakeSimulatorLLM:
            def generate_json(self, prompt: str, schema: Any) -> ModelResponse:
                tactics = [
                    {
                        "title": "Tactic 1: Court Delay (LLM Simulated)",
                        "landlord_message": "Do whatever you want bhai, court takes 10 years.",
                        "legal_position": "Rent Authority resolves within 60 days under MTA.",
                        "statutory_hook": "MTA 2021 Section 11",
                        "whatsapp_rebuttal": "Dear Landlord, Rent Authority disposes claims in 60 days.",
                    },
                    {
                        "title": "Tactic 2: Notice Period (LLM Simulated)",
                        "landlord_message": "No 2 month notice means forfeit.",
                        "legal_position": "Section 74 ICA bans penalty forfeiture.",
                        "statutory_hook": "Section 74 ICA",
                        "whatsapp_rebuttal": "Dear Landlord, Section 74 ICA bars arbitrary forfeiture.",
                    },
                    {
                        "title": "Tactic 3: Broken Geyser (LLM Simulated)",
                        "landlord_message": "Geyser was burnt by your high voltage.",
                        "legal_position": "Routine electrical failure is owner maintenance.",
                        "statutory_hook": "Section 11 MTA",
                        "whatsapp_rebuttal": "Dear Landlord, electrical wear is owner cost without misuse proof.",
                    },
                ]
                return ModelResponse(text=json.dumps(tactics), model="test")

            def generate_text(self, prompt: str) -> ModelResponse:
                return self.generate_json(prompt, None)

        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=30000,
            amount_returned_inr=15000,
            deduction_amount_inr=15000,
            deduction_reason="broken geyser thermostat",
        )
        res = simulate_pushbacks(case, client=FakeSimulatorLLM())
        self.assertEqual(len(res), 3)
        self.assertIn("LLM Simulated", res[0]["title"])
        self.assertIn("bhai", res[0]["landlord_message"])
        self.assertIn("Section 74", res[1]["whatsapp_rebuttal"])


if __name__ == "__main__":
    unittest.main()
