"""Evidence Strength & Win-Probability Meter for Indian Tenancy Disputes.

Evaluates documentary leverage and statutory evidentiary burden under:
- Bharatiya Sakshya Adhiniyam, 2023 (BSA Section 61 - Electronic Records)
- Indian Contract Act, 1872 (Sections 10, 73, 74)
- Model Tenancy Act, 2021 (Section 11)
"""

from typing import Any
from models import CaseFacts
from draft import classify_dispute_posture


def calculate_evidence_strength(case: CaseFacts) -> dict[str, Any]:
    """Calculates a deterministic 0-100% case recovery strength score based on statutory

    evidentiary thresholds, and generates an itemized leverage audit.
    """
    posture = classify_dispute_posture(case)

    # =========================================================================
    # SPECIAL CASE: FULLY JUSTIFIED DEDUCTIONS (100% Proven via GST Invoices)
    # =========================================================================
    if posture == "justified":
        return {
            "score": 15,
            "tier": "Claim Unviable (Landlord Substantiated)",
            "color": "red",
            "summary": (
                "The landlord has fully satisfied the statutory burden of proof under Section 11 of the "
                "Model Tenancy Act, 2021 and Section 73 of the Indian Contract Act, 1872 by furnishing genuine third-party "
                "GST invoices and utility vouchers for tenant-caused damage or consumption. Challenging this deduction "
                "in court or consumer forum is legally unviable and would likely result in dismissal with costs."
            ),
            "breakdown": [
                {
                    "factor": "Landlord Satisfied Statutory Evidentiary Threshold",
                    "delta": "-60%",
                    "status": "NEGATIVE",
                    "statute": "MTA 2021 §11",
                    "description": "Landlord furnished official contractor GST tax invoices and meter bills, meeting the legal burden of proof.",
                },
                {
                    "factor": "Tenant Liability for Admitted Physical Damage / Arrears",
                    "delta": "-25%",
                    "status": "NEGATIVE",
                    "statute": "ICA 1872 §73",
                    "description": "Actual expenditure resulting from tenant negligence beyond reasonable wear and tear is legally deductible.",
                },
                {
                    "factor": "Verified Deposit Payment & Lease Custody",
                    "delta": "+10%",
                    "status": "POSITIVE",
                    "statute": "BSA 2023 §61",
                    "description": "Payment records confirm original deposit custody, which the landlord has accounted for through refund + invoices.",
                },
            ],
            "actionable_tips": [
                "Do not pursue legal action, NALSA legal aid, or consumer forum complaints; the landlord complied with statutory requirements.",
                "Verify that the billing dates and items correspond to your tenancy period.",
                "Execute the mutual Deposit Settlement & Tenancy Discharge Record (in the 'Demand Letter Draft' tab) to confirm final closure.",
            ],
        }

    # =========================================================================
    # CONTESTED / UNJUSTIFIED / PARTIAL CASES
    # =========================================================================
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

    # 4. Landlord's Evidentiary Deficit vs Partial Receipts (MTA §11 & ICA §73)
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
    elif posture == "partial":
        score -= 10
        breakdown.append({
            "factor": "Mixed Evidence (Partially Invoiced)",
            "delta": "-10%",
            "status": "NEUTRAL",
            "statute": "MTA 2021 §11",
            "description": "Some expenses are verified by invoices (which must be conceded), but the remainder is unproven.",
        })
        tips.append("Concede the verified bills in your demand notice and focus your legal claim exclusively on the unproven balance.")
    else:
        # Landlord made arbitrary deduction without bills (0% proven)
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
