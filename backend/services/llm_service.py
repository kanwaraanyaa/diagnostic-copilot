"""
Configurable LLM service — supports Gemini, OpenAI-compatible, and Ollama.
"""

from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from abc import ABC, abstractmethod
from typing import Any

from config import get_settings
from logger import get_logger

log = get_logger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        """Generate text from a prompt."""
        ...

    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> dict[str, Any]:
        """Generate structured JSON from a prompt."""
        ...


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider."""

    def __init__(self) -> None:
        import google.generativeai as genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please add it to your .env file.")
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)
        self._model_name = settings.gemini_model
        log.info("gemini_provider_initialized", model=self._model_name)

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self._model.generate_content(full_prompt)
        return response.text

    def generate_json(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> dict[str, Any]:
        json_instruction = (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "Do not include markdown code fences or any other text. "
            "Output raw JSON only."
        )
        text = self.generate(prompt + json_instruction, system_prompt, **kwargs)
        return _parse_json_response(text)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible API provider."""

    def __init__(self) -> None:
        from openai import OpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set. Please add it to your .env file.")
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = settings.openai_model
        log.info("openai_provider_initialized", model=self._model)

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
        )
        return response.choices[0].message.content or ""

    def generate_json(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> dict[str, Any]:
        json_system = (system_prompt or "") + (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "Do not include markdown code fences or any other text."
        )
        text = self.generate(prompt, json_system, **kwargs)
        return _parse_json_response(text)


class OllamaProvider(BaseLLMProvider):
    """Ollama local model provider (uses OpenAI-compatible endpoint)."""

    def __init__(self) -> None:
        from openai import OpenAI

        settings = get_settings()
        self._client = OpenAI(
            api_key="ollama",
            base_url=f"{settings.ollama_base_url}/v1",
        )
        self._model = settings.ollama_model
        log.info("ollama_provider_initialized", model=self._model, base_url=settings.ollama_base_url)

    def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
        )
        return response.choices[0].message.content or ""

    def generate_json(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> dict[str, Any]:
        json_system = (system_prompt or "") + (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "Do not include markdown code fences or any other text."
        )
        text = self.generate(prompt, json_system, **kwargs)
        return _parse_json_response(text)


# ---- helpers ---------------------------------------------------------------

def _parse_json_response(text: str) -> dict[str, Any]:
    """Best-effort JSON parsing from LLM output."""
    cleaned = text.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        log.warning("json_parse_failed", text_preview=cleaned[:200])
        return {"raw_text": text, "parse_error": True}


# ---- factory ---------------------------------------------------------------

_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}

_provider_instance: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Return the configured LLM provider (singleton)."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_name = settings.llm_provider.lower()
    provider_cls = _PROVIDERS.get(provider_name)

    if provider_cls is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider_name}'. "
            f"Supported: {', '.join(_PROVIDERS.keys())}"
        )

    _provider_instance = provider_cls()
    return _provider_instance


def reset_llm_provider() -> None:
    """Reset the singleton (useful for testing)."""
    global _provider_instance
    _provider_instance = None
