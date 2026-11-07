"""Layer 1: Query Expander - Converts conversational text to dense legal queries."""

from llm_client import ModelClient


def expand_legal_query(story: str, deduction_reason: str | None, client: ModelClient | None = None) -> str:
    """Transform messy colloquial intake into a dense, formal statutory retrieval query."""
    reason_str = deduction_reason.strip() if deduction_reason else "unjustified withholding"

    if client and hasattr(client, "generate_text"):
        prompt = (
            f"Convert this tenant security deposit dispute into a dense, 1-sentence formal Indian legal search query "
            f"suitable for retrieving statutory sections (Contract Act, Model Tenancy Act, Evidence Act). "
            f"Focus on the deduction reason: '{reason_str}'. Return ONLY the query string without markdown:\n\n"
            f"Dispute context: {story[:300]}"
        )
        try:
            resp = client.generate_text(prompt)
            clean_query = resp.text.strip().strip('"').strip("'")
            if clean_query:
                return clean_query
        except Exception:
            pass

    # Deterministic fallback query expansion
    return f"Residential tenancy security deposit deduction for {reason_str} normal wear and tear versus landlord breach Indian Contract Act Model Tenancy Act"

