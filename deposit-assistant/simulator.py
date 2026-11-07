"""Landlord Pushback Simulator & Strategic WhatsApp Rebuttals.

Simulates common landlord adversarial responses under Indian tenancy norms
and equips tenants with legally grounded, 2-line WhatsApp rebuttals citing:
- Indian Contract Act, 1872 (Sections 73, 74)
- Model Tenancy Act, 2021 (Section 11)
- Bharatiya Sakshya Adhiniyam, 2023 (Section 61)
- Transfer of Property Act, 1882 (Sections 106, 108)
- Legal Services Authorities Act, 1987 (Pre-Litigation Lok Adalat)
"""

from typing import Any
from models import CaseFacts
from draft import classify_dispute_posture


def simulate_pushbacks(case: CaseFacts, posture: str | None = None) -> list[dict[str, Any]]:
    """Generates 3 realistic adversarial landlord responses and corresponding

    statutorily grounded WhatsApp rebuttals tailored to the specific case facts.
    """
    if posture is None:
        posture = classify_dispute_posture(case)

    # Disputed amount calculation
    dep = case.deposit_amount_inr or 0
    ret = case.amount_returned_inr or 0
    disputed_amt = max(0, dep - ret) if case.deposit_amount_inr is not None else (case.deduction_amount_inr or 0)
    amt_str = f"₹{disputed_amt:,}" if disputed_amt > 0 else "the outstanding deposit"

    reason_lower = (case.deduction_reason or "").lower()

    # If case is 100% justified with verified invoices
    if posture == "justified":
        return [
            {
                "title": "Closing the Dispute (Landlord Seeks Final Clearance)",
                "landlord_message": (
                    f"\"I have already returned the balance deposit and shared the actual repair GST invoice and utility bill. "
                    f"Please confirm receipt and confirm that all accounts are settled.\""
                ),
                "legal_position": (
                    "Under Section 11 of the Model Tenancy Act, 2021, the landlord has fulfilled the statutory burden "
                    "by providing third-party tax invoices for actual expenditure. The matter is legally resolved."
                ),
                "statutory_hook": "Section 11 Model Tenancy Act, 2021 & Section 73 Indian Contract Act, 1872",
                "whatsapp_rebuttal": (
                    f"\"Dear Landlord, I have verified the contractor GST invoice and utility bill. The accounts reconcile. "
                    f"I have received the balance deposit and confirm full and final settlement of all tenancy obligations. Thank you.\""
                ),
            }
        ]

    pushbacks = []

    # Pushback 1: The Court Delay & Intimidation Defense
    pushbacks.append({
        "title": "Tactic 1: Court Delay / Litigation Threat (\"Go to court, it will take 5 years\")",
        "landlord_message": (
            f"\"Do whatever you want. Send any notice you like. Civil court cases in India take 5 to 10 years. "
            f"You will spend more money on your lawyer's fees than the {amt_str} you are asking for.\""
        ),
        "legal_position": (
            "Tenancy deposit disputes do not require protracted civil litigation. The Model Tenancy framework "
            "mandates summary resolution by the Rent Authority within 60 days. Furthermore, pre-litigation conciliation "
            "through the District Legal Services Authority (DLSA) / Lok Adalat is free of court fees and produces an enforceable civil decree."
        ),
        "statutory_hook": "Section 11 Model Tenancy Act, 2021 & Legal Services Authorities Act, 1987",
        "whatsapp_rebuttal": (
            f"\"Dear Landlord, rental deposit recovery does not require lengthy civil suits. Under the Model Tenancy framework, "
            f"the Rent Authority resolves deposit withholding summarily within 60 days. Furthermore, I can initiate free pre-litigation "
            f"conciliation via the District Legal Services Authority (DLSA) / Lok Adalat at zero court fees. Please release {amt_str} "
            f"within the 15-day notice window to avoid formal registration of this dispute.\""
        ),
    })

    # Pushback 2: The Unilateral "Notice Period Deficit" or Forfeiture Penalty
    pushbacks.append({
        "title": "Tactic 2: Notice Period Forfeiture (\"You didn't give 2 months notice\")",
        "landlord_message": (
            f"\"You vacated suddenly without giving a full 2-month advance written notice. "
            f"Your deposit is therefore forfeited as rent in lieu of notice.\""
        ),
        "legal_position": (
            "Under Section 106 of the Transfer of Property Act, 1882, the statutory notice period for residential tenancies "
            "is 15 days. Moreover, under Section 74 of the Indian Contract Act, 1872, automatic forfeiture of a security deposit "
            "constitutes an impermissible penalty. A landlord is legally required to mitigate losses by re-letting and can only "
            "claim actual proven vacancy loss."
        ),
        "statutory_hook": "Section 74 Indian Contract Act, 1872 & Section 106 Transfer of Property Act, 1882",
        "whatsapp_rebuttal": (
            f"\"Dear Landlord, under Section 74 of the Indian Contract Act, 1872, automatic forfeiture of a security deposit "
            f"is legally void as an arbitrary penalty. The statutory residential notice under Section 106 Transfer of Property Act "
            f"is 15 days, and keys were accepted upon inspection without objection. As you have suffered no proven unlet vacancy loss, "
            f"withholding {amt_str} is legally unviable. Please process the refund.\""
        ),
    })

    # Pushback 3: Category-Specific Defense
    if any(k in reason_lower for k in ["business", "loss", "personal", "wedding", "loan"]):
        pushbacks.append({
            "title": "Tactic 3: Personal Financial Hardship (\"I have business losses right now\")",
            "landlord_message": (
                f"\"I am currently facing severe business losses and financial hardship. "
                f"I cannot return the deposit right now. You should cooperate as a human being.\""
            ),
            "legal_position": (
                "Under Indian Contract Act Section 73, a security deposit is held in fiduciary trust solely to secure "
                "tenancy covenants. A landlord's unrelated commercial or personal debts have zero legal nexus to the lease. "
                "Retaining deposit funds to offset personal financial crisis constitutes unjust enrichment."
            ),
            "statutory_hook": "Section 73 Indian Contract Act, 1872 (Fiduciary Nature of Deposit)",
            "whatsapp_rebuttal": (
                f"\"Dear Landlord, while I understand personal difficulties, under Section 73 of the Indian Contract Act, "
                f"a security deposit is held in trust exclusively for tenancy obligations. Personal or business losses have zero legal "
                f"connection to my tenancy and cannot be legally offset against my money. Please refund {amt_str} immediately.\""
            ),
        })
    elif any(k in reason_lower for k in ["society", "rwa", "penalty", "fine"]):
        pushbacks.append({
            "title": "Tactic 3: Building Society Fines (\"Society charged me a penalty for your flat\")",
            "landlord_message": (
                f"\"The society management committee imposed a ₹{case.deduction_amount_inr or 5000} fine for noise/by-law violations "
                f"during your stay. I had to pay it to the RWA.\""
            ),
            "legal_position": (
                "A landlord cannot deduct society fines without furnishing: (1) the official written RWA violation notice "
                "specifically naming the flat, and (2) the official stamped society payment receipt showing the fine was paid."
            ),
            "statutory_hook": "Section 73 Indian Contract Act, 1872 & Section 11 Model Tenancy Act, 2021",
            "whatsapp_rebuttal": (
                f"\"Dear Landlord, under Section 73 of the Contract Act, any deduction requires proof of actual loss. "
                f"Please provide: (1) the official RWA infraction notice naming our unit, (2) the stamped society payment receipt, "
                f"and (3) the lease clause authorizing this deduction. In the absence of these documents, please refund the full balance of {amt_str}.\""
            ),
        })
    elif any(k in reason_lower for k in ["paint", "repainting", "whitewash"]):
        pushbacks.append({
            "title": "Tactic 3: Mandatory Repainting (\"Agreement says painting is tenant's responsibility\")",
            "landlord_message": (
                f"\"Every tenant must pay for repainting the flat before leaving. "
                f"It took ₹{case.deduction_amount_inr or 15000} to whitewash and paint the walls for the new tenant.\""
            ),
            "legal_position": (
                "Under Indian tenancy jurisprudence and Section 73 of the Contract Act, ordinary fading and nail marks "
                "constitute normal wear and tear and are the owner's operational maintenance costs. Moreover, Section 11 MTA "
                "mandates genuine third-party GST invoices for any permitted repair deductions."
            ),
            "statutory_hook": "Section 73 Indian Contract Act, 1872 & Section 11 Model Tenancy Act, 2021",
            "whatsapp_rebuttal": (
                f"\"Dear Landlord, under Section 73 of the Indian Contract Act, normal paint fading constitutes reasonable wear and tear, "
                f"which is the owner's maintenance responsibility under Indian law. Furthermore, Section 11 of the Model Tenancy Act "
                f"prohibits deductions without actual contractor GST tax invoices and payment vouchers. Please furnish genuine vendor GST bills "
                f"or refund the deducted amount of {amt_str}.\""
            ),
        })
    else:
        pushbacks.append({
            "title": "Tactic 3: Unsubstantiated Deep Cleaning / Damage Claim",
            "landlord_message": (
                f"\"The flat was not left in clean condition. I had to hire deep cleaners and replace items. "
                f"That cost me {amt_str}, so I am retaining it.\""
            ),
            "legal_position": (
                "Section 11 of the Model Tenancy Act, 2021 mandates that any deduction from a security deposit must be "
                "substantiated by an itemized written explanation accompanied by actual expenditure receipts. Unilateral estimates "
                "without third-party vendor vouchers are legally invalid."
            ),
            "statutory_hook": "Section 11 Model Tenancy Act, 2021 & Section 73 Indian Contract Act, 1872",
            "whatsapp_rebuttal": (
                f"\"Dear Landlord, under Section 11 of the Model Tenancy Act and Section 73 ICA, any deduction requires an itemized written breakdown "
                f"and official contractor GST invoices/receipts for actual money spent. Without verifiable tax invoices and move-out inspection "
                f"records, unilateral retention is legally invalid. Please share the official GST receipts or refund {amt_str}.\""
            ),
        })

    return pushbacks
