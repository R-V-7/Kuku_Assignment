"""Generate objective, evaluation-conditioned legal notices and settlement agreements.

Conditioned on Layer 4 statutory evaluation via a Strict State Machine:
1. 'unjustified' (0% Proven): When deductions are arbitrary, personal losses, wear-and-tear repainting, or unevidenced.
   -> Generates 'FORMAL NOTICE FOR REFUND OF SECURITY DEPOSIT' (15-day demand notice demanding 100% full refund).
   -> Strictly zero concession language; never mentions conceding any charges or utility bills.
2. 'justified' (100% Proven): When all deductions are supported by genuine third-party tax invoices / meter bills for tenant-caused damage or arrears.
   -> Generates 'FORMAL WRITTEN ACKNOWLEDGEMENT & DEPOSIT SETTLEMENT RECORD' (closure & mutual discharge letter).
3. 'partial' (Mixed Evidence, >0% and <100% Proven): When some charges are documented with third-party invoices/bills but others are arbitrary/unproven.
   -> Generates 'FORMAL NOTICE FOR PARTIAL REFUND OF DISPUTED SECURITY DEPOSIT'.
   -> Concedes ONLY the specifically verified expenses that were documented; demands refund of the disputed remainder.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from models import CaseFacts


def _classify_with_llm(case: CaseFacts, client: Any) -> str | None:
    """Uses Gemini 3.5 Flash Lite to evaluate evidence under Section 11 MTA and Section 73 ICA."""
    facts_str = f"Landlord Stated Reason: {case.deduction_reason or 'None'}\n"
    if case.deduction_amount_inr:
        facts_str += f"Deduction Amount: ₹{case.deduction_amount_inr:,}\n"
    if case.other_details:
        facts_str += f"Reported Details: {'; '.join(case.other_details)}\n"

    prompt = f"""You are a specialized legal classification model for Indian residential rental deposit disputes.
Evaluate the following case facts under Section 11 of the Model Tenancy Act, 2021 and Section 73 of the Indian Contract Act, 1872.

STRICT CLASSIFICATION CRITERIA:
1. "justified" (100% Proven):
   - The landlord has furnished verified third-party documentation (such as official contractor GST tax invoices, official company receipts, or utility meter bills) for admitted tenant-caused damage or actual utility arrears.
   - ZERO arbitrary, personal (e.g. business losses), or routine wear-and-tear deductions are claimed.

2. "partial" (Mixed Evidence):
   - Part of the deduction is backed by genuine third-party receipts/bills, but another part is arbitrary, personal, or unsubstantiated.

3. "unjustified" (0% Proven):
   - The landlord provided zero third-party receipts, GST invoices, or utility bills.
   - Or the deduction is for routine wear-and-tear (e.g. repainting without GST bills), or unrelated personal hardship (e.g. business losses, wedding expenses, personal loans).

Case Facts:
{facts_str}

