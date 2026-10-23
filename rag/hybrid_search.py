"""
Hybrid retrieval — combines dense (ChromaDB) and sparse (BM25) results.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any

from config import get_settings
from logger import get_logger
from rag.bm25 import BM25Index
from rag.vector_store import VectorStore

log = get_logger(__name__)


def hybrid_search(
    query: str,
    vector_store: VectorStore,
    bm25_index: BM25Index,
    top_k: int | None = None,
    dense_weight: float | None = None,
    sparse_weight: float | None = None,
) -> list[dict[str, Any]]:
    """
    Combine dense and sparse retrieval results using weighted Reciprocal Rank Fusion.

    Parameters
    ----------
    query : str
        The search query.
    vector_store : VectorStore
        Dense retrieval backend (ChromaDB).
    bm25_index : BM25Index
        Sparse retrieval backend (BM25).
    top_k : int, optional
        Number of results to return. Defaults to config value.
    dense_weight : float, optional
        Weight for dense scores. Defaults to config value.
    sparse_weight : float, optional
        Weight for sparse scores. Defaults to config value.

    Returns
    -------
    list[dict]
        Merged, scored, and sorted results.
    """
    settings = get_settings()
    k = top_k or settings.top_k_retrieval
    dw = dense_weight if dense_weight is not None else settings.dense_weight
    sw = sparse_weight if sparse_weight is not None else settings.sparse_weight

    # Retrieve from both sources
    dense_hits = vector_store.query(query, top_k=k * 2)
    sparse_hits = bm25_index.query(query, top_k=k * 2)

    # Index by chunk_id
    merged: dict[str, dict[str, Any]] = {}

    for hit in dense_hits:
        cid = hit["chunk_id"]
        merged[cid] = {
            "chunk_id": cid,
            "content": hit["content"],
            "metadata": hit["metadata"],
            "dense_score": hit["score"],
            "sparse_score": 0.0,
        }

    for hit in sparse_hits:
        cid = hit["chunk_id"]
        if cid in merged:
            merged[cid]["sparse_score"] = hit["score"]
        else:
            merged[cid] = {
                "chunk_id": cid,
                "content": hit["content"],
                "metadata": hit["metadata"],
                "dense_score": 0.0,
                "sparse_score": hit["score"],
            }

    # Compute hybrid score
    results: list[dict[str, Any]] = []
    for item in merged.values():
        hybrid_score = dw * item["dense_score"] + sw * item["sparse_score"]
        results.append(
            {
                "chunk_id": item["chunk_id"],
                "content": item["content"],
                "metadata": item["metadata"],
                "score": hybrid_score,
                "dense_score": item["dense_score"],
                "sparse_score": item["sparse_score"],
            }
        )

    # Sort by hybrid score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    log.info(
        "hybrid_search_complete",
        query_preview=query[:80],
        dense_hits=len(dense_hits),
        sparse_hits=len(sparse_hits),
        merged_hits=len(results),
        returned=min(k, len(results)),
    )

    return results[:k]
