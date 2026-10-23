"""
ChromaDB vector store — dense retrieval backend.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Any, Sequence

import chromadb
import numpy as np

from config import get_settings
from logger import get_logger
from rag.chunking import DocumentChunk
from rag.embeddings import EmbeddingService, get_embedding_service

log = get_logger(__name__)

_COLLECTION_NAME = "medical_knowledge"


class VectorStore:
    """ChromaDB-backed vector store for dense retrieval."""

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        settings = get_settings()
        self._persist_dir = str(persist_dir or settings.chroma_persist_dir)
        self._emb = embedding_service or get_embedding_service()

        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        log.info(
            "vector_store_ready",
            persist_dir=self._persist_dir,
            existing_docs=self._collection.count(),
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    # ---- indexing -----------------------------------------------------------

    def add_chunks(self, chunks: Sequence[DocumentChunk]) -> int:
        """Embed and upsert chunks into the collection. Returns count added."""
        if not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        texts = [c.content for c in chunks]
        metadatas = [c.metadata for c in chunks]

        embeddings = self._emb.embed_texts(texts).tolist()

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        log.info("chunks_indexed", count=len(chunks))
        return len(chunks)

    def clear(self) -> None:
        """Delete the collection and recreate it."""
        self._client.delete_collection(_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        log.info("vector_store_cleared")

    # ---- querying -----------------------------------------------------------

    def query(
        self,
        query_text: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Dense cosine-similarity retrieval.

        Returns a list of dicts with keys:
        ``chunk_id``, ``content``, ``metadata``, ``score``.
        """
        query_emb = self._emb.embed_query(query_text).tolist()

        results = self._collection.query(
            query_embeddings=[query_emb],
            n_results=min(top_k, self._collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        hits: list[dict[str, Any]] = []
        if results and results["ids"]:
            for idx in range(len(results["ids"][0])):
                distance = results["distances"][0][idx] if results["distances"] else 1.0
                # ChromaDB cosine distance → similarity
                score = 1.0 - distance
                hits.append(
                    {
                        "chunk_id": results["ids"][0][idx],
                        "content": results["documents"][0][idx] if results["documents"] else "",
                        "metadata": results["metadatas"][0][idx] if results["metadatas"] else {},
                        "score": max(score, 0.0),
                    }
                )

        return hits
