"""
Script to ingest documents into the knowledge base.

Usage:
    python scripts/ingest_data.py              # Ingest from data/demo/
    python scripts/ingest_data.py data/raw/    # Ingest from custom directory
    python scripts/ingest_data.py --clear      # Clear and re-ingest
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import get_settings
from logger import setup_logging
from rag.ingestion import ingest_directory

setup_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into the knowledge base")
    parser.add_argument("directory", nargs="?", default=None, help="Directory to ingest (default: data/demo/)")
    parser.add_argument("--clear", action="store_true", help="Clear existing index before ingestion")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    settings = get_settings()
    data_dir = Path(args.directory) if args.directory else settings.demo_data_dir

    print(f"\n[INFO] Ingesting documents from: {data_dir}")
    print(f"   ChromaDB persist dir: {settings.chroma_persist_dir}")
    print(f"   Embedding model: {settings.embedding_model}")
    print(f"   Chunk size: {settings.chunk_size}, overlap: {settings.chunk_overlap}\n")

    count = ingest_directory(directory=data_dir, clear_existing=args.clear)

    print(f"\n[SUCCESS] Ingestion complete! {count} chunks indexed.")
    print("   You can now start the backend and frontend.")


if __name__ == "__main__":
    main()
