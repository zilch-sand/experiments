"""Fuzzy matching for classification results against known categories."""

from rapidfuzz import fuzz, process


def fuzzy_match_label(
    prediction: str,
    categories: list[str],
    threshold: int = 60,
) -> str | None:
    """Match a prediction to the closest category using fuzzy matching.

    Returns the matched category or None if no match above threshold.
    """
    if not prediction or not categories:
        return None

    prediction = prediction.strip()

    # Exact match first (case-insensitive)
    for cat in categories:
        if prediction.lower() == cat.lower():
            return cat

    # Fuzzy match
    result = process.extractOne(
        prediction, categories, scorer=fuzz.ratio, score_cutoff=threshold
    )
    if result:
        return result[0]
    return None


def fuzzy_match_multi_label(
    prediction: str,
    categories: list[str],
    delimiter: str = "|",
    threshold: int = 60,
) -> list[str]:
    """Match multi-label predictions to categories.

    Splits prediction by delimiter and fuzzy-matches each part.
    """
    if not prediction:
        return []

    parts = [p.strip() for p in prediction.split(delimiter) if p.strip()]
    matched = []
    for part in parts:
        match = fuzzy_match_label(part, categories, threshold)
        if match and match not in matched:
            matched.append(match)
    return matched


def find_safe_delimiter(categories: list[str]) -> str:
    """Find a delimiter that doesn't appear in any category label."""
    candidates = ["|", "||", ";;", "###", "^^^"]
    for delim in candidates:
        if not any(delim in cat for cat in categories):
            return delim
    return "|||"
