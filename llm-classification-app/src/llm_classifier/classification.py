"""
Fuzzy label matching and row classification.
"""
from __future__ import annotations

from rapidfuzz import process, fuzz

from .config import FUZZY_THRESHOLD
from .models import ModelConfig


def fuzzy_match_label(
    response: str,
    categories: list[str],
    multi_label: bool,
    threshold: int = FUZZY_THRESHOLD,
) -> str | list[str]:
    """
    Match a model response string to the closest category/categories.

    For multi_label, the response is split on '|' and each part is matched
    independently.

    Returns a matched label string, a list of matched labels, or "UNMATCHED"
    when no match exceeds the threshold.
    """
    if not categories:
        return "UNMATCHED"

    def _match_one(text: str) -> str:
        text = text.strip()
        result = process.extractOne(text, categories, scorer=fuzz.WRatio)
        if result and result[1] >= threshold:
            return result[0]
        return "UNMATCHED"

    if multi_label:
        parts = [p.strip() for p in response.split("|") if p.strip()]
        return [_match_one(p) for p in parts] if parts else ["UNMATCHED"]

    return _match_one(response)


def classify_row(
    model_config: ModelConfig,
    prompt: str,
    categories: list[str],
    multi_label: bool,
    thinking_level: int | None,
) -> dict:
    """
    Classify a single row using the given model.

    Returns a dict with keys:
      raw_response, matched_label, input_tokens, output_tokens

    Raises on API errors.
    """
    from .vertex_client import call_model
    from .config import THINKING_BUDGETS

    thinking_budget = THINKING_BUDGETS.get(thinking_level or 0)

    result = call_model(
        model_config=model_config,
        prompt=prompt,
        system_prompt=(
            "You are an expert data classifier. "
            "Respond with only the category label(s) requested — no explanation."
        ),
        thinking_level=thinking_budget,
        max_tokens=model_config.max_tokens_default,
    )

    raw = result["text"].strip()
    matched = fuzzy_match_label(raw, categories, multi_label)

    return {
        "raw_response": raw,
        "matched_label": matched if isinstance(matched, str) else "|".join(matched),
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
