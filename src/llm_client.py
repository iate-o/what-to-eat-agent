"""Thin OpenAI structured-output adapter with one parse retry."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)
PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LLMError(RuntimeError):
    """Friendly boundary error for model or structured parsing failures."""


def load_prompt(name: str, **values: str) -> str:
    template = (PROMPT_DIR / name).read_text(encoding="utf-8")
    for key, value in values.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("Add an OpenAI API key to use the recipe agent.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - environment setup boundary
            raise LLMError("The OpenAI package is not installed. Run pip install -r requirements.txt.") from exc
        self._client = OpenAI(api_key=key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def parse(self, prompt: str, schema: type[T]) -> T:
        last_error: Exception | None = None
        for _ in range(2):
            try:
                if hasattr(self._client.responses, "parse"):
                    response = self._client.responses.parse(
                        model=self.model,
                        input=[
                            {
                                "role": "system",
                                "content": "Return only the requested structured result. Never reveal hidden reasoning.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        text_format=schema,
                    )
                    parsed = response.output_parsed
                else:  # pragma: no cover - compatibility with earlier SDKs
                    response = self._client.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "Return only the requested structured result. Never reveal hidden reasoning.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        response_format=schema,
                    )
                    parsed = response.choices[0].message.parsed
                if parsed is None:
                    raise ValueError("Model returned no structured output")
                return parsed
            except Exception as exc:  # SDK errors vary by version
                last_error = exc
        raise LLMError(
            "The model could not return a valid structured response after one retry. "
            "Please try again."
        ) from last_error
