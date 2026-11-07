import unittest

from followup import followup_questions, unanswered_questions
from models import CaseFacts


class FollowupTests(unittest.TestCase):
    def test_partial_date_and_unknowns_prompt(self):
        questions = followup_questions(CaseFacts(move_out_date="March", deduction_reason="painting"))
        self.assertTrue(any("year" in question for question in questions))
        self.assertTrue(any("deduct" in question for question in questions))
        self.assertTrue(any("agreement" in question for question in questions))

    def test_explicit_no_is_not_unknown(self):
        questions = followup_questions(CaseFacts(agreement_exists="no", payment_proof_exists="no", move_out_date="March 2025"))
        self.assertFalse(any("agreement" in question for question in questions))
        self.assertFalse(any("proof" in question for question in questions))
        self.assertFalse(any("year" in question for question in questions))

    def test_known_deduction_no_longer_asked(self):
        case = CaseFacts(deduction_reason="painting", deduction_amount_inr=5000)
        self.assertFalse(any("specified how much" in question for question in followup_questions(case)))

    def test_unknown_answer_does_not_repeat_question(self):
        questions = followup_questions(CaseFacts(deduction_reason="painting"))
        deduction = next(q for q in questions if "specified how much" in q)
        remaining = unanswered_questions(questions, [deduction])
        self.assertNotIn(deduction, remaining)
        self.assertIn("Which state is the rental property in?", remaining)

    def test_uncertainties_pruning_and_no_redundant_questions(self):
        """Uncertainties about known fields (deposit, returned, date, state) must be automatically

        cleared and must NEVER prompt redundant 'Please clarify this uncertainty' loops.
        """
        # When user populates known fields
        case = CaseFacts(
            scope="residential_deposit",
            state="Punjab",
            deposit_amount_inr=25000,
            amount_returned_inr=15000,
            move_out_date="2nd january 2026",
            written_agreement_exists="no",
            payment_proof_exists="no",
            deduction_reason="painting",
            deduction_amount_inr=10000,
            uncertainties=[
                "Total deposit amount is unknown",
                "Amount returned in INR is unknown",
                "Move out date is unknown",
                "Location is unknown",
            ],
        )
        # All standard uncertainties must be automatically cleared
        self.assertEqual(case.uncertainties, [])
        # No follow-up questions remaining
        remaining_q = followup_questions(case)
        self.assertEqual(remaining_q, [])

    def test_auto_calculate_returned_amount_skips_redundant_question(self):
        """When deposit and deduction amount are both known, amount_returned_inr must be

        auto-calculated (deposit - deduction), and the returned question must be suppressed.
        """
        # Scenario where landlord kept 15000 and user enters deposit of 25000
        case = CaseFacts(
            scope="residential_deposit",
            state="Maharashtra",
            deposit_amount_inr=25000,
            deduction_amount_inr=15000,
            deduction_reason="painting the flat is my responsibility",
        )
        # amount_returned_inr must be auto-calculated to 10,000
        self.assertEqual(case.amount_returned_inr, 10000)
        # follow-up questions must NOT ask for amount returned
        questions = followup_questions(case)
        self.assertFalse(any("returned" in q.lower() for q in questions))
        self.assertFalse(any("deposit, if any" in q.lower() for q in questions))


if __name__ == "__main__":
    unittest.main()
