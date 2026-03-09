"""Classification logic: single-label, multi-label, token counting."""

import json
import time
from dataclasses import dataclass

import litellm
import pandas as pd

from backend.fuzzy_match import fuzzy_match_label, fuzzy_match_multi_label, find_safe_delimiter
from backend.models import ModelConfig
from backend.prompt import PromptTemplate


@dataclass
class ClassificationResult:
    row_index: int
    raw_response: str
    matched_label: str | list[str]
    input_tokens: int
    output_tokens: int


def classify_single_row(
    model_config: ModelConfig,
    prompt_text: str,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
) -> ClassificationResult:
    """Classify a single row using litellm."""
    kwargs = model_config.to_litellm_kwargs()

    response = litellm.completion(
        messages=[{"role": "user", "content": prompt_text}],
        **kwargs,
    )

    raw = response.choices[0].message.content.strip()
    usage = response.usage

    if multi_label:
        matched = fuzzy_match_multi_label(raw, categories, delimiter)
    else:
        matched = fuzzy_match_label(raw, categories) or raw

    return ClassificationResult(
        row_index=0,
        raw_response=raw,
        matched_label=matched,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )


def classify_rows(
    df: pd.DataFrame,
    model_config: ModelConfig,
    prompt_template: PromptTemplate,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
    max_rows: int | None = None,
    progress_callback=None,
) -> list[ClassificationResult]:
    """Classify multiple rows with progress tracking.

    Args:
        df: DataFrame to classify
        model_config: Model configuration
        prompt_template: Prompt template with placeholders
        categories: Classification categories
        multi_label: Whether to allow multiple labels
        delimiter: Delimiter for multi-label output
        max_rows: Limit number of rows (for testing)
        progress_callback: Callable(current, total) for progress updates
    """
    rows_to_process = df.head(max_rows) if max_rows else df
    total = len(rows_to_process)
    results = []

    for idx, (_, row) in enumerate(rows_to_process.iterrows()):
        prompt_text = prompt_template.render(
            row.to_dict(), categories, multi_label, delimiter
        )

        result = classify_single_row(
            model_config, prompt_text, categories, multi_label, delimiter
        )
        result.row_index = idx

        results.append(result)

        if progress_callback:
            progress_callback(idx + 1, total)

    return results


def count_tokens_for_prompt(prompt_text: str, model_id: str) -> int:
    """Estimate token count for a prompt using litellm.

    Falls back to character-based estimation (~4 chars/token) if
    litellm token counting fails (e.g., unsupported model, missing tokenizer).
    """
    try:
        return litellm.token_counter(model=model_id, text=prompt_text)
    except Exception:
        return len(prompt_text) // 4


def estimate_tokens_from_sample(
    df: pd.DataFrame,
    prompt_template: PromptTemplate,
    categories: list[str],
    model_id: str,
    sample_size: int = 5,
) -> dict:
    """Estimate average token counts from a sample of rows."""
    sample = df.head(min(sample_size, len(df)))
    token_counts = []

    for _, row in sample.iterrows():
        prompt_text = prompt_template.render(row.to_dict(), categories)
        tokens = count_tokens_for_prompt(prompt_text, "vertex_ai/" + model_id)
        token_counts.append(tokens)

    avg_input = sum(token_counts) / len(token_counts) if token_counts else 0
    return {
        "avg_input_tokens": avg_input,
        "sample_counts": token_counts,
        "total_rows": len(df),
        "estimated_total_input_tokens": avg_input * len(df),
    }


def apply_results_to_dataframe(
    df: pd.DataFrame,
    results: list[ClassificationResult],
    column_name: str = "classification",
    multi_label: bool = False,
    delimiter: str = "|",
) -> pd.DataFrame:
    """Apply classification results to a copy of the DataFrame."""
    df_out = df.copy()
    df_out[column_name] = None
    df_out["raw_response"] = None

    for result in results:
        if result.row_index < len(df_out):
            if multi_label and isinstance(result.matched_label, list):
                df_out.at[result.row_index, column_name] = delimiter.join(
                    result.matched_label
                )
            else:
                df_out.at[result.row_index, column_name] = result.matched_label
            df_out.at[result.row_index, "raw_response"] = result.raw_response

    return df_out