Return strictly a JSON object with this format:
{{"posture": "justified" | "partial" | "unjustified", "rationale": "one-sentence explanation"}}
"""
    if callable(getattr(client, "generate_json", None)):
        resp = client.generate_json(prompt, {"type": "object"}).text.strip()
    else:
        resp = client.generate_text(prompt).text.strip()

    if resp.startswith("```") and resp.endswith("```"):
        resp = "\n".join(resp.splitlines()[1:-1]).strip()

    data = json.loads(resp)
    posture = str(data.get("posture", "")).strip().lower()
    if posture in ("justified", "partial", "unjustified"):
        return posture
    return None


def _classify_posture_heuristics(case: CaseFacts, evaluation_text: str = "") -> str:
    """Strict State Machine classifying dispute posture into 'unjustified', 'justified', or 'partial'.

    Routing is based strictly on the proportion of proven vs unproven deductions:
    - 'unjustified' (0% Proven): Landlord provided zero verifiable third-party receipts/invoices,
      or claimed deductions are entirely arbitrary (e.g. personal business losses, wear & tear painting).
    - 'justified' (100% Proven): Landlord provided verified third-party documentation (GST invoices,
      meter bills) for tenant-caused damage or unpaid utilities, with zero unproven claims.
    - 'partial' (Mixed Evidence, >0% and <100% Proven): Landlord proved some expenses with third-party
      invoices, but other claimed deductions remain arbitrary or unsubstantiated.
    """
    # 1. Fact-based proof extraction (strictly from case intake facts, NOT statutory evaluation text)
    facts_text = (
        (case.deduction_reason or "") + " "
        + " ".join(case.other_details or [])
    ).lower()

    # Evidence that official third-party invoices/bills were actually furnished/sent
    proof_indicators = [
        "gst invoice", "gst bill", "tax invoice", "meter bill", "electricity meter bill",
        "official invoice", "official receipt", "official bill", "bills on whatsapp",
        "bill on whatsapp", "invoice on whatsapp", "receipt on whatsapp", "sent invoice",
        "sent bill", "sent receipt", "provided invoice", "provided bill", "provided receipt",
        "carpenter gst", "carpenter invoice", "contractor invoice", "paid receipt"
    ]
    has_verified_proof = any(k in facts_text for k in proof_indicators)

    # Negative evidence: explicitly stating no bills or receipts were provided
    negative_proof_indicators = [
        "no receipt", "no bill", "no invoice", "without receipt", "without invoice",
        "no proof", "refused to provide", "refused bills", "no society letter",
        "arbitrary deduction"
    ]
    has_negative_proof = any(k in facts_text for k in negative_proof_indicators)
    if has_negative_proof:
        has_verified_proof = False

    # 2. Legitimate heads: tenant-caused damage or accepted utility arrears
    tenant_damage_or_arrears_indicators = [
        "overflowing sink", "left sink overflowing", "water damage", "accidental",
        "broken", "damage caused", "meter bill", "electricity bill", "water bill",
        "utility bill", "pending bill", "unpaid bill", "repair"
    ]
    has_tenant_fault_or_arrears = any(k in facts_text for k in tenant_damage_or_arrears_indicators)

    # 3. Arbitrary, personal, or unevidenced heads (inherently 0% justified)
    arbitrary_indicators = [
        "business loss", "business losses", "personal", "wedding", "market",
        "loan", "crisis", "financial difficulty", "afford", "arbitrary",
        "fine without receipt", "penalty without receipt"
    ]
    has_arbitrary_claims = any(k in facts_text for k in arbitrary_indicators)

    # Routine maintenance that is landlord's obligation unless explicitly evidenced
    routine_wear_indicators = [
        "painting", "whitewash", "white wash", "repainting", "deep clean", "cleaning"
    ]
    has_routine_wear = any(k in (case.deduction_reason or "").lower() for k in routine_wear_indicators)

    # Evaluation signals from Layer 4
    eval_lower = evaluation_text.lower() if evaluation_text else ""
    eval_impermissible = any(
        k in eval_lower
        for k in [
            "zero legal connection", "cannot deduct for business losses",
            "impermissible", "unjust enrichment", "not permissible"
        ]
    )

    # Strict State Machine Routing:
    # -------------------------------------------------------------
    # State 1: 100% Proven -> 'justified'
    # Must have verified proof AND legitimate damage/arrears AND zero arbitrary claims
    if has_verified_proof and has_tenant_fault_or_arrears and not has_arbitrary_claims and not has_routine_wear and not eval_impermissible:
        return "justified"

    # State 2: Mixed Evidence (>0% and <100% Proven) -> 'partial'
    # Has verified proof for some item, but also arbitrary claims or unevidenced deductions
    if has_verified_proof and (has_arbitrary_claims or has_routine_wear or eval_impermissible):
        return "partial"

    # State 3: 0% Proven -> 'unjustified'
    # No verified proof, or pure arbitrary deductions (business losses, wear & tear painting, etc.)
    return "unjustified"


def classify_dispute_posture(
    case: CaseFacts, evaluation_text: str = "", client: Any | None = None
) -> str:
    """Hybrid Classifier: Uses Gemini 3.5 Flash Lite if an active LLM client is available

    to semantically evaluate the case facts, with an instant deterministic heuristic
    state machine fallback.
    """
    if client is not None:
        try:
            llm_result = _classify_with_llm(case, client)
            if llm_result in ("justified", "partial", "unjustified"):
                return llm_result
        except Exception:
            pass  # Seamless fallback to heuristic state machine

    return _classify_posture_heuristics(case, evaluation_text)


def _extract_verified_expenses_summary(case: CaseFacts) -> str:
    """Extract a factual, human-readable summary of specifically verified expenses from case facts."""
    facts = ((case.deduction_reason or "") + " " + " ".join(case.other_details or [])).lower()
    verified_items: list[str] = []
    if any(k in facts for k in ["meter bill", "electricity", "utility", "water bill"]):
        verified_items.append("the verified utility charges supported by the official meter bill")
    if any(k in facts for k in ["gst", "carpenter", "repair", "contractor", "damage"]):
        verified_items.append("the actual repair expenses supported by vendor GST tax invoice")
    if not verified_items:
        verified_items.append("the documented expenses supported by verified third-party receipts")
    return " and ".join(verified_items)


def generate_demand_letter(
    case: CaseFacts,
    tenant_name: str = "[Tenant Name]",
    landlord_name: str = "[Landlord Name]",
    property_address: str = "",
    notice_date: str = "",
    bank_details: str = "[Your Bank Name, Account Number, IFSC Code or UPI ID]",
    retrieved_chunks: list[dict[str, Any]] | None = None,
    evaluation_text: str | None = None,
    posture: str | None = None,
) -> str:
    """Generate an objective, evaluation-conditioned legal correspondence.

    Postures:
    - 'unjustified' (0% Proven): Formal Notice for Refund of Security Deposit (15-Day Demand Notice)
      Demands 100% full refund with strictly zero concession language.
    - 'justified' (100% Proven): Formal Written Acknowledgement & Deposit Settlement Record
      Mutual discharge and lease closure acknowledging verified invoices.
    - 'partial' (Mixed Evidence): Formal Notice for Partial Refund of Disputed Security Deposit
      Concedes only the specifically verified expenses and disputes the unproven remainder.
    """
    if posture is None:
        posture = classify_dispute_posture(case, evaluation_text or "")

    today_str = (
        notice_date.strip()
        if notice_date.strip()
        else date.today().strftime("%d %B %Y")
    )
    t_name = tenant_name.strip() if tenant_name.strip() else "[Tenant Name]"
    l_name = landlord_name.strip() if landlord_name.strip() else "[Landlord Name]"

    loc_parts = [p for p in [case.city, case.state] if p]
    loc_str = ", ".join(loc_parts) if loc_parts else "[City, State]"
    addr_str = (
        property_address.strip()
        if property_address.strip()
        else f"Premises situated at {loc_str}"
    )

    dep_amt = (
        f"₹{case.deposit_amount_inr:,}"
        if case.deposit_amount_inr is not None
        else "[Deposit Amount in ₹]"
    )
    ret_amt = (
        f"₹{case.amount_returned_inr:,}"
        if case.amount_returned_inr is not None
        else "₹0"
    )

    if case.deposit_amount_inr is not None:
        ret_val = (
            case.amount_returned_inr if case.amount_returned_inr is not None else 0
        )
        bal_val = max(0, case.deposit_amount_inr - ret_val)
        bal_amt = f"₹{bal_val:,}"
    else:
        bal_amt = "[Outstanding Deposit Amount in ₹]"

    ded_amt_str = (
        f"₹{case.deduction_amount_inr:,}"
        if case.deduction_amount_inr is not None
        else (bal_amt if bal_amt != "[Outstanding Deposit Amount in ₹]" else "an unspecified amount")
    )

    move_out = case.move_out_date if case.move_out_date else "[Move-out Date]"

    # Wording based on tri-state written agreement
    if case.written_agreement_exists == "yes":
        agreement_clause = (
            "The tenancy was governed by a written rental agreement executed between us."
        )
    elif case.written_agreement_exists == "no":
        agreement_clause = (
            "The tenancy was established under an oral tenancy agreement with mutual terms."
        )
    else:
        agreement_clause = (
            "The tenancy was mutually established and recognized between both parties."
        )

    # Wording based on tri-state payment proof
    if case.payment_proof_exists == "yes":
        proof_clause = (
            f"The payment of the security deposit of {dep_amt} was made upon commencement "
            "and is evidenced by verified transaction records / receipts."
        )
    elif case.payment_proof_exists == "no":
        proof_clause = (
            f"The security deposit of {dep_amt} was duly paid at the commencement of the tenancy."
        )
    else:
        proof_clause = (
            f"The agreed security deposit of {dep_amt} was tendered to you upon commencing the tenancy."
        )

    # Statutory references from retrieved chunks
    if retrieved_chunks:
        stat_cites = "; ".join(
            f"{c.get('section', '')} of the {c.get('act', '')} ({c.get('title', '')})"
            for c in retrieved_chunks
        )
    else:
        stat_cites = "Section 11 of the Model Tenancy Act, 2021 and Section 73 of the Indian Contract Act, 1872"

    facts_text = (
        (case.deduction_reason or "") + " "
        + " ".join(case.other_details or [])
    ).lower()

    # =========================================================================
    # POSTURE 1: FULLY JUSTIFIED (100% Proven -> Settlement & Tenancy Discharge)
    # =========================================================================
    if posture == "justified":
        doc_title = "FORMAL WRITTEN ACKNOWLEDGEMENT & DEPOSIT SETTLEMENT RECORD"
        subject_line = "Subject: Acknowledgement of Deposit Accounting, Receipt of Invoices, and Tenancy Discharge"

        invoices_received = []
        if any(k in facts_text for k in ["meter bill", "electricity", "utility", "water bill"]):
            invoices_received.append("official utility electricity meter bill")
        if any(k in facts_text for k in ["gst", "carpenter", "repair", "contractor", "damage"]):
            invoices_received.append("official contractor/repair GST tax invoice")
        if not invoices_received:
            invoices_received.append("itemized repair bills and expenditure receipts")

        invoices_str = " and ".join(invoices_received)

        notice = f"""{doc_title}

