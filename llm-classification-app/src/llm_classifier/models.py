"""
Model registry with pricing loaded from llm-prices JSON files.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import LLM_PRICES_DATA_DIR


@dataclass
class ModelConfig:
    id: str
    display_name: str
    provider: str  # "google" | "anthropic" | "meta"
    vertex_model_id: str
    supports_thinking: bool = False
    thinking_param_name: str = ""  # "thinking" for Claude, "thought" for Gemini
    max_tokens_default: int = 8192


# ---------------------------------------------------------------------------
# Pricing loader
# ---------------------------------------------------------------------------

_price_cache: dict[str, tuple[float, float]] = {}


def _load_prices() -> None:
    """Load all vendor pricing files into _price_cache keyed by model id."""
    if _price_cache:
        return
    data_dir = Path(LLM_PRICES_DATA_DIR)
    if not data_dir.exists():
        return
    for json_file in data_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
            for model in data.get("models", []):
                history = model.get("price_history", [])
                if history:
                    latest = history[0]
                    _price_cache[model["id"]] = (
                        float(latest.get("input") or 0),
                        float(latest.get("output") or 0),
                    )
        except Exception:
            pass


def get_price(model_id: str) -> tuple[float, float]:
    """Return (input_price_per_million, output_price_per_million) for a model id."""
    _load_prices()
    return _price_cache.get(model_id, (0.0, 0.0))


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated cost in USD."""
    inp, out = get_price(model_id)
    return (inp * input_tokens + out * output_tokens) / 1_000_000


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

MODELS: dict[str, ModelConfig] = {
    "Gemini 2.0 Flash": ModelConfig(
        id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        provider="google",
        vertex_model_id="gemini-2.0-flash-001",
        supports_thinking=False,
        max_tokens_default=8192,
    ),
    "Gemini 2.0 Flash Lite": ModelConfig(
        id="gemini-2.0-flash-lite",
        display_name="Gemini 2.0 Flash Lite",
        provider="google",
        vertex_model_id="gemini-2.0-flash-lite-001",
        supports_thinking=False,
        max_tokens_default=8192,
    ),
    "Gemini 2.5 Pro": ModelConfig(
        id="gemini-2.5-pro-preview-03-25",
        display_name="Gemini 2.5 Pro",
        provider="google",
        vertex_model_id="gemini-2.5-pro-preview-03-25",
        supports_thinking=True,
        thinking_param_name="thought",
        max_tokens_default=16000,
    ),
    "Claude 3.5 Sonnet (Vertex)": ModelConfig(
        id="claude-3.5-sonnet",
        display_name="Claude 3.5 Sonnet (Vertex)",
        provider="anthropic",
        vertex_model_id="claude-3-5-sonnet@20241022",
        supports_thinking=False,
        max_tokens_default=8192,
    ),
    "Claude 3.7 Sonnet (Vertex)": ModelConfig(
        id="claude-3.7-sonnet",
        display_name="Claude 3.7 Sonnet (Vertex)",
        provider="anthropic",
        vertex_model_id="claude-3-7-sonnet@20250219",
        supports_thinking=True,
        thinking_param_name="thinking",
        max_tokens_default=16000,
    ),
    "Llama 3.1 405B (Vertex)": ModelConfig(
        id="llama-3.1-405b",
        display_name="Llama 3.1 405B (Vertex)",
        provider="meta",
        vertex_model_id="meta/llama3-405b-instruct-maas",
        supports_thinking=False,
        max_tokens_default=8192,
    ),
    "Llama 3.3 70B (Vertex)": ModelConfig(
        id="llama-3.3-70b",
        display_name="Llama 3.3 70B (Vertex)",
        provider="meta",
        vertex_model_id="meta/llama-3.3-70b-instruct-maas",
        supports_thinking=False,
        max_tokens_default=8192,
    ),
}

# Convenience: model id -> config
MODELS_BY_ID: dict[str, ModelConfig] = {m.id: m for m in MODELS.values()}
