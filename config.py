"""
Central configuration loaded from environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Application-wide settings read from environment variables."""

    # --- LLM Provider -------------------------------------------------------
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")

    # Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_MODEL")

    # OpenAI-compatible
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")

    # --- Embeddings ----------------------------------------------------------
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )

    # --- RAG -----------------------------------------------------------------
    chroma_persist_dir: str = Field(default="./data/chroma_db", alias="CHROMA_PERSIST_DIR")
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP")
    dense_weight: float = Field(default=0.6, alias="DENSE_WEIGHT")
    sparse_weight: float = Field(default=0.4, alias="SPARSE_WEIGHT")
    top_k_retrieval: int = Field(default=10, alias="TOP_K_RETRIEVAL")
    top_k_rerank: int = Field(default=5, alias="TOP_K_RERANK")

    # --- Database ------------------------------------------------------------
    database_url: str = Field(default="sqlite:///./data/diagnostic_copilot.db", alias="DATABASE_URL")

    # --- Backend -------------------------------------------------------------
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    backend_api_url: str = Field(default="http://localhost:8000", alias="BACKEND_API_URL")

    # --- Logging -------------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Security ------------------------------------------------------------
    max_image_size_mb: int = Field(default=10, alias="MAX_IMAGE_SIZE_MB")
    allowed_image_types: str = Field(default="png,jpg,jpeg", alias="ALLOWED_IMAGE_TYPES")
    temp_image_dir: str = Field(default="./data/temp_images", alias="TEMP_IMAGE_DIR")

    # --- Vision Provider -----------------------------------------------------
    vision_provider: str = Field(default="gemini", alias="VISION_PROVIDER")
    vision_model: str = Field(default="gemini-3.8-flash", alias="VISION_MODEL")

    # --- Paths ---------------------------------------------------------------
    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        return _PROJECT_ROOT / "data"

    @property
    def raw_data_dir(self) -> Path:
        return _PROJECT_ROOT / "data" / "raw"

    @property
    def processed_data_dir(self) -> Path:
        return _PROJECT_ROOT / "data" / "processed"

    @property
    def demo_data_dir(self) -> Path:
        return _PROJECT_ROOT / "data" / "demo"

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    class Config:
        env_file = ".env"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
