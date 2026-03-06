"""Load and query pricing data from the local llm_prices.json file."""

import json
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


_PRICES_FILE = Path(__file__).parent / "llm_prices.json"


def load_all_prices() -> dict[str, ModelPrice]:
    """Load pricing for all models, keyed by model id."""
    data = json.loads(_PRICES_FILE.read_text())
    prices: dict[str, ModelPrice] = {}
    for entry in data.get("prices", []):
        model_id = entry["id"]
        prices[model_id] = ModelPrice(
            model_id=model_id,
            name=entry.get("name", model_id),
            vendor=entry.get("vendor", ""),
            input_per_mtok=entry.get("input", 0),
            output_per_mtok=entry.get("output", 0),
            input_cached_per_mtok=entry.get("input_cached"),
        )
    return prices


def get_vertex_models() -> list[dict]:
    """Return models available on Vertex AI with pricing info."""
    data = json.loads(_PRICES_FILE.read_text())
    models = []
    for entry in data.get("prices", []):
        vertex_id = entry.get("vertex_id")
        if not vertex_id:
            continue
        price = ModelPrice(
            model_id=entry["id"],
            name=entry.get("name", entry["id"]),
            vendor=entry.get("vendor", ""),
            input_per_mtok=entry.get("input", 0),
            output_per_mtok=entry.get("output", 0),
            input_cached_per_mtok=entry.get("input_cached"),
        )
        models.append({
            "id": entry["id"],
            "vertex_id": vertex_id,
            "name": price.name,
            "vendor": entry.get("vendor", "").capitalize(),
            "price": price,
        })
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
