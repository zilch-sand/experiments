"""Load and query pricing data from the llm-prices submodule."""

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelPrice:
    model_id: str
    name: str
    vendor: str
    input_per_mtok: float  # $ per million tokens
    output_per_mtok: float
    input_cached_per_mtok: float | None = None

    @property
    def input_per_token(self) -> float:
        return self.input_per_mtok / 1_000_000

    @property
    def output_per_token(self) -> float:
        return self.output_per_mtok / 1_000_000

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, cached_input_tokens: int = 0
    ) -> float:
        cost = (input_tokens - cached_input_tokens) * self.input_per_token
        cost += output_tokens * self.output_per_token
        if cached_input_tokens and self.input_cached_per_mtok is not None:
            cost += cached_input_tokens * (self.input_cached_per_mtok / 1_000_000)
        return cost


# Map from vendor names used in llm-prices to Vertex AI model prefixes
VERTEX_MODEL_MAP: dict[str, dict[str, str]] = {
    "google": {},  # Gemini models use their IDs directly on Vertex
    "anthropic": {  # Claude models on Vertex use a specific format
        "claude-3.7-sonnet": "claude-3-7-sonnet@20250219",
        "claude-3.5-sonnet": "claude-3-5-sonnet-v2@20241022",
        "claude-3-opus": "claude-3-opus@20240229",
        "claude-3-haiku": "claude-3-haiku@20240307",
        "claude-3.5-haiku": "claude-3-5-haiku@20241022",
        "claude-sonnet-4.5": "claude-sonnet-4-5@20250514",
        "claude-opus-4": "claude-opus-4@20250514",
    },
}


def _prices_dir() -> Path:
    return Path(__file__).parent.parent / "llm-prices" / "data"


def load_all_prices() -> dict[str, ModelPrice]:
    """Load pricing for all models, keyed by llm-prices model id."""
    prices: dict[str, ModelPrice] = {}
    data_dir = _prices_dir()
    if not data_dir.exists():
        return prices
    for json_file in sorted(data_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        vendor = data.get("vendor", json_file.stem)
        for model in data.get("models", []):
            model_id = model["id"]
            history = model.get("price_history", [])
            if not history:
                continue
            latest = history[0]
            prices[model_id] = ModelPrice(
                model_id=model_id,
                name=model.get("name", model_id),
                vendor=vendor,
                input_per_mtok=latest.get("input", 0),
                output_per_mtok=latest.get("output", 0),
                input_cached_per_mtok=latest.get("input_cached"),
            )
    return prices


def get_vertex_models() -> list[dict]:
    """Return models available on Vertex AI with pricing info."""
    all_prices = load_all_prices()
    models = []

    # Google models (Gemini) - available directly on Vertex
    for mid, price in all_prices.items():
        if price.vendor == "google" and "gemini" in mid:
            models.append({
                "id": mid,
                "vertex_id": f"vertex_ai/{mid}",
                "name": price.name,
                "vendor": "Google",
                "price": price,
            })

    # Anthropic models on Vertex AI
    for llm_id, vertex_id in VERTEX_MODEL_MAP.get("anthropic", {}).items():
        if llm_id in all_prices:
            price = all_prices[llm_id]
            models.append({
                "id": llm_id,
                "vertex_id": f"vertex_ai/{vertex_id}",
                "name": price.name,
                "vendor": "Anthropic",
                "price": price,
            })

    # Llama models on Vertex (Model Garden)
    llama_models = [
        {
            "id": "llama-3.1-405b",
            "vertex_id": "vertex_ai/meta/llama-3.1-405b-instruct-maas",
            "name": "Llama 3.1 405B",
            "vendor": "Meta",
        },
        {
            "id": "llama-3.1-70b",
            "vertex_id": "vertex_ai/meta/llama-3.1-70b-instruct-maas",
            "name": "Llama 3.1 70B",
            "vendor": "Meta",
        },
        {
            "id": "llama-3.1-8b",
            "vertex_id": "vertex_ai/meta/llama-3.1-8b-instruct-maas",
            "name": "Llama 3.1 8B",
            "vendor": "Meta",
        },
    ]
    # Llama pricing on Vertex (approximate, per 1M tokens)
    llama_prices = {
        "llama-3.1-405b": (5.33, 16.0),
        "llama-3.1-70b": (2.56, 3.58),
        "llama-3.1-8b": (0.20, 0.20),
    }
    for m in llama_models:
        inp, out = llama_prices.get(m["id"], (0, 0))
        m["price"] = ModelPrice(
            model_id=m["id"],
            name=m["name"],
            vendor="Meta",
            input_per_mtok=inp,
            output_per_mtok=out,
        )
        models.append(m)

    return models


def estimate_dataset_cost(
    price: ModelPrice,
    avg_input_tokens: float,
    avg_output_tokens: float,
    num_rows: int,
    cached_input_tokens: int = 0,
) -> float:
    """Estimate total cost for classifying a full dataset."""
    per_row = price.estimate_cost(
        int(avg_input_tokens), int(avg_output_tokens), cached_input_tokens
    )
    return per_row * num_rows


def format_cost(cost: float) -> str:
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.2f}"
