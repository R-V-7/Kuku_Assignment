"""Deterministic prompts for incomplete or ambiguous case information."""

import re
from models import CaseFacts, UNION_TERRITORIES, MAJOR_INDIAN_CITIES_TO_STATE


def followup_questions(case: CaseFacts) -> list[str]:
    questions = []
    if case.scope == "unknown":
        questions.append("Is this about the security deposit for a residential rental?")

    # State check: Only prompt for state if missing AND city is not an auto-resolved UT or known city
    if not case.state and not case.suggested_state:
        c_clean = case.city.strip().lower() if case.city else ""
        if c_clean not in UNION_TERRITORIES and c_clean not in MAJOR_INDIAN_CITIES_TO_STATE:
            questions.append("Which state is the rental property in?")

    if case.deposit_amount_inr is None:
        questions.append("How much was the security deposit, in rupees?")

    # Auto-calculate amount_returned_inr when both deposit and deduction are known
    # Skip the returned question entirely if we can derive it
    if case.amount_returned_inr is None:
        if case.deposit_amount_inr is not None and case.deduction_amount_inr is not None:
            # Can be auto-calculated: returned = deposit - deduction
            # Don't ask the question; the app.py / Step 3 will auto-fill
            pass
        else:
            questions.append("How much of the deposit, if any, has already been returned?")

    if not case.move_out_date or not re.search(r"\b(?:19|20)\d{2}\b", case.move_out_date):
        questions.append("When did you move out? Please include the year, if known.")
    if case.written_agreement_exists == "unknown":
        questions.append("Was there a written rental agreement?")
    if case.payment_proof_exists == "unknown":
        questions.append("Do you have proof that you paid the deposit?")
    if not case.deduction_reason:
        questions.append("Has the landlord given a reason for withholding or deducting money?")
    if case.deduction_reason and case.deduction_amount_inr is None:
        questions.append("Has the landlord specified how much they want to deduct? If so, how much?")

    # DO NOT append any uncertainty-based questions.
    # All critical fields are already covered by the deterministic questions above.
    # Uncertainty-based questions cause routing failures and field overwrites in app.py.

    return questions


def unanswered_questions(questions: list[str], answered: list[str]) -> list[str]:
    """Do not repeat a question after a reply, even when its answer is unknown."""
    completed = set(answered)
    return [question for question in questions if question not in completed]
