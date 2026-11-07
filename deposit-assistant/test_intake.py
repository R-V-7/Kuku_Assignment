import unittest

from intake import IntakeError, extract_case
from llm_client import ModelResponse
from models import CaseFacts


class FakeClient:
    def __init__(self, response):
        self.response = response

    def generate_text(self, prompt):
        return ModelResponse(text=self.response, model="fake")


class IntakeTests(unittest.TestCase):
    def test_unknown_fields_stay_unknown(self):
        case = extract_case("My landlord owes my deposit.", FakeClient('{"deposit_amount_inr": 50000}'))
        self.assertEqual(case.deposit_amount_inr, 50000)
        self.assertEqual(case.agreement_exists, "unknown")
        self.assertEqual(case.payment_proof_exists, "unknown")
        self.assertIsNone(case.move_out_date)

    def test_invalid_or_extra_fields_rejected(self):
        for response in ('{"agreement_exists": false}', '{"deposit_amount_inr": -1}', '{"invented": true}', 'not JSON'):
            with self.subTest(response=response), self.assertRaises(IntakeError):
                extract_case("Example", FakeClient(response))

    def test_fenced_json(self):
        case = extract_case("Example", FakeClient('```json\n{"scope": "unknown"}\n```'))
        self.assertEqual(case.scope, "unknown")

    def test_empty_story_rejected(self):
        with self.assertRaises(IntakeError):
            extract_case("  ", FakeClient('{}'))

    def test_followup_passes_prior_case_and_question(self):
        class RecordingClient(FakeClient):
            def generate_text(self, prompt):
                self.prompt = prompt
                return super().generate_text(prompt)

        client = RecordingClient('{"deposit_amount_inr":50000,"deduction_amount_inr":5000}')
        case = extract_case("5000", client, CaseFacts(deposit_amount_inr=50000), "How much is the deduction?")
        self.assertIn('"deposit_amount_inr":50000', client.prompt)
        self.assertIn("How much is the deduction?", client.prompt)
        self.assertEqual(case.deduction_amount_inr, 5000)

    def test_suggested_state_is_not_confirmed_state(self):
        case = extract_case("Mumbai", FakeClient('{"city":"Mumbai","suggested_state":"Maharashtra"}'))
        self.assertIsNone(case.state)
        self.assertEqual(case.suggested_state, "Maharashtra")

    def test_inference_is_kept_separately_for_review(self):
        case = extract_case("Deposit 50000, returned 10000", FakeClient('{"deposit_amount_inr":50000,"amount_returned_inr":10000,"inferred_details":["40000 remains before any deductions"]}'))
        self.assertEqual(case.inferred_details, ["40000 remains before any deductions"])

    def test_invalid_response_is_retried_with_structured_schema(self):
        class RetryClient:
            def __init__(self):
                self.calls = 0

            def generate_json(self, prompt, schema):
                self.calls += 1
                self.schema = schema
                return ModelResponse(text="invalid" if self.calls == 1 else '{"deposit_amount_inr":60000}', model="fake")

        client = RetryClient()
        case = extract_case("Deposit was 60000", client)
        self.assertEqual(case.deposit_amount_inr, 60000)
        self.assertEqual(client.calls, 2)
        self.assertIn("properties", client.schema)


if __name__ == "__main__":
    unittest.main()
