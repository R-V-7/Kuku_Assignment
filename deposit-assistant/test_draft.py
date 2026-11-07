"""Tests for the Demand Letter Draft generator."""

import unittest
from typing import Any
from models import CaseFacts
from draft import generate_demand_letter, classify_dispute_posture


class DraftTests(unittest.TestCase):
    def test_demand_letter_dynamic_deduction_reason(self):
        case = CaseFacts(
            scope="residential_deposit",
            city="Delhi",
            state="Delhi",
            deposit_amount_inr=60000,
            amount_returned_inr=20000,
            move_out_date="15 January 2025",
            written_agreement_exists="yes",
            payment_proof_exists="yes",
            deduction_reason="business losses",
            deduction_amount_inr=40000,
        )
        letter = generate_demand_letter(
            case,
            tenant_name="Rahul Verma",
            landlord_name="Mr. Sharma",
            property_address="Saket, New Delhi",
        )
        self.assertIn("Rahul Verma", letter)
        self.assertIn("Mr. Sharma", letter)
        self.assertIn("Saket, New Delhi", letter)
        self.assertIn("₹40,000", letter)
        self.assertIn("business losses", letter)
        self.assertNotIn("painting", letter)
        self.assertIn("Section 73 of the Indian Contract Act, 1872", letter)
        self.assertIn("written rental agreement", letter)

    def test_demand_letter_no_written_agreement(self):
        case = CaseFacts(
            scope="residential_deposit",
            city="Chandigarh",
            state="Chandigarh",
            deposit_amount_inr=30000,
            amount_returned_inr=0,
            written_agreement_exists="no",
            payment_proof_exists="yes",
        )
        letter = generate_demand_letter(case)
        self.assertIn("oral tenancy agreement", letter)
        self.assertIn("₹30,000", letter)

    def test_demand_letter_unknown_tri_state(self):
        case = CaseFacts(
            scope="residential_deposit",
            written_agreement_exists="unknown",
            payment_proof_exists="unknown",
        )
        letter = generate_demand_letter(case)
        self.assertIn("mutually established", letter)

    def test_demand_letter_justified_settlement_record(self):
        """When landlord provides verified GST invoice and utility bill for admitted damage,
        drafter must NOT generate an adversarial threat; it must generate a formal Settlement Record.
        """
        case = CaseFacts(
            scope="residential_deposit",
            city="Bangalore",
            state="Karnataka",
            deposit_amount_inr=100000,
            amount_returned_inr=75000,
            move_out_date="1st November 2026",
            written_agreement_exists="yes",
            payment_proof_exists="yes",
            deduction_reason="replacing modular kitchen cabinets due to water damage from overflowing sink and pending BESCOM electricity bill",
            deduction_amount_inr=25000,
            other_details=[
                "Landlord sent official carpenter GST invoice and pending BESCOM meter bill on WhatsApp",
                "Tenant accidentally left sink overflowing overnight causing water damage",
            ],
        )
        retrieved_chunks = [
            {"id": "ICA_SEC_73", "section": "Section 73", "act": "Indian Contract Act, 1872", "title": "Compensation for breach"},
            {"id": "MTA_SEC_11", "section": "Section 11", "act": "Model Tenancy Act, 2021", "title": "Deductions for utilities and agreed repairs"},
        ]
        letter = generate_demand_letter(
            case,
            tenant_name="Tenant User",
            landlord_name="Flat Owner",
            property_address="Bangalore Flat",
            retrieved_chunks=retrieved_chunks,
        )
        # Must be a settlement closure record, NOT a hostile demand
        self.assertIn("FORMAL WRITTEN ACKNOWLEDGEMENT & DEPOSIT SETTLEMENT RECORD", letter)
        self.assertIn("BESCOM", letter)
        self.assertIn("Section 11", letter)
        self.assertIn("mutually discharged", letter)
        # Must NOT falsely claim no invoices were provided or threaten litigation
        self.assertNotIn("Arbitrary deductions without providing itemized repair bills, GST invoices", letter)
        self.assertNotIn("initiate formal legal remedies before the competent Rent Authority", letter)

    def test_demand_letter_partial_dispute(self):
        """When one charge is invoiced but another is arbitrary, drafter generates partial demand."""
        case = CaseFacts(
            scope="residential_deposit",
            city="Pune",
            state="Maharashtra",
            deposit_amount_inr=50000,
            amount_returned_inr=25000,
            deduction_reason="business losses and pending electricity meter bill with GST invoice",
            deduction_amount_inr=25000,
            other_details=["Landlord sent official electricity meter bill with payment receipt"],
        )
        posture = classify_dispute_posture(case)
        self.assertEqual(posture, "partial")
        letter = generate_demand_letter(case, posture="partial")
        self.assertIn("FORMAL NOTICE FOR PARTIAL REFUND", letter)
        self.assertIn("CONCESSION OF SPECIFICALLY VERIFIED CHARGES", letter)
        self.assertIn("DISPUTE OF UNJUSTIFIED / UNPROVEN DEDUCTIONS", letter)

    def test_demand_letter_unjustified_business_losses_zero_concession_language(self):
        """When landlord claims arbitrary business losses with zero receipts,

        posture is strictly unjustified (0% proven), demand letter demands 100% refund,
        and there is STRICTLY ZERO mention of conceding any charges or utility bills.
        """
        case = CaseFacts(
            scope="residential_deposit",
            city="Pune",
            state="Maharashtra",
            deposit_amount_inr=60000,
            amount_returned_inr=20000,
            deduction_amount_inr=40000,
            deduction_reason="business losses",
            other_details=["He claims he had business losses and needs the money."],
        )
        # Even if evaluation_text quotes Section 11 MTA ("receipts for actual expenditure incurred")
        eval_text = (
            "Under Section 11 of the Model Tenancy Act, 2021, any deduction must be supported by "
            "an itemized written statement and receipts for actual expenditure incurred. "
            "Personal business losses have zero legal connection to the tenancy."
        )
        posture = classify_dispute_posture(case, evaluation_text=eval_text)
        self.assertEqual(posture, "unjustified")

        letter = generate_demand_letter(case, evaluation_text=eval_text)
        self.assertIn("FORMAL NOTICE FOR REFUND OF SECURITY DEPOSIT", letter)
        self.assertIn("Formal Demand for Immediate Refund of Outstanding Security Deposit of ₹40,000", letter)
        # Crucial anti-hallucination checks:
        self.assertNotIn("conced", letter.lower())
        self.assertNotIn("utility", letter.lower())
        self.assertNotIn("bescom", letter.lower())

    def test_hybrid_llm_posture_classification(self):
        """When an LLM client returns structured JSON, hybrid classifier parses it."""
        from llm_client import ModelResponse

        class FakeLLMClient:
            def __init__(self, posture_val: str) -> None:
                self.posture_val = posture_val

            def generate_json(self, prompt: str, schema: Any) -> ModelResponse:
                return ModelResponse(text=f'{{"posture": "{self.posture_val}", "rationale": "verified invoice"}}', model="test")

            def generate_text(self, prompt: str) -> ModelResponse:
                return ModelResponse(text=f'{{"posture": "{self.posture_val}", "rationale": "verified invoice"}}', model="test")

        case = CaseFacts(
            scope="residential_deposit",
            deduction_reason="novel custom repair with Urban Company verified receipt",
            deduction_amount_inr=5000,
        )
        # Test LLM returning justified
        res_just = classify_dispute_posture(case, client=FakeLLMClient("justified"))
        self.assertEqual(res_just, "justified")

        # Test LLM returning partial
        res_part = classify_dispute_posture(case, client=FakeLLMClient("partial"))
        self.assertEqual(res_part, "partial")

        # Test LLM failure falls back cleanly to heuristics
        class FailingLLMClient:
            def generate_text(self, prompt: str) -> ModelResponse:
                raise RuntimeError("API timeout")

        res_fallback = classify_dispute_posture(case, client=FailingLLMClient())
        self.assertIn(res_fallback, ("unjustified", "partial", "justified"))


if __name__ == "__main__":
    unittest.main()
