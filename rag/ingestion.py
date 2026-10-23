"""
Document ingestion pipeline — load, chunk, embed, and index documents.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

from config import get_settings
from logger import get_logger
from rag.bm25 import BM25Index
from rag.chunking import DocumentChunk, chunk_documents_from_directory
from rag.vector_store import VectorStore

log = get_logger(__name__)

BM25_INDEX_PATH = Path("data/processed/bm25_index.json")


def ingest_directory(
    directory: Path | None = None,
    vector_store: VectorStore | None = None,
    bm25_index: BM25Index | None = None,
    clear_existing: bool = False,
) -> int:
    """
    Full ingestion pipeline:
    1. Load and chunk documents from *directory*.
    2. Insert into ChromaDB (dense index).
    3. Build BM25 (sparse index) and save to disk.

    Parameters
    ----------
    directory : Path, optional
        Directory to ingest. Defaults to ``data/demo``.
    vector_store : VectorStore, optional
        Override the default vector store.
    bm25_index : BM25Index, optional
        Override the default BM25 index.
    clear_existing : bool
        If True, clear the existing index before ingestion.

    Returns
    -------
    int
        Number of chunks indexed.
    """
    settings = get_settings()
    data_dir = directory or settings.demo_data_dir

    if not data_dir.exists():
        log.error("data_directory_not_found", path=str(data_dir))
        return 0

    # 1. Chunk documents
    chunks = chunk_documents_from_directory(data_dir)
    if not chunks:
        log.warning("no_chunks_created", directory=str(data_dir))
        return 0

    # 2. Dense index — ChromaDB
    vs = vector_store or VectorStore()
    if clear_existing:
        vs.clear()
    vs.add_chunks(chunks)

    # 3. Sparse index — BM25
    bm = bm25_index or BM25Index()
    bm.build(chunks)
    bm.save(BM25_INDEX_PATH)

    log.info(
        "ingestion_complete",
        directory=str(data_dir),
        total_chunks=len(chunks),
        vector_store_count=vs.count,
        bm25_count=bm.count,
    )
    return len(chunks)


def ensure_indexes_loaded(
    vector_store: VectorStore | None = None,
    bm25_index: BM25Index | None = None,
) -> tuple[VectorStore, BM25Index]:
    """
    Ensure both indexes exist.  If the BM25 index is empty but a
    saved file exists, load it. If ChromaDB is empty, trigger ingestion.

    Returns
    -------
    tuple[VectorStore, BM25Index]
    """
    vs = vector_store or VectorStore()
    bm = bm25_index or BM25Index()

    # Try loading BM25 from disk if empty
    if bm.count == 0 and BM25_INDEX_PATH.exists():
        bm.load(BM25_INDEX_PATH)

    # If still nothing, attempt ingestion from demo data
    if vs.count == 0:
        log.info("indexes_empty_triggering_ingestion")
        ingest_directory(vector_store=vs, bm25_index=bm)

    return vs, bm
