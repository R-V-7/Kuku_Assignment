"""Deposit Dispute Assistant - 5-Layer Core Business Engine.

Encapsulates:
Layer 1: Pre-Ingestion Guardrails (PII Redaction, Tri-State Pydantic Extraction, Legal Query Expander).
Layer 2: Human-in-the-Loop Fact Confirmation & State Machine.
Layer 3: Frictionless In-Memory Vector Retrieval (Micro-RAG via numpy cosine similarity).
Layer 4: Bounded Grounding & Statutory Synthesis.
Layer 5: Post-Generation AST Citation Firewall & Telemetry Logger.
"""

from typing import Any
from models import (
    CaseFacts,
    UNION_TERRITORIES,
    MAJOR_INDIAN_CITIES_TO_STATE,
    INDIAN_STATES,
    normalize_ut_location,
    clean_location_input,
    resolve_indian_location,
)
from intake import extract_case, IntakeError
from followup import followup_questions, unanswered_questions
from guidance import guidance_for, get_guidance_topics, SOURCES
from draft import generate_demand_letter, classify_dispute_posture
from llm_client import ModelClient, ModelError, create_client
from rag import (
    redact_pii,
    expand_legal_query,
    MicroVectorStore,
    CitationFirewall,
    synthesize_rag_evaluation,
)


class DisputeEngine:
    """High-level orchestrator for the 5-layer deposit dispute assistant pipeline."""

    def __init__(self, client: ModelClient | None = None) -> None:
        self.client = client
        self.vector_store = MicroVectorStore()

    def get_client(self) -> ModelClient:
        if self.client is None:
            self.client = create_client()
        return self.client

    def redact_user_input(self, text: str) -> tuple[str, list[dict[str, str]]]:
        """Layer 1: Mask Aadhaar, PAN, phone, and email before LLM ingestion."""
        return redact_pii(text)

    def extract_intake(
        self,
        story: str,
        current_case: CaseFacts | None = None,
        question: str | None = None,
    ) -> CaseFacts:
        """Layer 1: Extract or update structured facts with PII protection."""
        client = self.get_client()
        sanitized_story, _ = self.redact_user_input(story)
        return extract_case(
            story=sanitized_story,
            client=client,
            current_case=current_case,
            question=question,
        )

    def expand_query(self, story: str, deduction_reason: str | None) -> str:
        """Layer 1: Expand conversational intake into a dense statutory retrieval query."""
        client = self.get_client()
        return expand_legal_query(story, deduction_reason, client=client)

    @staticmethod
    def get_followup_questions(
        case: CaseFacts, answered: list[str] | None = None
    ) -> list[str]:
        """Layer 2: Get remaining targeted questions for unknown or missing facts."""
        questions = followup_questions(case)
        if answered:
            return unanswered_questions(questions, answered)
        return questions

    @staticmethod
    def get_next_question(
        case: CaseFacts, answered: list[str] | None = None
    ) -> str | None:
        """Return the highest priority targeted question, or None if facts are sufficient."""
        unanswered = DisputeEngine.get_followup_questions(case, answered)
        return unanswered[0] if unanswered else None

    def retrieve_statutes(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Layer 3: In-memory cosine similarity retrieval over verified statutes."""
        client = self.get_client()
        return self.vector_store.retrieve(query=query, top_k=top_k, client=client)

    def synthesize_rag_guidance(
        self, case: CaseFacts, retrieved_chunks: list[dict[str, Any]]
    ) -> tuple[str, str, dict[str, Any]]:
        """Layer 4 & 5: Bounded statutory synthesis passing through Citation Firewall."""
        client = self.get_client()
        return synthesize_rag_evaluation(case, retrieved_chunks, client=client)

    @staticmethod
    def get_guidance_topics(case: CaseFacts) -> list[str]:
        """Dynamically construct UI dropdown topics for guidance."""
        return get_guidance_topics(case)

    @staticmethod
    def evaluate_guidance(
        case: CaseFacts,
        topic: str,
        evaluation_text: str = "",
        posture: str | None = None,
    ) -> tuple[list[str], list[str]]:
        """Static rule-based safe guidance evaluation conditioned on dispute posture."""
        return guidance_for(case, topic, evaluation_text=evaluation_text, posture=posture)

    @staticmethod
    def classify_dispute_posture(case: CaseFacts, evaluation_text: str = "") -> str:
        """Classifies dispute posture into 'justified', 'partial', or 'unjustified'."""
        return classify_dispute_posture(case, evaluation_text)

    @staticmethod
    def draft_demand_letter(
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
        """Layer 4: Generate an objective, evaluation-conditioned legal correspondence."""
        return generate_demand_letter(
            case=case,
            tenant_name=tenant_name,
            landlord_name=landlord_name,
            property_address=property_address,
            notice_date=notice_date,
            bank_details=bank_details,
            retrieved_chunks=retrieved_chunks,
            evaluation_text=evaluation_text,
            posture=posture,
        )


__all__ = [
    "CaseFacts",
    "UNION_TERRITORIES",
    "MAJOR_INDIAN_CITIES_TO_STATE",
    "INDIAN_STATES",
    "normalize_ut_location",
    "clean_location_input",
    "resolve_indian_location",
    "extract_case",
    "IntakeError",
    "followup_questions",
    "unanswered_questions",
    "guidance_for",
    "get_guidance_topics",
    "SOURCES",
    "generate_demand_letter",
    "classify_dispute_posture",
    "DisputeEngine",
    "redact_pii",
    "expand_legal_query",
    "MicroVectorStore",
    "CitationFirewall",
    "synthesize_rag_evaluation",
]
