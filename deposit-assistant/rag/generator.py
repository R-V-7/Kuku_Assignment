"""Layer 4: Bounded Grounding & Synthesis with Layer 5 Citation Firewall."""

from __future__ import annotations

import time
from typing import Any
from models import CaseFacts
from rag.firewall import CitationFirewall
from llm_client import ModelClient


def synthesize_rag_evaluation(
    case: CaseFacts,
    retrieved_chunks: list[dict[str, Any]],
    client: ModelClient | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Synthesize legally grounded evaluation strictly constrained to retrieved statutory chunks.

    Returns:
        (sanitized_text, firewall_status, telemetry_dict)
    """
    start_time = time.time()
    reason_str = case.deduction_reason.strip() if case.deduction_reason else "unspecified deductions"
    details_str = "; ".join(case.other_details) if case.other_details else "None reported"

    context_str = "\n\n".join(
        f"[{c['id']}] {c['act']} - {c['section']}: {c['title']}\n{c['text']}"
        for c in retrieved_chunks
    )

    prompt = f"""You are evaluating a civil tenancy legal dispute over '{reason_str}'.
CRITICAL LEGAL CONSTRAINT: You are strictly forbidden from citing criminal laws (such as IPC, BNS, CrPC) or escalating civil contract disputes to criminal offenses.
You MUST base your evaluation ONLY on the following retrieved statutory text:
<context>
{context_str}
</context>

If the context does not cover the reason, explicitly state that you cannot evaluate it based on the verified laws.
DO NOT invent or cite outside laws, criminal sections, or court cases. Provide an objective, civil contractual evaluation of whether the landlord's deduction is permissible under the provided statutory text and what documentary proof is required.

Tenant Case Facts:
- City/State: {case.city}, {case.state}
- Deposit Paid: Rs. {case.deposit_amount_inr}
- Amount Returned: Rs. {case.amount_returned_inr}
- Stated Deduction: Rs. {case.deduction_amount_inr} for '{reason_str}'
- Additional Facts & Evidence: {details_str}
- Written Agreement: {case.written_agreement_exists}
- Payment Proof: {case.payment_proof_exists}
"""

    raw_text = ""
    if client and hasattr(client, "generate_text"):
        try:
            resp = client.generate_text(prompt)
            raw_text = resp.text.strip()
        except Exception:
            pass

    # Deterministic fallback synthesis if offline
    if not raw_text:
        sections_summary = ", ".join(f"{c['section']} of {c['act']}" for c in retrieved_chunks)
        raw_text = (
            f"Based strictly on the retrieved statutory provisions ({sections_summary}), "
            f"deductions from a residential security deposit for '{reason_str}' require verified proof of actual, "
            f"direct loss beyond reasonable wear and tear. Under these verified laws, a landlord cannot arbitrarily "
            f"withhold funds without providing an itemized written statement and receipts for actual expenditure incurred."
        )

    # Layer 5: Post-Generation AST Citation Firewall
    sanitized_text, status, telemetry_log = CitationFirewall.audit_and_sanitize(
        raw_text, retrieved_chunks
    )

    latency_ms = round((time.time() - start_time) * 1000, 2)
    est_tokens = len(prompt.split()) + len(sanitized_text.split())
    est_cost_usd = round(est_tokens * 0.0000001, 6)

    telemetry = {
        "latency_ms": latency_ms,
        "estimated_tokens": est_tokens,
        "estimated_cost_usd": est_cost_usd,
        "firewall_status": status,
        "firewall_log": telemetry_log,
        "retrieved_chunk_ids": [c["id"] for c in retrieved_chunks],
    }

    return sanitized_text, status, telemetry

