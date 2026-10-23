"""
Tests for RAG pipeline components — Phase 1.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from rag.chunking import (
    DocumentChunk,
    chunk_document,
    detect_document_type,
    extract_title_from_content,
)
from rag.bm25 import BM25Index, _tokenize
from rag.citations import build_citations, format_citations_for_prompt


# =============================================================================
# Chunking Tests
# =============================================================================


class TestChunking:
    """Tests for document chunking."""

    def test_chunk_simple_document(self, tmp_path: Path):
        doc = tmp_path / "test.md"
        doc.write_text("# Test Document\n\nThis is a test document with enough content to create at least one chunk. " * 10)

        chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_chunk_metadata(self, tmp_path: Path):
        doc = tmp_path / "pneumonia_guide.md"
        doc.write_text("# Pneumonia Guide\n\nPneumonia is an infection of the lungs. " * 20)

        chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)
        assert len(chunks) > 0

        meta = chunks[0].metadata
        assert "source" in meta
        assert "title" in meta
        assert "chunk_id" in meta
        assert "document_type" in meta

    def test_chunk_id_deterministic(self, tmp_path: Path):
        doc = tmp_path / "test.md"
        doc.write_text("# Test\n\nContent here. " * 20)

        chunks1 = chunk_document(doc, chunk_size=200, chunk_overlap=20)
        chunks2 = chunk_document(doc, chunk_size=200, chunk_overlap=20)

        assert chunks1[0].chunk_id == chunks2[0].chunk_id

    def test_empty_document(self, tmp_path: Path):
        doc = tmp_path / "empty.md"
        doc.write_text("")

        chunks = chunk_document(doc)
        assert len(chunks) == 0

    def test_extract_title_from_heading(self):
        content = "# My Title\n\nSome content"
        title = extract_title_from_content(content, Path("fallback.md"))
        assert title == "My Title"

    def test_extract_title_fallback(self):
        content = "No heading here"
        title = extract_title_from_content(content, Path("my_document.md"))
        assert title == "My Document"

    def test_detect_document_type(self):
        assert detect_document_type(Path("guideline_pneumonia.md"), "") == "clinical_guideline"
        assert detect_document_type(Path("case_report.md"), "") == "case_report"
        assert detect_document_type(Path("textbook_chapter.md"), "") == "educational"


# =============================================================================
# BM25 Tests
# =============================================================================


class TestBM25:
    """Tests for BM25 sparse retrieval."""

    def _build_index(self) -> BM25Index:
        chunks = [
            DocumentChunk(chunk_id="c1", content="Pneumonia is an infection of the lungs caused by bacteria or viruses.", metadata={"title": "Pneumonia"}),
            DocumentChunk(chunk_id="c2", content="Elevated white blood cell count indicates infection or inflammation.", metadata={"title": "WBC"}),
            DocumentChunk(chunk_id="c3", content="Troponin levels rise when there is damage to the heart muscle.", metadata={"title": "Troponin"}),
            DocumentChunk(chunk_id="c4", content="Diabetes mellitus is characterized by high blood glucose levels.", metadata={"title": "Diabetes"}),
        ]
        index = BM25Index()
        index.build(chunks)
        return index

    def test_build_index(self):
        index = self._build_index()
        assert index.count == 4

    def test_query_returns_relevant(self):
        index = self._build_index()
        results = index.query("lung infection pneumonia", top_k=2)
        assert len(results) > 0
        assert results[0]["chunk_id"] == "c1"

    def test_query_scoring(self):
        index = self._build_index()
        results = index.query("heart muscle damage troponin", top_k=4)
        assert len(results) > 0
        # Troponin doc should score highest
        assert results[0]["chunk_id"] == "c3"

    def test_empty_query(self):
        index = self._build_index()
        results = index.query("", top_k=5)
        assert len(results) == 0

    def test_save_and_load(self, tmp_path: Path):
        index = self._build_index()
        save_path = tmp_path / "bm25.json"
        index.save(save_path)

        new_index = BM25Index()
        new_index.load(save_path)
        assert new_index.count == 4

        # Verify search still works
        results = new_index.query("pneumonia", top_k=2)
        assert len(results) > 0

    def test_tokenizer(self):
        tokens = _tokenize("Elevated WBC count > 11,000")
        assert "elevated" in tokens
        assert "wbc" in tokens
        assert "count" in tokens


# =============================================================================
# Citation Tests
# =============================================================================


class TestCitations:
    """Tests for citation building and formatting."""

    def _sample_results(self) -> list[dict]:
        return [
            {
                "chunk_id": "c1",
                "content": "Pneumonia is a lung infection.",
                "metadata": {"title": "Pneumonia Guide", "source": "demo/pneumonia.md", "document_type": "clinical_guideline"},
                "score": 0.85,
                "rerank_score": 0.9,
            },
            {
                "chunk_id": "c2",
                "content": "WBC elevation indicates infection.",
                "metadata": {"title": "CBC Guide", "source": "demo/cbc.md", "document_type": "educational"},
                "score": 0.7,
                "rerank_score": 0.75,
            },
        ]

    def test_build_citations(self):
        citations = build_citations(self._sample_results())
        assert len(citations) == 2
        assert citations[0].source_id == "E1"
        assert citations[1].source_id == "E2"
        assert citations[0].title == "Pneumonia Guide"

    def test_citation_deduplication(self):
        results = self._sample_results()
        results.append(results[0].copy())  # Duplicate
        citations = build_citations(results)
        assert len(citations) == 2

    def test_citation_relevance_score(self):
        citations = build_citations(self._sample_results())
        assert citations[0].relevance_score == 0.9  # Uses rerank_score

    def test_format_citations_for_prompt(self):
        citations = build_citations(self._sample_results())
        formatted = format_citations_for_prompt(citations)
        assert "[E1]" in formatted
        assert "[E2]" in formatted
        assert "Pneumonia Guide" in formatted

    def test_format_empty_citations(self):
        formatted = format_citations_for_prompt([])
        assert "No relevant evidence" in formatted
