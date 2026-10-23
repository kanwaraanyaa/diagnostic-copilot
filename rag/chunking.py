"""
Document chunking with metadata preservation.
"""

from __future__ import annotations

import hashlib
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings
from logger import get_logger

log = get_logger(__name__)


@dataclass
class DocumentChunk:
    """A single chunk of text with metadata."""
    chunk_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.metadata.get("source", "")

    @property
    def title(self) -> str:
        return self.metadata.get("title", "")

    @property
    def document_type(self) -> str:
        return self.metadata.get("document_type", "unknown")


def _generate_chunk_id(source: str, index: int, content: str) -> str:
    """Deterministic chunk ID from source + index + content hash."""
    h = hashlib.sha256(f"{source}:{index}:{content[:128]}".encode()).hexdigest()[:12]
    return f"chunk_{h}"


def load_text_file(file_path: Path) -> str:
    """Read a plain-text or markdown file."""
    return file_path.read_text(encoding="utf-8", errors="replace")


def extract_title_from_content(content: str, file_path: Path) -> str:
    """Try to extract a title from the first heading or use the filename."""
    for line in content.splitlines()[:10]:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("# ").strip()
        if stripped.startswith("Title:"):
            return stripped.split(":", 1)[1].strip()
    return file_path.stem.replace("_", " ").replace("-", " ").title()


def detect_document_type(file_path: Path, content: str) -> str:
    """Heuristic detection of document type from path/content."""
    name_lower = file_path.stem.lower()
    content_lower = content[:500].lower()

    if "guideline" in name_lower or "guideline" in content_lower:
        return "clinical_guideline"
    if "review" in name_lower or "peer" in content_lower or "abstract" in content_lower:
        return "peer_reviewed"
    if "case" in name_lower or "case report" in content_lower:
        return "case_report"
    if "textbook" in name_lower or "chapter" in name_lower:
        return "educational"
    return "educational"


def chunk_document(
    file_path: Path,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """
    Load a text/markdown file → split into chunks with metadata.

    Parameters
    ----------
    file_path : Path
        Path to a .txt or .md file.
    chunk_size : int, optional
        Override the configured chunk size.
    chunk_overlap : int, optional
        Override the configured chunk overlap.

    Returns
    -------
    list[DocumentChunk]
    """
    settings = get_settings()
    cs = chunk_size or settings.chunk_size
    co = chunk_overlap or settings.chunk_overlap

    content = load_text_file(file_path)
    if not content.strip():
        log.warning("empty_document", path=str(file_path))
        return []

    title = extract_title_from_content(content, file_path)
    doc_type = detect_document_type(file_path, content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cs,
        chunk_overlap=co,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    text_chunks = splitter.split_text(content)

    chunks: list[DocumentChunk] = []
    for idx, text in enumerate(text_chunks):
        chunk_id = _generate_chunk_id(str(file_path), idx, text)
        meta = {
            "source": str(file_path),
            "title": title,
            "document_type": doc_type,
            "section": "",
            "chunk_id": chunk_id,
            "chunk_index": idx,
            "total_chunks": len(text_chunks),
        }
        chunks.append(DocumentChunk(chunk_id=chunk_id, content=text, metadata=meta))

    log.info(
        "document_chunked",
        path=str(file_path),
        title=title,
        doc_type=doc_type,
        num_chunks=len(chunks),
    )
    return chunks


def chunk_documents_from_directory(directory: Path) -> list[DocumentChunk]:
    """Recursively chunk all .txt and .md files under *directory*."""
    all_chunks: list[DocumentChunk] = []
    extensions = {".txt", ".md"}

    for file_path in sorted(directory.rglob("*")):
        if file_path.suffix.lower() in extensions and file_path.is_file():
            all_chunks.extend(chunk_document(file_path))

    log.info("directory_chunked", directory=str(directory), total_chunks=len(all_chunks))
    return all_chunks
