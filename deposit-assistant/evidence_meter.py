"""Evidence Strength & Win-Probability Meter for Indian Tenancy Disputes.

Evaluates documentary leverage and statutory evidentiary burden under:
- Bharatiya Sakshya Adhiniyam, 2023 (BSA Section 61 - Electronic Records)
- Indian Contract Act, 1872 (Sections 10, 73, 74)
- Model Tenancy Act, 2021 (Section 11)
"""

from typing import Any
from models import CaseFacts


def calculate_evidence_strength(case: CaseFacts) -> dict[str, Any]:
    """Calculates a deterministic 0-100% case strength score based on statutory

    evidentiary thresholds, and generates an itemized leverage audit.
    """
    score = 40  # Baseline neutral starting point
    breakdown = []
    tips = []

    # 1. Payment Proof (BSA 2023 Section 61 - Electronic Records / Bank Trail)
    if case.payment_proof_exists == "yes":
        score += 25
        breakdown.append({
            "factor": "Verified Deposit Payment Trail",
            "delta": "+25%",
            "status": "POSITIVE",
            "statute": "BSA 2023 §61",
            "description": "Bank transfer / UPI records serve as admissible electronic evidence proving deposit custody.",
        })
    elif case.payment_proof_exists == "no":
        score -= 20
        breakdown.append({
            "factor": "No Payment Proof (Cash/Unrecorded)",
            "delta": "-20%",
            "status": "NEGATIVE",
            "statute": "BSA 2023 §61",
            "description": "Lack of receipts or bank statements shifts the initial burden of proving payment onto the tenant.",
        })
        tips.append("Retrieve passbook entries, UPI transaction IDs, or WhatsApp payment acknowledgments to establish payment proof.")
    else:
        breakdown.append({
            "factor": "Payment Proof Status Unknown",
            "delta": "0%",
            "status": "NEUTRAL",
            "statute": "BSA 2023 §61",
            "description": "Custody proof not yet confirmed. Documentary bank records strongly increase claim leverage.",
        })
        tips.append("Locate your bank or UPI transaction record to secure an immediate +25% evidence boost.")

    # 2. Written Tenancy Agreement (ICA 1872 Section 10 & MTA 2021 Section 4)
    if case.written_agreement_exists == "yes":
        score += 20
        breakdown.append({
            "factor": "Signed Rental Agreement",
            "delta": "+20%",
            "status": "POSITIVE",
            "statute": "ICA 1872 §10 / MTA §4",
            "description": "Written agreement binds both parties to specific deposit refund terms and exit protocols.",
        })
    elif case.written_agreement_exists == "no":
        score -= 10
        breakdown.append({
            "factor": "Oral Lease Agreement",
            "delta": "-10%",
            "status": "NEGATIVE",
            "statute": "MTA 2021 §4",
            "description": "Absence of a written lease requires proving tenancy terms through rent receipts and conduct.",
        })
        tips.append("Gather rent receipts, society entry logs, or utility payments in your name to prove tenancy duration.")
    else:
        breakdown.append({
            "factor": "Agreement Status Unknown",
            "delta": "0%",
            "status": "NEUTRAL",
            "statute": "ICA 1872 §10",
            "description": "Contractual terms remain unverified.",
        })

    # 3. Move-out Date & Peaceful Vacating Proof (Transfer of Property Act §108)
    if case.move_out_date:
        score += 10
        breakdown.append({
            "factor": "Established Move-Out Timeline",
            "delta": "+10%",
            "status": "POSITIVE",
            "statute": "TPA 1882 §108(q)",
            "description": "Documented move-out date establishes the statutory 30-day deadline for deposit return.",
        })
    else:
        score -= 5
        tips.append("Confirm your exact move-out date and preserve key handover text messages.")

    # 4. Landlord's Evidentiary Deficit vs Justified Receipts (MTA §11 & ICA §73)
    other_details_str = " ".join(case.other_details).lower()
    has_landlord_invoices = any(
        k in other_details_str
        for k in ["invoice", "gst", "receipt", "bill", "voucher", "contractor bill"]
    )

    reason_lower = (case.deduction_reason or "").lower()
    is_personal_loss = any(
        k in reason_lower
        for k in ["business", "loss", "losses", "personal", "wedding", "loan", "crisis"]
    )

    if is_personal_loss:
        score += 15
        breakdown.append({
            "factor": "Unrelated Hardship Excuse (No Legal Nexus)",
            "delta": "+15%",
            "status": "POSITIVE",
            "statute": "ICA 1872 §73",
            "description": "Personal business losses have zero legal connection to residential tenancy. Clear breach of contract.",
        })
    elif has_landlord_invoices:
        # Landlord has verified invoices
        score -= 25
        breakdown.append({
            "factor": "Landlord Produced Verified Tax Invoices",
            "delta": "-25%",
            "status": "NEGATIVE",
            "statute": "MTA 2021 §11",
            "description": "Landlord has documentary receipts for actual expenditure, satisfying the statutory burden of proof.",
        })
    else:
        # Landlord made arbitrary deduction without bills
        score += 15
        breakdown.append({
            "factor": "Landlord Lacks Itemized Receipts",
            "delta": "+15%",
            "status": "POSITIVE",
            "statute": "MTA 2021 §11 / ICA §73",
            "description": "Unilateral deduction without third-party invoices constitutes arbitrary retention under Indian law.",
        })

    # Clamp score to [10, 95] to reflect realistic legal uncertainty
    final_score = max(10, min(95, score))

    if final_score >= 70:
        tier = "Strong Legal Position"
        color = "green"
        summary = "You possess strong documentary evidence. The statutory burden of proof rests heavily on the landlord."
    elif final_score >= 45:
        tier = "Moderate Leverage"
        color = "orange"
        summary = "You have a viable legal claim, but reinforcing electronic payment and handover records will strengthen your recovery."
    else:
        tier = "High Evidence Deficit"
        color = "red"
        summary = "Documentary evidence is limited. Prioritize gathering electronic banking trails and written communications before legal escalation."

    return {
        "score": final_score,
        "tier": tier,
        "color": color,
        "summary": summary,
        "breakdown": breakdown,
        "actionable_tips": tips,
    }
