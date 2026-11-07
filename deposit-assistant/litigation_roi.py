"""Dispute Resolution Expected Value (EV) & Litigation ROI Calculator for Indian Tenancy Claims.

Evaluates cost, duration, forum suitability, and statutory interest accrual under:
- Legal Services Authorities Act, 1987 (NALSA / DLSA Pre-Litigation Lok Adalat)
- Consumer Protection Act, 2019 (e-Daakhil District Consumer Commission)
- Model Tenancy Act, 2021 (Rent Authority / Rent Court)
- Interest Act, 1978 & Code of Civil Procedure, 1908 (Order 37 Summary Suit)
"""

from datetime import datetime, timezone
from typing import Any
from models import CaseFacts
from draft import classify_dispute_posture


def calculate_litigation_roi(case: CaseFacts, posture: str | None = None) -> dict[str, Any]:
    """Computes dispute resolution ROI, recommends the optimal Indian legal forum,

    and calculates accrued statutory interest on the withheld deposit.
    """
    if posture is None:
        posture = classify_dispute_posture(case)

    # 1. Determine effective disputed amount
    if case.deduction_amount_inr is not None and case.deduction_amount_inr > 0:
        disputed_amount = case.deduction_amount_inr
    elif case.deposit_amount_inr is not None and case.amount_returned_inr is not None:
        disputed_amount = max(0, case.deposit_amount_inr - case.amount_returned_inr)
    elif case.deposit_amount_inr is not None:
        disputed_amount = case.deposit_amount_inr
    else:
        disputed_amount = 0

    # 2. Case Posture Check: Justified cases have 0 litigation ROI
    if posture == "justified":
        return {
            "disputed_amount_inr": 0,
            "statutory_interest_inr": 0,
            "total_claimable_inr": 0,
            "roi_tier": "NOT_RECOMMENDED",
            "verdict": "Litigation Negative / Claim Substantiated",
            "recommended_forum": "Mutual Settlement & Out-of-Court Discharge",
            "forum_authority": "Direct Landlord Reconciliation",
            "court_fee_display": "₹0",
            "lawyer_fee_advice": "Do NOT hire a lawyer; dispute is substantiated by landlord receipts.",
            "estimated_duration": "Immediate",
            "expected_net_recovery": "₹0 (Deduction Legally Valid)",
            "statutory_rate_pct": 0.0,
            "summary": (
                "The landlord has satisfied the statutory burden of proof under Section 11 MTA by producing "
                "contractor tax invoices for admitted damage. Pursuing legal escalation carries a negative return "
                "and risks dismissal with costs. Mutual settlement is strongly advised."
            ),
            "forum_matrix": [],
        }

    # 3. Calculate Statutory Interest (Default 8.0% p.a. simple interest under Interest Act, 1978)
    annual_rate = 8.0
    months_elapsed = 6  # standard default statutory default window

    if case.move_out_date:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                mo_dt = datetime.strptime(case.move_out_date.strip(), fmt)
                now_dt = datetime.now()
                diff_days = max(30, (now_dt - mo_dt).days)
                # Interest kicks in after 30-day statutory grace period
                interest_days = max(0, diff_days - 30)
                months_elapsed = max(1, round(interest_days / 30))
                break
            except Exception:
                continue

    interest_amount = int(round(disputed_amount * (annual_rate / 100.0) * (months_elapsed / 12.0)))
    total_claimable = disputed_amount + interest_amount

    # 4. Forum Recommendation Matrix based on Economic Tiers
    if disputed_amount < 15000:
        # Micro Dispute (< ₹15,000)
        roi_tier = "ZERO_COST_ESCALATION"
        verdict = "Zero-Cost Informal Conciliation (High Net ROI)"
        recommended_forum = "NALSA / DLSA Pre-Litigation Lok Adalat"
        forum_authority = "District Legal Services Authority (DLSA)"
        court_fee_display = "₹0 (Completely Free)"
        lawyer_fee_advice = "DO NOT hire a private advocate. Private lawyer fees (₹15,000+) exceed your claim value."
        estimated_duration = "30 – 60 Days"
        expected_net_recovery = f"₹{disputed_amount:,} (100% Net Recovery)"
        summary = (
            f"For a dispute of ₹{disputed_amount:,}, hiring a private lawyer produces a negative financial ROI. "
            "Under the Legal Services Authorities Act, 1987, DLSA Pre-Litigation Lok Adalat is free of court fees, "
            "requires no lawyers, and yields a binding settlement enforceable as a civil court decree."
        )
    elif disputed_amount <= 60000:
        # Mid-Range Dispute (₹15,000 – ₹60,000)
        roi_tier = "FAVORABLE_CONSUMER_COMMISSION"
        verdict = "Self-Filed e-Daakhil Consumer Complaint (High ROI)"
        recommended_forum = "e-Daakhil (District Consumer Disputes Redressal Commission)"
        forum_authority = "Consumer Commission (CPA 2019)"
        court_fee_display = "₹0 (Zero Court Fee for claims under ₹5 Lakh)"
        lawyer_fee_advice = "Self-file online without an advocate. The e-Daakhil portal permits self-representation."
        estimated_duration = "3 – 6 Months"
        expected_net_recovery = f"₹{total_claimable:,} (Principal + Interest)"
        summary = (
            f"A disputed claim of ₹{disputed_amount:,} is ideally suited for self-filing on the Ministry of Consumer "
            "Affairs' e-Daakhil portal. Under the Consumer Protection Rules, 2020, claims up to ₹5,00,000 are 100% "
            "exempt from court fees. Rental housing services fall within consumer jurisdiction."
        )
    else:
        # High-Value Dispute (> ₹60,000)
        roi_tier = "SUBSTANTIAL_CLAIM_MULTI_FORUM"
        verdict = "Rent Authority / Summary Civil Suit (Strong Positive ROI)"
        recommended_forum = "Rent Authority (Model Tenancy Act) / Summary Civil Suit (Order 37 CPC)"
        forum_authority = "Rent Court / Civil Judge Senior Division"
        court_fee_display = "Nominal State Court Fees (~₹1,000 – ₹3,000)"
        lawyer_fee_advice = "Can engage legal counsel or file via DLSA appointed panel advocate."
        estimated_duration = "4 – 12 Months"
        expected_net_recovery = f"₹{total_claimable:,} (Principal + Accrued Statutory Interest)"
        summary = (
            f"With ₹{disputed_amount:,} withheld, formal legal escalation yields a strongly positive financial return. "
            "Under Section 11 of the Model Tenancy Act, the Rent Authority possesses summary jurisdiction to penalize "
            "unauthorized withholding. Alternatively, an Order 37 CPC summary suit for debt recovery can be instituted."
        )

    # 5. Comparative Forum Matrix
    forum_matrix = [
        {
            "forum": "1. WhatsApp / Registered Post Demand Notice",
            "cost": "₹0 – ₹100",
            "duration": "15 Days",
            "court_fee": "₹0",
            "suitability": "Mandatory first step before any formal filing.",
            "status": "ACTIVE_STEP",
        },
        {
            "forum": "2. DLSA Pre-Litigation Lok Adalat",
            "cost": "₹0",
            "duration": "1 – 2 Months",
            "court_fee": "₹0 (Legal Services Authorities Act §21)",
            "suitability": "Best for ₹0 legal spend with legally binding settlement decree.",
            "status": "RECOMMENDED" if disputed_amount < 25000 else "VIABLE",
        },
        {
            "forum": "3. e-Daakhil Consumer Commission",
            "cost": "₹100 (Affidavit)",
            "duration": "3 – 6 Months",
            "court_fee": "₹0 (Exempt under ₹5 Lakh)",
            "suitability": "Best for self-representation against stubborn landlords.",
            "status": "RECOMMENDED" if 15000 <= disputed_amount <= 60000 else "VIABLE",
        },
        {
            "forum": "4. Rent Authority / Civil Suit",
            "cost": "₹2,000 – ₹10,000",
            "duration": "4 – 12 Months",
            "court_fee": "State Ad Valorem Fee",
            "suitability": "Best for high-value deposits (>₹60,000) with substantial damages.",
            "status": "RECOMMENDED" if disputed_amount > 60000 else "OPTIONAL",
        },
    ]

    return {
        "disputed_amount_inr": disputed_amount,
        "statutory_interest_inr": interest_amount,
        "months_elapsed": months_elapsed,
        "statutory_rate_pct": annual_rate,
        "total_claimable_inr": total_claimable,
        "roi_tier": roi_tier,
        "verdict": verdict,
        "recommended_forum": recommended_forum,
        "forum_authority": forum_authority,
        "court_fee_display": court_fee_display,
        "lawyer_fee_advice": lawyer_fee_advice,
        "estimated_duration": estimated_duration,
        "expected_net_recovery": expected_net_recovery,
        "summary": summary,
        "forum_matrix": forum_matrix,
    }


__all__ = ["calculate_litigation_roi"]
