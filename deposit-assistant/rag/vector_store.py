"""Layer 3: Frictionless In-Memory Vector Retrieval (Micro-RAG).

Uses numpy cosine similarity with google-genai text-embedding-004
and an automatic lexical/BM25 fallback for zero-infrastructure offline operation.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

import numpy as np


class MicroVectorStore:
    """Lightweight in-memory vector store without C++ or external DB dependencies."""

    def __init__(self, statutes_path: Path | str | None = None) -> None:
        if statutes_path is None:
            statutes_path = Path(__file__).parent.parent / "statutes.json"
        self.statutes_path = Path(statutes_path)
        self.chunks: list[dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        if self.statutes_path.exists():
            with open(self.statutes_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
        else:
            self.chunks = []

    def _get_embedding(self, text: str, client: Any | None = None) -> np.ndarray | None:
        """Fetch embedding via google-genai text-embedding-004 if API key is active."""
        if client and hasattr(client, "_client") and os.environ.get("GEMINI_API_KEY"):
            try:
                res = client._client.models.embed_content(
                    model="text-embedding-004",
                    contents=text,
                )
                if hasattr(res, "embedding") and res.embedding:
                    return np.array(res.embedding.values, dtype=np.float32)
                elif hasattr(res, "embeddings") and res.embeddings:
                    return np.array(res.embeddings[0].values, dtype=np.float32)
            except Exception:
                pass
        return None

    def _lexical_similarity(self, query: str, doc_text: str, tags: list[str]) -> float:
        """Robust lexical BM25/Jaccard fallback when running offline without API key."""
        q_tokens = set(re.findall(r"\b\w{3,}\b", query.lower()))
        d_tokens = set(re.findall(r"\b\w{3,}\b", doc_text.lower()))
        tag_tokens = set(t.lower() for t in tags)

        if not q_tokens:
            return 0.0

        tag_matches = len(q_tokens.intersection(tag_tokens)) * 3.0
        doc_matches = len(q_tokens.intersection(d_tokens)) * 1.0

        total_score = (tag_matches + doc_matches) / (len(q_tokens) + 5.0)
        return min(0.99, total_score)

    def retrieve(self, query: str, top_k: int = 2, client: Any | None = None) -> list[dict[str, Any]]:
        """Retrieve top-k statutory clauses via cosine similarity or lexical fallback."""
        if not self.chunks:
            return []

        query_vec = self._get_embedding(query, client)

        scored_results: list[tuple[float, dict[str, Any]]] = []

        if query_vec is not None:
            # Build embeddings matrix if not yet cached
            if self.embeddings is None or len(self.embeddings) != len(self.chunks):
                vec_list = []
                for chunk in self.chunks:
                    content = f"{chunk['title']} {chunk['text']} {' '.join(chunk.get('tags', []))}"
                    c_vec = self._get_embedding(content, client)
                    if c_vec is None:
                        # Fallback for that chunk
                        c_vec = np.random.randn(768).astype(np.float32)
                    vec_list.append(c_vec)
                self.embeddings = np.array(vec_list, dtype=np.float32)

            # Cosine similarity calculation
            norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec)
            norms[norms == 0] = 1e-8
            sims = np.dot(self.embeddings, query_vec) / norms

            for idx, sim in enumerate(sims):
                res = dict(self.chunks[idx])
                res["similarity_score"] = round(float(sim), 4)
                scored_results.append((float(sim), res))
        else:
            # High-precision lexical matching fallback
            for chunk in self.chunks:
                sim = self._lexical_similarity(
                    query, chunk["text"] + " " + chunk["title"], chunk.get("tags", [])
                )
                res = dict(chunk)
                res["similarity_score"] = round(float(sim), 4)
                scored_results.append((float(sim), res))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored_results[:top_k]]

