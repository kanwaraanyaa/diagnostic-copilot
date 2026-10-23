"""
Citation builder — converts retrieval results into structured Citation objects.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any

from backend.schemas.patient import Citation, DocumentType
from logger import get_logger

log = get_logger(__name__)


def build_citations(
    retrieval_results: list[dict[str, Any]],
    prefix: str = "E",
) -> list[Citation]:
    """
    Convert retrieval results into a list of ``Citation`` objects with
    sequential source IDs (E1, E2, …).

    Parameters
    ----------
    retrieval_results : list[dict]
        Results from hybrid search / reranking.
        Each dict must have ``content``, ``metadata``, and ``score`` keys.
    prefix : str
        Prefix for source IDs.

    Returns
    -------
    list[Citation]
    """
    citations: list[Citation] = []
    seen_chunks: set[str] = set()

    for idx, result in enumerate(retrieval_results, start=1):
        chunk_id = result.get("chunk_id", f"unknown_{idx}")
        if chunk_id in seen_chunks:
            continue
        seen_chunks.add(chunk_id)

        metadata = result.get("metadata", {})
        doc_type_str = metadata.get("document_type", "unknown")
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            doc_type = DocumentType.UNKNOWN

        citation = Citation(
            source_id=f"{prefix}{idx}",
            title=metadata.get("title", "Untitled"),
            source=metadata.get("source", ""),
            document_type=doc_type,
            content=result.get("content", ""),
            relevance_score=round(result.get("rerank_score", result.get("score", 0.0)), 4),
            chunk_id=chunk_id,
            section=metadata.get("section", ""),
        )
        citations.append(citation)

    log.info("citations_built", count=len(citations))
    return citations


def format_citations_for_prompt(citations: list[Citation]) -> str:
    """
    Format citations as a text block to inject into LLM prompts.

    Example output::

        [E1] Pneumonia Overview (clinical_guideline, relevance: 0.89)
        Community-acquired pneumonia (CAP) is an acute infection…

        [E2] WBC Interpretation (educational, relevance: 0.76)
        Elevated white blood cell count may indicate…
    """
    if not citations:
        return "No relevant evidence was retrieved."

    parts: list[str] = []
    for c in citations:
        header = f"[{c.source_id}] {c.title} ({c.document_type.value}, relevance: {c.relevance_score:.2f})"
        parts.append(f"{header}\n{c.content}")

    return "\n\n".join(parts)