Date: {today_str}

To,
{l_name}
(Landlord / Property Owner)
Property: {addr_str}

From,
{t_name}
(Former Tenant)
Contact: [Tenant Phone / Email]

{subject_line}

Dear {l_name},

I am writing regarding the residential premises situated at:
{addr_str}.

I peacefully vacated and handed over possession of the premises on {move_out}. {agreement_clause}

1. SECURITY DEPOSIT ACCOUNTING:
{proof_clause}
Upon move-out inspection, the security deposit of {dep_amt} was reconciled as follows:
- Amount Refunded to Tenant: {ret_amt}
- Withheld Deductions: {ded_amt_str} for {case.deduction_reason or 'the documented repairs and charges'}

2. RECEIPT & VERIFICATION OF VENDOR INVOICES:
I hereby formally acknowledge receipt and inspection of the supporting documentation furnished by you, specifically the {invoices_str}. These documents confirm that the expenditure incurred was for actual, verifiable repairs and pending utility consumption directly attributable to the tenancy.

3. STATUTORY ALIGNMENT & LEGAL POSITION:
Under applicable statutory principles, specifically {stat_cites}, deductions from a security deposit are legally permissible when they correspond to unpaid utilities and agreed repairs supported by genuine third-party tax invoices and itemized expenditure receipts. As you have provided verifiable third-party tax invoices and payment vouchers, the deductions satisfy statutory requirements.

