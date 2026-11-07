"""Small model interface for the deposit assistant.

Add another provider by implementing ``generate_text``; callers need not know
which SDK the provider uses. User text is sent to the configured provider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class ModelError(Exception):
    """A configuration or model request failed."""


@dataclass(frozen=True)
class ModelResponse:
    text: str
    model: str


class ModelClient(Protocol):
    def generate_text(self, prompt: str) -> ModelResponse: ...
    def generate_json(self, prompt: str, schema: dict) -> ModelResponse: ...


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ModelError("Set GEMINI_API_KEY before using the Gemini model.")
        if not model.strip():
            raise ModelError("Set GEMINI_MODEL to an available model ID.")
        try:
            from google import genai
        except ImportError as exc:
            raise ModelError(
                "The Google Gen AI SDK is not installed. Run: pip install -r requirements.txt"
            ) from exc
        self.model = model
        self._client = genai.Client(api_key=api_key)

    def generate_text(self, prompt: str) -> ModelResponse:
        return self._generate(prompt)

    def generate_json(self, prompt: str, schema: dict) -> ModelResponse:
        return self._generate(prompt, schema)

    def _generate(self, prompt: str, schema: dict | None = None) -> ModelResponse:
        if not prompt.strip():
            raise ModelError("The prompt cannot be empty.")
        try:
            config = {"response_mime_type": "application/json", "response_json_schema": schema} if schema else None
            result = self._client.models.generate_content(model=self.model, contents=prompt, config=config)
            response_text = result.text
        except Exception as exc:
            # Surface a safe error category without printing credentials or request data.
            status = getattr(exc, "code", None)
            if status == 400:
                detail = "HTTP 400: The API rejected the request; check the key and model configuration."
            elif status in (401, 403):
                detail = f"HTTP {status}: Authentication or access denied; check the API key and project access."
            elif status == 404:
                detail = "HTTP 404: The configured model was not found or is unavailable to this account."
            elif status == 429:
                detail = "HTTP 429: Rate limit or quota exceeded; check quota and billing in Google AI Studio."
            elif isinstance(status, int) and 500 <= status < 600:
                detail = f"HTTP {status}: The model provider is temporarily unavailable."
            else:
                detail = f"{type(exc).__name__}: Check network connectivity and model configuration."
            raise ModelError(
                f"Model request failed. {detail}"
            ) from exc
        if not response_text or not response_text.strip():
            raise ModelError("The model returned no text. Try again or check the model configuration.")
        return ModelResponse(text=response_text.strip(), model=self.model)


def create_client() -> ModelClient:
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider != "gemini":
        raise ModelError(f"Unsupported provider: {provider!r}. Currently supported: gemini.")
    return GeminiClient(
        api_key=os.getenv("GEMINI_API_KEY", ""),
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    )
