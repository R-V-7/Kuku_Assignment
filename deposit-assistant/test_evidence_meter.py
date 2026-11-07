"""Tests for the Evidence Strength & Win-Probability Meter."""

import unittest
from models import CaseFacts
from evidence_meter import calculate_evidence_strength


class EvidenceMeterTests(unittest.TestCase):
    def test_strong_case_bank_agreement_and_unproven_deduction(self):
        """Case with UPI/bank statement, written lease, and unproven deduction should score high (>=70%)."""
        case = CaseFacts(
            scope="residential_deposit",
            city="Delhi",
            state="Delhi",
            deposit_amount_inr=50000,
            amount_returned_inr=20000,
            deduction_amount_inr=30000,
            deduction_reason="business losses",
            written_agreement_exists="yes",
            payment_proof_exists="yes",
            move_out_date="15 January 2025",
        )
        result = calculate_evidence_strength(case)
        self.assertGreaterEqual(result["score"], 75)
        self.assertEqual(result["tier"], "Strong Legal Position")
        self.assertEqual(result["color"], "green")

        # Verify key breakdown entries
        factors = [b["factor"] for b in result["breakdown"]]
        self.assertIn("Verified Deposit Payment Trail", factors)
        self.assertIn("Signed Rental Agreement", factors)
        self.assertIn("Unrelated Hardship Excuse (No Legal Nexus)", factors)

    def test_weak_case_cash_no_agreement(self):
        """Oral lease with cash deposit and no proof should score lower and recommend tips."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=25000,
            amount_returned_inr=15000,
            written_agreement_exists="no",
            payment_proof_exists="no",
        )
        result = calculate_evidence_strength(case)
        self.assertLessEqual(result["score"], 45)
        self.assertIn(result["tier"], ["Moderate Leverage", "High Evidence Deficit"])
        self.assertTrue(len(result["actionable_tips"]) > 0)

    def test_invoiced_deductions_lower_score(self):
        """When landlord provides verified GST invoice, tenant's unilateral claim score decreases."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=100000,
            amount_returned_inr=75000,
            deduction_amount_inr=25000,
            deduction_reason="water damage to cabinets",
            written_agreement_exists="yes",
            payment_proof_exists="yes",
            move_out_date="1 November 2026",
            other_details=["Landlord provided official carpenter GST invoice and BESCOM bill."],
        )
        result = calculate_evidence_strength(case)
        factors = [b["factor"] for b in result["breakdown"]]
        self.assertIn("Landlord Produced Verified Tax Invoices", factors)


if __name__ == "__main__":
    unittest.main()