4. FULL & FINAL SETTLEMENT & MUTUAL DISCHARGE:
In view of the valid documentation provided, I accept the adjusted deduction of {ded_amt_str} towards the said expenses. 

With the refund of {ret_amt} already received, the security deposit account for the tenancy stands fully reconciled, settled, and closed. Both parties are hereby mutually discharged from any further monetary, legal, or tenancy claims in respect of the subject premises.

Thank you for your cooperation during the tenancy.

Sincerely,

{t_name}
(Former Tenant)
"""

    # =========================================================================
    # POSTURE 2: PARTIALLY JUSTIFIED (Mixed Evidence -> Partial Refund Demand)
    # =========================================================================
    elif posture == "partial":
        doc_title = "FORMAL NOTICE FOR PARTIAL REFUND OF DISPUTED SECURITY DEPOSIT"
        subject_line = "Subject: Demand for Refund of Disputed Deductions under Tenancy Agreement"
        verified_expenses_str = _extract_verified_expenses_summary(case)

        notice = f"""{doc_title}

Date: {today_str}

To,
{l_name}
(Landlord / Property Owner)
Property: {addr_str}

From,
{t_name}
(Former Tenant)
Contact: [Tenant Phone / Email]

{subject_line}

Dear {l_name},

I am issuing this formal notice regarding the residential premises situated at:
{addr_str}.

I peacefully vacated and handed over possession of the premises on {move_out}. {agreement_clause}

1. TENANCY PARTICULARS & DEPOSIT ACCOUNTING:
{proof_clause}
To date, you have returned {ret_amt} from the initial deposit of {dep_amt}, while retaining {ded_amt_str} citing '{case.deduction_reason}'.

