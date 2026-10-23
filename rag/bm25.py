"""
BM25 sparse retrieval engine.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import re
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from rank_bm25 import BM25Okapi

from logger import get_logger
from rag.chunking import DocumentChunk

log = get_logger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9]+\b", text)
    return tokens


class BM25Index:
    """BM25-based sparse retrieval over document chunks."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []
        self._corpus_tokens: list[list[str]] = []
        self._bm25: BM25Okapi | None = None

    @property
    def count(self) -> int:
        return len(self._chunks)

    def build(self, chunks: Sequence[DocumentChunk]) -> None:
        """Build the BM25 index from a list of document chunks."""
        self._chunks = list(chunks)
        self._corpus_tokens = [_tokenize(c.content) for c in self._chunks]
        if self._corpus_tokens:
            self._bm25 = BM25Okapi(self._corpus_tokens)
        else:
            self._bm25 = None
        log.info("bm25_index_built", num_docs=len(self._chunks))

    def query(self, query_text: str, top_k: int = 10) -> list[dict[str, Any]]:
        """
        BM25 retrieval.

        Returns a list of dicts with keys:
        ``chunk_id``, ``content``, ``metadata``, ``score``.
        """
        if self._bm25 is None or not self._chunks:
            return []

        tokens = _tokenize(query_text)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)

        # Normalize scores to 0-1 range
        max_score = float(np.max(scores)) if np.max(scores) > 0 else 1.0
        normalized = scores / max_score

        # Get top-k indices
        top_indices = np.argsort(normalized)[::-1][:top_k]

        hits: list[dict[str, Any]] = []
        for idx in top_indices:
            if normalized[idx] <= 0:
                continue
            chunk = self._chunks[idx]
            hits.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "score": float(normalized[idx]),
                }
            )
        return hits

    def save(self, path: Path) -> None:
        """Save chunk data to disk (BM25 itself is rebuilt on load)."""
        data = [
            {
                "chunk_id": c.chunk_id,
                "content": c.content,
                "metadata": c.metadata,
            }
            for c in self._chunks
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info("bm25_index_saved", path=str(path))

    def load(self, path: Path) -> None:
        """Load chunk data from disk and rebuild the BM25 index."""
        if not path.exists():
            log.warning("bm25_index_file_not_found", path=str(path))
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks = [
            DocumentChunk(
                chunk_id=d["chunk_id"],
                content=d["content"],
                metadata=d.get("metadata", {}),
            )
            for d in data
        ]
        self.build(chunks)
        log.info("bm25_index_loaded", path=str(path), count=len(chunks))
