"""Arena mode: compare multiple models and judge results."""

import pandas as pd
import litellm

from backend.classifier import classify_rows, ClassificationResult
from backend.models import ModelConfig
from backend.prompt import PromptTemplate
from backend.pricing import estimate_dataset_cost, format_cost


DEFAULT_JUDGE_PROMPT = """You are an expert judge evaluating text classification quality.

For each row, multiple models have classified a piece of text. Evaluate which model 
produced the best classification.

Consider:
1. Accuracy: Does the classification match the text content?
2. Specificity: Is the classification appropriately specific?
3. Consistency: Is the classification style consistent?

For each row, provide:
- The best model name
- A brief justification (1 sentence)

Respond in JSON format:
{{"evaluations": [{{"row": 0, "best_model": "model_name", "reason": "..."}}]}}

Here are the classifications to evaluate:

{classifications}"""


def run_arena(
    df: pd.DataFrame,
    model_configs: list[ModelConfig],
    prompt_template: PromptTemplate,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
    max_rows: int = 10,
    progress_callback=None,
) -> dict:
    """Run classification with multiple models for comparison.

    Returns a dict with results from each model and aggregated data.
    """
    all_results = {}
    token_stats = {}
    total_models = len(model_configs)

    for model_idx, config in enumerate(model_configs):
        model_key = f"{config.display_name} (T={config.temperature}"
        if config.thinking_level:
            model_key += f", think={config.thinking_level}"
        model_key += ")"

        def model_progress(current, total):
            if progress_callback:
                overall = (model_idx * max_rows + current) / (total_models * max_rows)
                progress_callback(overall)

        results = classify_rows(
            df=df,
            model_config=config,
            prompt_template=prompt_template,
            categories=categories,
            multi_label=multi_label,
            delimiter=delimiter,
            max_rows=max_rows,
            progress_callback=model_progress,
        )

        all_results[model_key] = results

        # Calculate token stats
        total_input = sum(r.input_tokens for r in results)
        total_output = sum(r.output_tokens for r in results)
        avg_input = total_input / len(results) if results else 0
        avg_output = total_output / len(results) if results else 0

        token_stats[model_key] = {
            "avg_input_tokens": avg_input,
            "avg_output_tokens": avg_output,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "sample_cost": config.price.estimate_cost(total_input, total_output)
            if config.price
            else 0,
            "estimated_full_cost": estimate_dataset_cost(
                config.price, avg_input, avg_output, len(df)
            )
            if config.price
            else 0,
        }

    return {
        "results": all_results,
        "token_stats": token_stats,
        "num_rows_tested": min(max_rows, len(df)),
    }


def judge_arena_results(
    arena_results: dict,
    df: pd.DataFrame,
    prompt_template: PromptTemplate,
    categories: list[str],
    judge_config: ModelConfig,
    judge_prompt: str = DEFAULT_JUDGE_PROMPT,
    max_rows: int = 10,
) -> str:
    """Use a judge model to evaluate arena results.

    Categories are excluded from the judge prompt to avoid biasing
    the evaluation — the judge should assess quality based solely
    on how well each classification matches the source text.
    """
    # Build classification summary for judge
    classifications_text = ""
    rows_to_show = min(max_rows, len(df))

    for row_idx in range(rows_to_show):
        row = df.iloc[row_idx]
        # Show the text columns used in the prompt
        cols_used = prompt_template.columns_used
        text_preview = " | ".join(
            f"{col}: {row.get(col, 'N/A')}" for col in cols_used
        )
        classifications_text += f"\n--- Row {row_idx} ---\n"
        classifications_text += f"Text: {text_preview}\n"

        for model_key, results in arena_results["results"].items():
            if row_idx < len(results):
                label = results[row_idx].matched_label
                if isinstance(label, list):
                    label = " | ".join(label)
                classifications_text += f"  {model_key}: {label}\n"

    final_prompt = judge_prompt.format(classifications=classifications_text)

    kwargs = judge_config.to_litellm_kwargs()
    kwargs["max_tokens"] = 4096

    response = litellm.completion(
        messages=[{"role": "user", "content": final_prompt}],
        **kwargs,
    )

    return response.choices[0].message.content.strip()


def export_arena_data(
    arena_results: dict,
    df: pd.DataFrame,
    prompt_template: PromptTemplate,
    max_rows: int = 10,
) -> pd.DataFrame:
    """Export arena comparison data as a DataFrame."""
    rows = []
    rows_to_export = min(max_rows, len(df))

    for row_idx in range(rows_to_export):
        row_data = {}
        # Include columns used in the prompt
        for col in prompt_template.columns_used:
            row_data[col] = df.iloc[row_idx].get(col, "")

        # Add each model's classification
        for model_key, results in arena_results["results"].items():
            if row_idx < len(results):
                label = results[row_idx].matched_label
                if isinstance(label, list):
                    label = " | ".join(label)
                row_data[f"classification_{model_key}"] = label
                row_data[f"raw_{model_key}"] = results[row_idx].raw_response

        rows.append(row_data)

    return pd.DataFrame(rows)