2. CONCESSION OF SPECIFICALLY VERIFIED CHARGES:
I have reviewed the supporting documentation provided and concede only {verified_expenses_str}.

3. DISPUTE OF UNJUSTIFIED / UNPROVEN DEDUCTIONS:
However, the remaining deductions claimed by you lack contractual basis, are not substantiated by genuine tax invoices, or represent unrelated personal expenses / normal wear and tear. Under applicable law, specifically {stat_cites}, a landlord cannot unilaterally retain deposit funds without proof of actual, quantifiable damage resulting from tenant breach beyond reasonable wear and tear.

4. FORMAL DEMAND:
You are hereby called upon to refund the disputed balance within 15 (fifteen) days from receipt of this notice to the following account:
Payment Details: {bank_details}

Failing this, I reserve the right to seek recovery of the unjustified withholding before the competent Rent Authority, Consumer Disputes Redressal Commission, or approach DLSA / Lok Adalat for resolution.

Sincerely,

{t_name}
(Former Tenant)
"""

    # =========================================================================
    # POSTURE 3: UNJUSTIFIED (0% Proven -> 15-Day Demand Notice for 100% Refund)
    # =========================================================================
    else:
        doc_title = "FORMAL NOTICE FOR REFUND OF SECURITY DEPOSIT"
        subject_line = f"Subject: Formal Demand for Immediate Refund of Outstanding Security Deposit of {bal_amt}"

        if case.deduction_reason:
            deduction_clause = (
                f"You have purportedly withheld/deducted {ded_amt_str} citing '{case.deduction_reason}'. "
                f"Please take note that under applicable law, specifically {stat_cites}, "
                "a security deposit is held in trust solely to secure against tenant breach or damage beyond reasonable wear and tear. "
                "Arbitrary deductions without providing itemized repair bills, GST invoices, and prior joint inspection records "
                "are legally impermissible and constitute unjust retention of funds."
            )
        else:
            deduction_clause = (
                "You have failed to refund the security deposit within a reasonable time following vacant possession "
                "and handover of the premises in tenantable order, without providing any lawful justification or itemized bills."
            )

        legal_position_clause = (
            f"Under applicable Indian statutes, specifically {stat_cites}, "
            "a landlord is legally required to return the security deposit promptly upon vacant handover, subject only to "
            "demonstrable, itemized actual loss beyond reasonable wear and tear. Unilateral deductions without documentary "
            "proof and verified invoices amount to breach of trust and unlawful retention of tenant funds."
        )

        notice = f"""{doc_title}

Date: {today_str}

To,
{l_name}
(Landlord / Property Owner)
Property: {addr_str}

From,
{t_name}
(Former Tenant)
Contact: [Tenant Phone / Email]

{subject_line}

Dear {l_name},

I am issuing this formal demand notice regarding the residential premises situated at:
{addr_str}.

1. TENANCY PARTICULARS:
I was residing as a tenant at the above-mentioned premises and peacefully handed over vacant possession upon moving out on {move_out}. {agreement_clause}

2. SECURITY DEPOSIT ACCOUNTING:
{proof_clause}
To date, you have returned {ret_amt}, leaving an unpaid deposit balance of {bal_amt}.

3. UNJUSTIFIED WITHHOLDING / DEDUCTIONS:
{deduction_clause}

4. LEGAL POSITION:
{legal_position_clause}

5. FORMAL DEMAND:
You are hereby called upon to refund the outstanding sum of {bal_amt} within 15 (fifteen) days from the receipt of this notice, payable to the following bank account / UPI ID:
Payment Details: {bank_details}

In the event of failure to refund the said sum within 15 days, I shall be constrained to initiate formal legal remedies before the competent Rent Authority, Civil Court, Consumer Disputes Redressal Commission, or approach the District Legal Services Authority (DLSA) / Lok Adalat for recovery, holding you liable for all legal expenses, damages, and statutory interest.

Sincerely,

{t_name}
(Former Tenant)
"""

    if retrieved_chunks:
        try:
            from rag.firewall import CitationFirewall
            sanitized_notice, _, _ = CitationFirewall.audit_and_sanitize(notice, retrieved_chunks)
            return sanitized_notice
        except Exception:
            pass

    return notice
