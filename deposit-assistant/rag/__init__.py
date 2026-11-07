"""Micro-RAG pipeline package for Deposit Dispute Assistant."""

from rag.redactor import redact_pii
from rag.query_expander import expand_legal_query
from rag.vector_store import MicroVectorStore
from rag.firewall import CitationFirewall
from rag.generator import synthesize_rag_evaluation

__all__ = [
    "redact_pii",
    "expand_legal_query",
    "MicroVectorStore",
    "CitationFirewall",
    "synthesize_rag_evaluation",
]

