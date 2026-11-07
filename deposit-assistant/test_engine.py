"""Tests for DisputeEngine and strict architectural constraints."""

import unittest
from models import CaseFacts, normalize_ut_location
from engine import DisputeEngine
from intake import extract_case
from followup import followup_questions
from llm_client import ModelResponse


class FakeClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def generate_text(self, prompt: str) -> ModelResponse:
        return ModelResponse(text=self.response, model="fake")


class EngineAndConstraintsTests(unittest.TestCase):
    def test_delhi_state_bug_resolved_auto_mapping(self):
        """Union Territories like Delhi or Chandigarh must map to both city and state."""
        # 1. Direct model instantiation with city="Delhi"
        case_delhi = CaseFacts(city="Delhi")
        self.assertEqual(case_delhi.city, "Delhi")
        self.assertEqual(case_delhi.state, "Delhi")

        # 2. State="Delhi" maps to city="Delhi"
        case_state_delhi = CaseFacts(state="Delhi")
        self.assertEqual(case_state_delhi.city, "Delhi")
        self.assertEqual(case_state_delhi.state, "Delhi")

        # 3. Chandigarh UT mapping
        case_chd = CaseFacts(city="Chandigarh")
        self.assertEqual(case_chd.city, "Chandigarh")
        self.assertEqual(case_chd.state, "Chandigarh")

        # 4. Follow-up questions must NOT ask for state when city is Delhi
        questions = followup_questions(case_delhi)
        self.assertFalse(any("Which state" in q for q in questions))

    def test_dynamic_deduction_reason_business_losses(self):
        """Deduction reason must accept arbitrary strings like 'business losses' without Enum constraint."""
        json_resp = (
            '{"scope": "residential_deposit", "city": "Delhi", "state": "Delhi", '
            '"deposit_amount_inr": 50000, "amount_returned_inr": 20000, '
            '"deduction_reason": "business losses", "deduction_amount_inr": 30000}'
        )
        case = extract_case("Landlord kept 30k for business losses", FakeClient(json_resp))
        self.assertEqual(case.deduction_reason, "business losses")
        self.assertEqual(case.deduction_amount_inr, 30000)

        # Dynamic topic test
        topics = DisputeEngine.get_guidance_topics(case)
        self.assertEqual(topics[0], "Can the landlord deduct for business losses?")
        self.assertNotIn("painting", topics[0].lower())

        # Dynamic guidance evaluation test
        paragraphs, sources = DisputeEngine.evaluate_guidance(case, topics[0])
        self.assertIn("cannot determine", paragraphs[0])
        self.assertIn("business losses", paragraphs[0])
        self.assertNotIn("painting", paragraphs[0])
        self.assertIn("contract", sources)

    def test_tri_state_logic(self):
        """Booleans must not assume 'no'; must strictly use 'yes', 'no', 'unknown'."""
        case = CaseFacts()
        self.assertEqual(case.written_agreement_exists, "unknown")
        self.assertEqual(case.payment_proof_exists, "unknown")

        # Setting explicit 'no'
        case_no = CaseFacts(written_agreement_exists="no", payment_proof_exists="no")
        self.assertEqual(case_no.written_agreement_exists, "no")
        self.assertEqual(case_no.payment_proof_exists, "no")

        # Setting explicit 'yes'
        case_yes = CaseFacts(written_agreement_exists="yes", payment_proof_exists="yes")
        self.assertEqual(case_yes.written_agreement_exists, "yes")
        self.assertEqual(case_yes.payment_proof_exists, "yes")

    def test_ut_normalization_helper(self):
        """Direct test of the normalize_ut_location function."""
        c, s = normalize_ut_location("Delhi", None)
        self.assertEqual(c, "Delhi")
        self.assertEqual(s, "Delhi")

        c2, s2 = normalize_ut_location("Puducherry", None)
        self.assertEqual(c2, "Puducherry")
        self.assertEqual(s2, "Puducherry")

        # Non-UT city should remain unaffected
        c3, s3 = normalize_ut_location("Bengaluru", None)
        self.assertEqual(c3, "Bengaluru")
        self.assertIsNone(s3)

    def test_natural_language_location_parsing_and_uncertainty_clearing(self):
        """Natural language sentences like 'City is Mumbai and state is Maharashtra'

        must parse into separate city/state fields and clear location uncertainties.
        """
        # When city or state contains natural language sentence
        case = CaseFacts(
            state="City is Mumbai and state is Maharashtra",
            uncertainties=["Property location city and state are unknown", "Exact move-out day unclear"],
        )
        self.assertEqual(case.city, "Mumbai")
        self.assertEqual(case.state, "Maharashtra")
        # Location uncertainty must be cleared automatically, other uncertainties preserved
        self.assertNotIn("Property location city and state are unknown", case.uncertainties)
        self.assertIn("Exact move-out day unclear", case.uncertainties)

    def test_major_indian_cities_auto_mapping(self):
        """Major Indian cities (Pune, Bengaluru, Mumbai, Hyderabad, etc.) must auto-resolve state."""
        # 1. Pune -> Maharashtra
        case_pune = CaseFacts(city="Pune")
        self.assertEqual(case_pune.city, "Pune")
        self.assertEqual(case_pune.suggested_state, "Maharashtra")
        # Follow-up questions must NOT ask for state
        q_pune = followup_questions(case_pune)
        self.assertFalse(any("Which state" in q for q in q_pune))

        # 2. Bengaluru -> Karnataka
        case_blr = CaseFacts(city="Bengaluru")
        self.assertEqual(case_blr.city, "Bengaluru")
        self.assertEqual(case_blr.suggested_state, "Karnataka")
        q_blr = followup_questions(case_blr)
        self.assertFalse(any("Which state" in q for q in q_blr))

        # 3. Hyderabad -> Telangana
        case_hyd = CaseFacts(city="Hyderabad")
        self.assertEqual(case_hyd.city, "Hyderabad")
        self.assertEqual(case_hyd.suggested_state, "Telangana")
        q_hyd = followup_questions(case_hyd)
        self.assertFalse(any("Which state" in q for q in q_hyd))

    def test_state_followup_himachal_pradesh_resolution(self):
        """When user replies 'himachal pradesh' to state follow-up question,

        it must set state='Himachal Pradesh' without unpacking error or wrongly setting city.
        """
        from models import resolve_indian_location, INDIAN_STATES
        c, s, sugg = resolve_indian_location(None, "himachal pradesh")
        self.assertEqual(s, "Himachal Pradesh")
        self.assertIsNone(c)

        # If user typed 'himachal pradesh' as city accidentally, resolve_indian_location corrects it
        c2, s2, _ = resolve_indian_location("himachal pradesh", None)
        self.assertEqual(s2, "Himachal Pradesh")
        self.assertIsNone(c2)

        # CaseFacts instantiation with state='himachal pradesh'
        case = CaseFacts(state="himachal pradesh", uncertainties=["Property location city and state are unknown"])
        self.assertEqual(case.state, "Himachal Pradesh")
        self.assertNotIn("Property location city and state are unknown", case.uncertainties)

    def test_followup_no_answers_do_not_overwrite_state_or_city(self):
        """Replying 'no' to agreement or proof must NEVER overwrite state or city with 'no',

        and must correctly update boolean fields and clear uncertainties.
        """
        from models import resolve_indian_location, clean_location_input
        # Verify location functions reject 'no'
        c, s = clean_location_input("no", "no")
        self.assertIsNone(c)
        self.assertIsNone(s)

        rc, rs, _ = resolve_indian_location("no", "no")
        self.assertIsNone(rc)
        self.assertIsNone(rs)

        # Start with state=Maharashtra
        case = CaseFacts(
            scope="residential_deposit",
            state="Maharashtra",
            deduction_reason="painting the flat is my responsibility",
            deduction_amount_inr=10000,
            deposit_amount_inr=25000,
            amount_returned_inr=15000,
            move_out_date="3 January 2025",
            written_agreement_exists="no",
            payment_proof_exists="no",
            uncertainties=[
                "Total deposit amount is unknown",
                "Exact amount returned is unknown",
                "Move-out date is unknown",
                "Written agreement existence is unknown",
                "Payment proof existence is unknown",
            ],
        )
        self.assertEqual(case.state, "Maharashtra")
        self.assertIsNone(case.city)
        self.assertEqual(case.deposit_amount_inr, 25000)
        self.assertEqual(case.amount_returned_inr, 15000)
        self.assertEqual(case.move_out_date, "3 January 2025")
        self.assertEqual(case.written_agreement_exists, "no")
        self.assertEqual(case.payment_proof_exists, "no")
        self.assertEqual(case.uncertainties, [])
        self.assertEqual(followup_questions(case), [])


if __name__ == "__main__":
    unittest.main()

