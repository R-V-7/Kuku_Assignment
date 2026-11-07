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


if __name__ == "__main__":
    unittest.main()
