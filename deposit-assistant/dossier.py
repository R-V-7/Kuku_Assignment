"""One-Click e-Daakhil / DLSA Pre-Litigation Court Dossier Compiler.

Generates a structured, court-ready complaint packet for self-filing in Indian forums:
- e-Daakhil Portal (Consumer Protection Act, 2019)
- DLSA Pre-Litigation Lok Adalat (Legal Services Authorities Act, 1987)
- Rent Authority (Model Tenancy Act, 2021)
"""

from datetime import datetime
from models import CaseFacts
from draft import classify_dispute_posture
from litigation_roi import calculate_litigation_roi


def compile_court_dossier(case: CaseFacts, posture: str | None = None) -> str:
    """Compiles a complete, formatted court filing dossier (List of Dates, Statutory Grounds,

    Prayer, and Index of Annexures) for DLSA Lok Adalat or e-Daakhil Consumer Commission.
    """
    if posture is None:
        posture = classify_dispute_posture(case)

    # If the case is fully justified, compile a Mutual Settlement Discharge Dossier
    if posture == "justified":
        return _compile_settlement_discharge_dossier(case)

    return _compile_contested_filing_dossier(case, posture)


def _compile_settlement_discharge_dossier(case: CaseFacts) -> str:
    """Compiles an Accord & Satisfaction Discharge Dossier when landlord furnished valid invoices."""
    city = case.city or "the designated city"
    state = case.state or "the designated state"
    deposit_amt = f"₹{case.deposit_amount_inr:,}" if case.deposit_amount_inr else "the security deposit"
    refund_amt = f"₹{case.amount_returned_inr:,}" if case.amount_returned_inr else "the balance deposit"
    deduction_amt = f"₹{case.deduction_amount_inr:,}" if case.deduction_amount_inr else "the agreed deduction"
    reason = case.deduction_reason or "approved repairs and utility charges"
    today = datetime.now().strftime("%d %B %Y")

    return f"""# TENANCY DISCHARGE & MUTUAL SETTLEMENT DOSSIER
**Jurisdiction:** {city.title()}, {state.title()}  
**Governing Provisions:** Section 63, Indian Contract Act, 1872 (Accord & Satisfaction) & Section 11, Model Tenancy Act, 2021  
**Date of Execution:** {today}  

---

### 1. SUMMARY OF SETTLEMENT
1. **Tenancy Premise:** Leased residential accommodation in {city.title()}, {state.title()}.
2. **Total Security Deposit Custody:** {deposit_amt}.
3. **Verified Deductions Accounted:** {deduction_amt} for {reason}, substantiated by genuine third-party contractor GST invoices and verified meter vouchers.
4. **Net Amount Refunded to Tenant:** {refund_amt}.
5. **Settlement Posture:** Full and Final Accord and Satisfaction. Neither party possesses further civil claims or liabilities.

---

### 2. CHRONOLOGY OF SETTLEMENT
* **Deposit Inception:** Tenant remitted {deposit_amt} as security deposit pursuant to residential tenancy.
* **Vacating & Handover:** Premises surrendered on {case.move_out_date or 'tenancy conclusion'} in satisfactory condition, subject to ordinary wear and tear.
* **Account Reconciliation:** Landlord furnished third-party tax invoices under Section 11 MTA, 2021 detailing repair costs of {deduction_amt}.
* **Final Disbursement:** Landlord disbursed balance sum of {refund_amt} to Tenant. Accounts stand reconciled and settled.

---

### 3. INDEX OF DISCHARGE ANNEXURES
* **Annexure S-1:** Copy of Lease/Rental Agreement.
* **Annexure S-2:** Electronic Banking Record / UPI receipt confirming initial deposit remittance (BSA 2023 §61).
* **Annexure S-3:** Landlord's Contractor GST Invoices & Utility Vouchers (Section 11 MTA compliance).
* **Annexure S-4:** Bank / UPI Credit Advice of {refund_amt} into Tenant's account.

---
**Verified & Closed:** Both parties acknowledge that no pending dispute exists before any Civil Court, Rent Authority, or Consumer Redressal Commission.
"""


