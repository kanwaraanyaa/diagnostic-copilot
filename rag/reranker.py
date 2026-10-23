"""
Reranker — re-scores retrieved results for higher precision.

Phase 1 uses a lightweight cross-encoder–style reranker based on
embedding similarity between the query and each candidate.
Phase 3 can swap in a dedicated cross-encoder model.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any

import numpy as np

from config import get_settings
from logger import get_logger
from rag.embeddings import EmbeddingService, get_embedding_service

log = get_logger(__name__)


def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int | None = None,
    embedding_service: EmbeddingService | None = None,
) -> list[dict[str, Any]]:
    """
    Re-score candidates by embedding similarity to the query.

    Each candidate dict must contain a ``content`` key.
    A ``rerank_score`` key is added, and results are re-sorted.

    Parameters
    ----------
    query : str
        The original search query.
    candidates : list[dict]
        Candidates from hybrid search.
    top_k : int, optional
        Number of results to return after reranking.
    embedding_service : EmbeddingService, optional
        Override the default singleton.

    Returns
    -------
    list[dict]
        Reranked candidates with ``rerank_score`` added.
    """
    settings = get_settings()
    k = top_k or settings.top_k_rerank
    emb = embedding_service or get_embedding_service()

    if not candidates:
        return []

    query_vec = emb.embed_query(query)
    contents = [c["content"] for c in candidates]
    content_vecs = emb.embed_texts(contents)

    # Cosine similarity (vectors are already normalized)
    similarities = content_vecs @ query_vec

    for i, candidate in enumerate(candidates):
        candidate["rerank_score"] = float(similarities[i])

    # Sort by rerank_score descending
    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

    log.info(
        "reranking_complete",
        input_count=len(candidates),
        output_count=min(k, len(candidates)),
        top_score=round(candidates[0]["rerank_score"], 4) if candidates else 0,
    )

    return candidates[:k]
