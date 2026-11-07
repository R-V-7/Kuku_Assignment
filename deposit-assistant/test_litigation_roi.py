"""Unit tests for Dispute Resolution Litigation ROI & Forum Recommender."""

import unittest
from models import CaseFacts
from litigation_roi import calculate_litigation_roi


class LitigationROITests(unittest.TestCase):
    def test_micro_dispute_under_15k_recommends_dlsa_lok_adalat(self):
        """Micro disputes (<15k) must warn against private lawyers and recommend zero-cost DLSA Lok Adalat."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=25000,
            amount_returned_inr=15000,
            deduction_amount_inr=10000,
            deduction_reason="painting and deep cleaning",
            city="Delhi",
            state="Delhi",
        )
        res = calculate_litigation_roi(case)
        self.assertEqual(res["disputed_amount_inr"], 10000)
        self.assertEqual(res["roi_tier"], "ZERO_COST_ESCALATION")
        self.assertIn("DLSA", res["recommended_forum"])
        self.assertIn("DO NOT hire a private advocate", res["lawyer_fee_advice"])
        self.assertEqual(res["court_fee_display"], "₹0 (Completely Free)")

    def test_mid_range_dispute_recommends_edaakhil_consumer_commission(self):
        """Mid-range claims (15k-60k) recommend self-filed e-Daakhil with zero court fee."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=60000,
            amount_returned_inr=20000,
            deduction_amount_inr=40000,
            deduction_reason="business losses",
            city="Chandigarh",
            state="Chandigarh",
        )
        res = calculate_litigation_roi(case)
        self.assertEqual(res["disputed_amount_inr"], 40000)
        self.assertEqual(res["roi_tier"], "FAVORABLE_CONSUMER_COMMISSION")
        self.assertIn("e-Daakhil", res["recommended_forum"])
        self.assertIn("5 Lakh", res["court_fee_display"])
        self.assertTrue(res["total_claimable_inr"] >= 40000)

    def test_high_value_dispute_recommends_rent_authority_summary_suit(self):
        """High-value claims (>60k) recommend Rent Authority / Summary Suit with statutory interest."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=150000,
            amount_returned_inr=50000,
            deduction_amount_inr=100000,
            deduction_reason="unilateral interior renovation charges",
            city="Bengaluru",
            state="Karnataka",
        )
        res = calculate_litigation_roi(case)
        self.assertEqual(res["disputed_amount_inr"], 100000)
        self.assertEqual(res["roi_tier"], "SUBSTANTIAL_CLAIM_MULTI_FORUM")
        self.assertIn("Rent Authority", res["recommended_forum"])
        self.assertTrue(res["statutory_interest_inr"] > 0)

    def test_justified_invoiced_case_has_negative_litigation_roi(self):
        """When landlord provides verified GST invoices, litigation ROI is negative/not recommended."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=80000,
            amount_returned_inr=50000,
            deduction_amount_inr=30000,
            deduction_reason="repaired broken glass door with contractor GST invoice",
            other_details=["landlord provided GST tax invoice and utility bill for broken door"],
            city="Bengaluru",
            state="Karnataka",
        )
        res = calculate_litigation_roi(case, posture="justified")
        self.assertEqual(res["roi_tier"], "NOT_RECOMMENDED")
        self.assertEqual(res["disputed_amount_inr"], 0)
        self.assertIn("Do NOT hire a lawyer", res["lawyer_fee_advice"])
        self.assertIn("Mutual Settlement", res["recommended_forum"])


if __name__ == "__main__":
    unittest.main()