def _compile_contested_filing_dossier(case: CaseFacts, posture: str) -> str:
    """Compiles a complete court/consumer commission petition dossier."""
    city = case.city or "the designated city"
    state = case.state or "the designated state"
    deposit_amt = f"₹{case.deposit_amount_inr:,}" if case.deposit_amount_inr else "Unstated"
    refund_amt = f"₹{case.amount_returned_inr:,}" if case.amount_returned_inr is not None else "₹0"
    deduction_amt = f"₹{case.deduction_amount_inr:,}" if case.deduction_amount_inr else "the withheld deposit"
    reason = case.deduction_reason or "unsubstantiated claims"
    today = datetime.now().strftime("%d %B %Y")
    move_out = case.move_out_date or "the conclusion of tenancy"

    # Fetch litigation ROI data for interest calculations
    roi_data = calculate_litigation_roi(case, posture=posture)
    interest_amt = f"₹{roi_data['statutory_interest_inr']:,}"
    total_claim = f"₹{roi_data['total_claimable_inr']:,}"

    return f"""# PRE-LITIGATION CASE DOSSIER & COMPLAINT PETITION

**BEFORE THE HON'BLE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION /**  
**BEFORE THE SECRETARY, DISTRICT LEGAL SERVICES AUTHORITY (DLSA)**  
**AT {city.upper()}, {state.upper()}**

---

### IN THE MATTER OF:
**TENANT / COMPLAINANT**  
*(Details as per Lease Agreement)*  
`... COMPLAINANT`

**VERSUS**

**LANDLORD / OPPOSITE PARTY**  
*(Property Owner / Lessor)*  
`... OPPOSITE PARTY`

---

## 1. SYNOPSIS & LIST OF DATES AND EVENTS

| Date | Event / Fact | Statutory Nexus |
| :--- | :--- | :--- |
| **Tenancy Inception** | Complainant entered into residential tenancy in {city.title()}, {state.title()} and transferred {deposit_amt} as refundable security deposit. | Section 10, Indian Contract Act, 1872 & Section 61, Bharatiya Sakshya Adhiniyam, 2023 |
| **{move_out}** | Complainant lawfully vacated premises and peacefully surrendered keys following joint handover. | Section 108(q), Transfer of Property Act, 1882 |
| **+30 Days Post-Exit** | Statutory 30-day refund window elapsed. Opposite Party failed to return full deposit or tender itemized GST invoices. | Section 11, Model Tenancy Act, 2021 |
| **Dispute Date** | Opposite Party unilaterally withheld {deduction_amt} under the pretext of '{reason}', without supplying third-party contractor tax invoices. | Section 73 & 74, Indian Contract Act, 1872 |
| **Notice Served** | Complainant served formal 15-day statutory demand notice requesting refund or production of genuine GST bills. | Consumer Protection Act, 2019 §2(11) |
| **Present Date** | Opposite Party failed to comply. Present complaint/conciliation petition instituted for recovery of {total_claim}. | Section 21, Legal Services Authorities Act, 1987 |

---

## 2. STATUTORY GROUNDS & STATEMENT OF CLAIM

1. **Unilateral Breach of Contract (Section 73, Indian Contract Act, 1872):**  
   The security deposit was delivered in trust solely to guarantee tenancy covenants. A landlord cannot unilaterally deduct funds for '{reason}' without proving actual, non-remote financial injury through certified receipts.

2. **Violation of Statutory Notice and Billing Mandate (Section 11, Model Tenancy Act, 2021):**  
   Section 11 strictly mandates that any deduction must be substantiated with itemized accounts and actual expenditure bills. In the absence of third-party contractor GST invoices, withholding constitutes an arbitrary penalty barred under Section 74 of the ICA.

3. **Admissibility of Electronic Records (Section 61, Bharatiya Sakshya Adhiniyam, 2023):**  
   The Complainant substantiates all financial transactions (deposit transfer of {deposit_amt} and partial return of {refund_amt}) through bank account statements and UPI transaction logs, forming admissible primary electronic evidence.

4. **Deficiency of Service (Section 2(11), Consumer Protection Act, 2019):**  
   The arbitrary retention of tenancy deposits by a landlord constitutes an unfair practice and deficiency in service, entitling the consumer to restitution and compensation.

---

## 3. PRAYER & RELIEF SOUGHT

WHEREFORE, the Complainant respectfully prays that this Hon'ble Authority / Commission may be pleased to:

* **A. Direct the Opposite Party** to immediately refund the unlawfully withheld principal sum of **{deduction_amt}** to the Complainant.
* **B. Award Statutory Interest** of **{interest_amt}** (calculated @ 8% p.a. from expiry of 30 days post move-out till actual realization) under the Interest Act, 1978.
* **C. Grant Reasonable Litigation Costs & Nominal Compensation** of ₹5,000/- for mental harassment and unjust deprivation of hard-earned funds.
* **D. Pass any other order(s)** deemed just and equitable in the interest of justice.

---

## 4. INDEX OF ANNEXURES (FILING CHECKLIST)

| Annexure No. | Document Description | Evidentiary Purpose |
| :---: | :--- | :--- |
| **Annexure C-1** | Copy of Signed Lease / Tenancy Agreement (or statement of oral tenancy terms). | Proves contractual relationship and agreed refund covenants. |
| **Annexure C-2** | Certified Bank Statement / UPI Transaction Log of deposit debit. | Primary electronic evidence under BSA 2023 §61 proving deposit remittance. |
| **Annexure C-3** | Move-Out Inspection Record / WhatsApp Key Handover Confirmation. | Confirms peaceful surrender without contemporaneous objection. |
| **Annexure C-4** | Copy of 15-Day Statutory Legal Demand Notice served on Landlord. | Proves pre-litigation notice requirement was satisfied. |
| **Annexure C-5** | Proof of Service (India Post Registered AD Tracking / WhatsApp Delivery). | Establishes delivery and opposite party's default. |

---

### 5. VERIFICATION
I, the Complainant above-named, do hereby verify and state that the contents of paragraphs 1 to 4 above are true and correct to my personal knowledge and belief derived from contractual records, and nothing material has been concealed therefrom.

Verified at **{city.title()}** on this **{today}**.

*(Complainant / Deponent)*
"""


__all__ = ["compile_court_dossier"]

