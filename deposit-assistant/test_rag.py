"""Unit tests for the 5-Layer Micro-RAG pipeline."""

import unittest
from rag.redactor import redact_pii
from rag.query_expander import expand_legal_query
from rag.vector_store import MicroVectorStore
from rag.firewall import CitationFirewall
from rag.generator import synthesize_rag_evaluation
from models import CaseFacts


class RAGPipelineTests(unittest.TestCase):
    def test_pii_redactor(self):
        sample = "My phone is 9876543210 and Aadhaar is 5432 1234 9876. My PAN is ABCDE1234F. Email: test@example.com."
        redacted, log = redact_pii(sample)
        self.assertIn("<PHONE_REDACTED>", redacted)
        self.assertIn("<AADHAAR_REDACTED>", redacted)
        self.assertIn("<PAN_REDACTED>", redacted)
        self.assertIn("<EMAIL_REDACTED>", redacted)
        self.assertEqual(len(log), 4)

    def test_query_expander_fallback(self):
        query = expand_legal_query("landlord kept money", "business losses")
        self.assertIn("business losses", query)
        self.assertIn("Contract Act", query)

    def test_vector_store_retrieval(self):
        store = MicroVectorStore()
        # Test retrieval for painting dispute
        results_painting = store.retrieve("repainting charges and normal wear and tear on walls", top_k=2)
        self.assertEqual(len(results_painting), 2)
        retrieved_ids = [r["id"] for r in results_painting]
        self.assertTrue(any(i in ["ICA_SEC_73", "MTA_SEC_15", "TPA_SEC_108"] for i in retrieved_ids))

        # Test retrieval for society penalty dispute
        results_society = store.retrieve("society penalty diwali festival loud music RWA fine", top_k=2)
        self.assertTrue(any(r["id"] == "RWA_BYLAWS" for r in results_society))

    def test_citation_firewall_passes_verified_citations(self):
        retrieved_chunks = [
            {"id": "ICA_SEC_73", "section": "Section 73", "act": "Indian Contract Act, 1872"},
            {"id": "MTA_SEC_11", "section": "Section 11", "act": "Model Tenancy Act, 2021"},
        ]
        text = "Under Section 73 of the Indian Contract Act and Section 11 of the Model Tenancy Act, refund is due."
        sanitized, status, telemetry = CitationFirewall.audit_and_sanitize(text, retrieved_chunks)
        self.assertEqual(status, "PASSED")
        self.assertNotIn("STRIPPED", sanitized)

    def test_citation_firewall_intercepts_hallucinated_citations(self):
        retrieved_chunks = [
            {"id": "ICA_SEC_73", "section": "Section 73", "act": "Indian Contract Act, 1872"},
        ]
        # Text cites hallucinated civil sections Section 42 and Section 14B not in retrieved context
        text = "Under Section 73 and Section 42, the landlord is liable under Section 14B."
        sanitized, status, telemetry = CitationFirewall.audit_and_sanitize(text, retrieved_chunks)
        self.assertEqual(status, "INTERCEPTED")
        self.assertIn("UNVERIFIED CITATION STRIPPED: Section 42", sanitized)
        self.assertIn("UNVERIFIED CITATION STRIPPED: Section 14B", sanitized)
        self.assertTrue(any(t["status"] == "INTERCEPTED" for t in telemetry))

    def test_citation_firewall_intercepts_criminal_ipc_hallucination(self):
        retrieved_chunks = [
            {"id": "ICA_SEC_73", "section": "Section 73", "act": "Indian Contract Act, 1872"},
            {"id": "MTA_SEC_11", "section": "Section 11", "act": "Model Tenancy Act, 2021"},
        ]
        # Text cites a hallucinated criminal offense Section 405 IPC
        text = "This constitutes unjust enrichment and criminal breach of trust (Section 405 IPC / BNS)."
        sanitized, status, telemetry = CitationFirewall.audit_and_sanitize(text, retrieved_chunks)
        self.assertEqual(status, "INTERCEPTED")
        self.assertIn("UNVERIFIED CRIMINAL CHARGE INTERCEPTED", sanitized)
        self.assertTrue(any("criminal" in str(t.get("reason", "")).lower() for t in telemetry))

    def test_guidance_evaluation_firewall_audit(self):
        """All guidance output paragraphs must pass cleanly through Citation Firewall."""
        from engine import DisputeEngine
        case = CaseFacts(
            scope="residential_deposit",
            city="Delhi",
            state="Delhi",
            deposit_amount_inr=50000,
            amount_returned_inr=20000,
            deduction_reason="business losses",
            deduction_amount_inr=30000,
        )
        retrieved_chunks = [
            {"id": "ICA_SEC_73", "section": "Section 73", "act": "Indian Contract Act, 1872"},
            {"id": "MTA_SEC_11", "section": "Section 11", "act": "Model Tenancy Act, 2021"},
        ]
        topics = DisputeEngine.get_guidance_topics(case)
        paragraphs, _ = DisputeEngine.evaluate_guidance(case, topics[0])
        for p in paragraphs:
            sanitized, status, _ = CitationFirewall.audit_and_sanitize(p, retrieved_chunks)
            self.assertEqual(status, "PASSED")
            self.assertNotIn("405 IPC", sanitized)
            self.assertNotIn("STRIPPED", sanitized)


if __name__ == "__main__":
    unittest.main()

