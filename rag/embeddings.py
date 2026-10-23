"""
Embedding service — wraps sentence-transformers for dense vector generation.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from functools import lru_cache
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from config import get_settings
from logger import get_logger

log = get_logger(__name__)


class EmbeddingService:
    """Thin wrapper around a SentenceTransformer model."""

    def __init__(self, model_name: str | None = None) -> None:
        name = model_name or get_settings().embedding_model
        log.info("loading_embedding_model", model=name)
        self._model = SentenceTransformer(name)
        self._model_name = name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Encode a batch of texts into dense vectors."""
        embeddings = self._model.encode(
            list(texts),
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return np.asarray(embeddings)

    def embed_query(self, query: str) -> np.ndarray:
        """Encode a single query string."""
        return self.embed_texts([query])[0]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Singleton embedding service."""
    return EmbeddingService()
