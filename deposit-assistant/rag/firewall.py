"""Layer 5: Post-Generation AST / Citation Firewall & Hallucination Backstop."""

from __future__ import annotations

import re
from typing import Any


class CitationFirewall:
    """Verifies that all statutory citations in LLM outputs exist in the retrieved context

    and prevents civil dispute escalation to unverified criminal codes (IPC, BNS, CrPC).
    """

    # Upgraded aggressive pattern to catch Act acronyms like "Section 405 IPC", "Section 420", etc.
    CITATION_PATTERN = re.compile(
        r"\b(?:Section|Sec\.|Article|Schedule|Bylaw)\s+\d+[A-Za-z]?(?:\s+(?-i:IPC|BNS|CrPC|CPC|IEA|BSA|[A-Z]{2,5}))?(?:\([a-z0-9]+\))?",
        re.IGNORECASE,
    )

    # Criminal offenses that must never be cited in civil tenancy disputes
    CRIMINAL_HALLUCINATION_PATTERN = re.compile(
        r"\b(?:criminal breach of trust|Section\s+405\s*(?:IPC|BNS)?|Section\s+420\s*(?:IPC|BNS)?|police FIR|arrest)\b",
        re.IGNORECASE,
    )

    @classmethod
    def audit_and_sanitize(
        cls, text: str, retrieved_chunks: list[dict[str, Any]]
    ) -> tuple[str, str, list[dict[str, Any]]]:
        """Verify generated text against retrieved chunks.

        Returns:
            (sanitized_text, status, telemetry_log)
            status is either 'PASSED' or 'INTERCEPTED'.
        """
        # Build whitelist of allowed sections from retrieved chunks
        allowed_sections: set[str] = set()
        for chunk in retrieved_chunks:
            sec = chunk.get("section", "")
            if sec:
                allowed_sections.add(cls._normalize_citation(sec))
            # Also extract individual section tokens
            for m in cls.CITATION_PATTERN.findall(sec):
                allowed_sections.add(cls._normalize_citation(m))
            act = chunk.get("act", "")
            if act:
                for match in cls.CITATION_PATTERN.findall(act):
                    allowed_sections.add(cls._normalize_citation(match))

        sanitized_text = text
        telemetry: list[dict[str, Any]] = []
        intercepted_count = 0

        # Check 1: Intercept unverified criminal escalations (IPC 405, criminal breach of trust)
        for crim_match in cls.CRIMINAL_HALLUCINATION_PATTERN.finditer(sanitized_text):
            crim_val = crim_match.group(0)
            intercepted_count += 1
            sanitized_text = sanitized_text.replace(
                crim_val, "[UNVERIFIED CRIMINAL CHARGE INTERCEPTED: civil breach only]"
            )
            telemetry.append(
                {
                    "citation": crim_val,
                    "status": "INTERCEPTED",
                    "reason": "Prohibited criminal law escalation in civil tenancy dispute",
                }
            )

        # Check 2: Intercept unverified sections not in retrieved chunks
        found_citations = cls.CITATION_PATTERN.findall(sanitized_text)

        for cite in found_citations:
            norm = cls._normalize_citation(cite)
            # Check if citation root is in allowed sections
            matched_allowed = any(
                norm == allowed or norm.startswith(allowed) or allowed.startswith(norm)
                for allowed in allowed_sections
            )

            if not matched_allowed:
                intercepted_count += 1
                sanitized_text = sanitized_text.replace(
                    cite, f"[UNVERIFIED CITATION STRIPPED: {cite}]"
                )
                telemetry.append(
                    {
                        "citation": cite,
                        "status": "INTERCEPTED",
                        "reason": "Not present in verified retrieved statutory chunks",
                    }
                )
            else:
                telemetry.append(
                    {
                        "citation": cite,
                        "status": "VERIFIED",
                        "reason": "Matches retrieved statutory chunk",
                    }
                )

        status = "INTERCEPTED" if intercepted_count > 0 else "PASSED"
        return sanitized_text, status, telemetry

    @staticmethod
    def _normalize_citation(citation: str) -> str:
        """Normalize citation strings for comparison (e.g. 'Sec. 73' -> 'section 73')."""
        c = citation.lower().strip()
        c = re.sub(r"^sec\.\s*", "section ", c)
        c = re.sub(r"\s+", " ", c)
        return c
