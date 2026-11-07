import unittest

from guidance import SOURCES, TOPICS, guidance_for
from models import CaseFacts


class GuidanceTests(unittest.TestCase):
    def test_deduction_not_declared_legal(self):
        text, refs = guidance_for(CaseFacts(scope="residential_deposit", deduction_amount_inr=20000), TOPICS[0])
        self.assertIn("cannot determine", text[0])
        self.assertTrue(any("20,000" in p for p in text))
        self.assertTrue(all(ref in SOURCES for ref in refs))

    def test_arithmetic_not_a_legal_conclusion(self):
        case = CaseFacts(scope="residential_deposit", deposit_amount_inr=50000, amount_returned_inr=10000)
        text, _ = guidance_for(case, TOPICS[1])
        self.assertIn("40,000", text[0])
        self.assertIn("not a legal determination", text[0])

    def test_out_of_scope_does_not_show_rental_guidance(self):
        text, _ = guidance_for(CaseFacts(scope="other"), TOPICS[0])
        self.assertIn("limited", text[0])
        self.assertNotIn("painting", " ".join(text))

    def test_what_can_i_do_next_justified_recommends_settlement(self):
        """When landlord provided verified GST invoices and utility bills for admitted damage,

        'What can I do next?' must recommend settlement closure, NOT a demand notice.
        """
        case = CaseFacts(
            scope="residential_deposit",
            city="Bangalore",
            state="Karnataka",
            deposit_amount_inr=100000,
            amount_returned_inr=75000,
            deduction_amount_inr=25000,
            deduction_reason="replacing modular kitchen cabinets due to water damage from overflowing sink and pending BESCOM electricity bill",
            other_details=[
                "Landlord sent official carpenter GST invoice and pending BESCOM meter bill on WhatsApp",
                "Tenant accidentally left sink overflowing overnight causing water damage",
            ],
        )
        paragraphs, _ = guidance_for(case, "What can I do next?")
        combined = " ".join(paragraphs)
        self.assertIn("Settlement & Discharge Record", combined)
        self.assertIn("Reconcile and Verify Invoices", combined)
        # Must NOT advise threatening the landlord with a demand notice
        self.assertNotIn("formal written demand notice", combined)

    def test_legal_help_justified_advises_against_litigation(self):
        """When deductions are justified and invoiced, 'Can I get legal help' must NOT recommend NALSA/litigation."""
        case = CaseFacts(
            scope="residential_deposit",
            city="Bangalore",
            state="Karnataka",
            deposit_amount_inr=100000,
            amount_returned_inr=75000,
            deduction_amount_inr=25000,
            deduction_reason="replacing modular kitchen cabinets due to water damage from overflowing sink and pending BESCOM electricity bill",
            other_details=[
                "Landlord sent official carpenter GST invoice and pending BESCOM meter bill on WhatsApp",
                "Tenant accidentally left sink overflowing overnight causing water damage",
            ],
        )
        paragraphs, _ = guidance_for(case, "Can I get legal help or explore settlement?")
        combined = " ".join(paragraphs)
        # Must advise that legal action is not recommended
        self.assertIn("Legal Action Not Recommended", combined)
        self.assertIn("Risk of Dismissal & Legal Costs", combined)
        self.assertIn("Section 11 of the Model Tenancy Act", combined)
        self.assertIn("Section 73 of the Indian Contract Act", combined)
        # Must NOT encourage NALSA or Lok Adalat litigation
        self.assertNotIn("NALSA explains how to approach", combined)
        self.assertNotIn("National Helpline 15100", combined)

    def test_unjustified_recommends_demand_notice_and_nalsa(self):
        """When deductions are arbitrary (e.g. business losses), advise formal notice and NALSA."""
        case = CaseFacts(
            scope="residential_deposit",
            city="Delhi",
            state="Delhi",
            deposit_amount_inr=60000,
            amount_returned_inr=20000,
            deduction_amount_inr=40000,
            deduction_reason="business losses",
        )
        # 1. Next steps
        next_steps, _ = guidance_for(case, "What can I do next?")
        self.assertTrue(any("demand notice" in p.lower() for p in next_steps))

        # 2. Legal help
        legal_help, _ = guidance_for(case, "Can I get legal help or explore settlement?")
        self.assertTrue(any("NALSA" in p for p in legal_help))
        self.assertTrue(any("Lok Adalat" in p for p in legal_help))

    def test_unjustified_zero_concession_anti_hallucination(self):
        """Ensure cases with 0% proven deductions (e.g. business losses) never hallucinate

        conceded utility bills or concession language even with statutory evaluation text.
        """
        case = CaseFacts(
            scope="residential_deposit",
            city="Pune",
            state="Maharashtra",
            deposit_amount_inr=60000,
            amount_returned_inr=20000,
            deduction_amount_inr=40000,
            deduction_reason="business losses",
            other_details=["Landlord claims he had business losses and needs the money."],
        )
        eval_text = (
            "Under Section 11 of the Model Tenancy Act, 2021, deductions must be supported by "
            "an itemized written statement and receipts for actual expenditure incurred. "
            "Personal business losses have zero legal connection to the tenancy."
        )
        # 1. Next steps
        next_steps, _ = guidance_for(case, "What can I do next?", evaluation_text=eval_text)
        combined_next = " ".join(next_steps)
        self.assertIn("Demand Notice", combined_next)
        self.assertNotIn("conced", combined_next.lower())
        self.assertNotIn("utility", combined_next.lower())
        self.assertNotIn("bescom", combined_next.lower())

        # 2. Legal help
        legal_help, _ = guidance_for(case, "Can I get legal help or explore settlement?", evaluation_text=eval_text)
        combined_help = " ".join(legal_help)
        self.assertIn("NALSA", combined_help)
        self.assertIn("Lok Adalat", combined_help)
        self.assertNotIn("Legal Action Not Recommended", combined_help)

    def test_hybrid_llm_guidance_generation(self):
        """When an LLM client provides custom statutory analysis, guidance_for integrates it."""
        from typing import Any
        from llm_client import ModelResponse

        class FakeGuidanceLLM:
            def generate_json(self, prompt: str, schema: Any) -> ModelResponse:
                return ModelResponse(
                    text='{"analysis_paragraphs": ["Custom LLM analysis of piped gas bill under Section 73 ICA.", "**Actionable Strategy:** Demand actual PNG meter statement."]}',
                    model="test",
                )

            def generate_text(self, prompt: str) -> ModelResponse:
                return ModelResponse(
                    text='{"analysis_paragraphs": ["Custom LLM analysis of piped gas bill under Section 73 ICA.", "**Actionable Strategy:** Demand actual PNG meter statement."]}',
                    model="test",
                )

        case = CaseFacts(
            scope="residential_deposit",
            deduction_reason="unpaid piped gas pipeline bill",
            deduction_amount_inr=3500,
        )
        paragraphs, sources = guidance_for(case, "Can the landlord deduct for unpaid piped gas pipeline bill?", client=FakeGuidanceLLM())
        combined = " ".join(paragraphs)
        self.assertIn("Custom LLM analysis of piped gas bill", combined)
        self.assertIn("Demand actual PNG meter statement", combined)
        self.assertIn("contract", sources)


if __name__ == "__main__":
    unittest.main()
