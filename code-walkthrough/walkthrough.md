# LLM Classification App — Code Walkthrough

*2026-03-03T02:21:48Z by Showboat 0.6.1*
<!-- showboat-id: 8645b335-0171-443f-a860-dedb57370206 -->

## Overview

The `llm-classification-app` is a Streamlit web application for classifying text with large language models (LLMs). It targets **Vertex AI** and supports Google (Gemini), Anthropic (Claude), and Meta (Llama) models via the `litellm` abstraction layer.

The app has three main modes:
- **🏷️ Classify** — interactive single/full-dataset classification
- **🏟️ Arena** — side-by-side comparison of multiple models
- **📦 Batch Jobs** — asynchronous batch processing via Vertex AI's batch prediction API

### Directory structure

```bash
find /home/runner/work/experiments/experiments/llm-classification-app -type f -name '*.py' | sort
```

```output
/home/runner/work/experiments/experiments/llm-classification-app/app.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/__init__.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/arena.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/classifier.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/feedback.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/fuzzy_match.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/models.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/pricing.py
/home/runner/work/experiments/experiments/llm-classification-app/backend/prompt.py
/home/runner/work/experiments/experiments/llm-classification-app/tests/test_batch.py
/home/runner/work/experiments/experiments/llm-classification-app/tests/test_fuzzy_match.py
/home/runner/work/experiments/experiments/llm-classification-app/tests/test_pricing.py
/home/runner/work/experiments/experiments/llm-classification-app/tests/test_prompt.py
```

The `backend/` package contains all business logic — completely decoupled from Streamlit. The separation means the same backend could be served by FastAPI or called from tests without any UI dependency. `app.py` is only glue code.

---

## Step 1: Prompt templates (`backend/prompt.py`)

Every classification starts with a prompt template. The template uses Python `str.format`-style placeholders: `{column_name}` for dataset columns and `{label_options}` as a special placeholder that gets replaced with the list of valid categories.

```bash
sed -n '1,40p' /home/runner/work/experiments/experiments/llm-classification-app/backend/prompt.py
```

```output
"""Prompt template handling with {col} placeholders and {label_options}."""

import re
from dataclasses import dataclass, field


DEFAULT_CLASSIFICATION_PROMPT = """Classify the following text into one of the provided categories.

Text to classify:
{text}

Categories: {label_options}

Respond with ONLY the category label, nothing else."""

DEFAULT_MULTI_LABEL_PROMPT = """Classify the following text into one or more of the provided categories.

Text to classify:
{text}

Categories: {label_options}

Respond with the applicable category labels separated by '|'. Include ONLY the labels, nothing else."""


@dataclass
class PromptTemplate:
    template: str
    columns_used: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.columns_used = self.extract_columns()

    def extract_columns(self) -> list[str]:
        """Extract column placeholders from template, excluding label_options."""
        placeholders = re.findall(r"\{(\w+)\}", self.template)
        return [p for p in placeholders if p != "label_options"]

    def validate(self, available_columns: list[str]) -> list[str]:
        """Validate template against available columns. Returns list of errors."""
```

The two default prompts show the pattern clearly: the user writes a template that references their own CSV column names (`{text}`, or whatever column holds the content) plus `{label_options}`. Single-label mode instructs the model to respond with *one* label; multi-label mode asks for labels separated by a delimiter.

`PromptTemplate` is a dataclass that wraps the raw string. On construction it calls `extract_columns()` — a regex over `{word}` patterns that filters out the reserved `label_options` placeholder. This column list is later used for validation and for building the UI's 'prompt preview'.

```bash
sed -n '62,85p' /home/runner/work/experiments/experiments/llm-classification-app/backend/prompt.py
```

```output
        delimiter: str = "|",
    ) -> str:
        """Render the prompt for a specific row."""
        label_str = ", ".join(categories)
        values = {"label_options": label_str}
        for col in self.columns_used:
            values[col] = str(row.get(col, f"[missing:{col}]"))
        try:
            return self.template.format(**values)
        except KeyError as e:
            return f"Error rendering prompt: missing key {e}"

    def preview(
        self, first_row: dict, categories: list[str], multi_label: bool = False,
        delimiter: str = "|",
    ) -> str:
        """Preview the prompt using the first row of data."""
        return self.render(first_row, categories, multi_label, delimiter)


FEEDBACK_PROMPT = """You are an expert in prompt engineering and text classification. 
Please review the following classification prompt and categories, then provide feedback.

PROMPT TEMPLATE:
```

`render()` builds a `values` dict with `label_options` set to a comma-joined category string, then adds each referenced column's value from the row. Missing columns are substituted with a `[missing:col]` marker rather than raising, so partial data still produces a visible (if imperfect) prompt. `template.format(**values)` does the final substitution.

---

## Step 2: Model configuration (`backend/models.py` + `backend/pricing.py`)

Before calling any LLM, the app needs to know *which* model to call and *how much it costs*. These two concerns are split across two files.

```bash
sed -n '1,50p' /home/runner/work/experiments/experiments/llm-classification-app/backend/models.py
```

```output
"""Model configuration and Vertex AI integration via litellm."""

from dataclasses import dataclass, field
from backend.pricing import get_vertex_models, ModelPrice


@dataclass
class ModelConfig:
    """Configuration for a model run."""
    vertex_id: str
    display_name: str
    vendor: str
    price: ModelPrice | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    thinking_level: str | None = None  # "low", "medium", "high" for supported models
    extra_params: dict = field(default_factory=dict)

    def to_litellm_kwargs(self) -> dict:
        """Convert to kwargs for litellm.completion()."""
        kwargs = {
            "model": self.vertex_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        # Thinking budget / effort for models that support it
        if self.thinking_level:
            if "gemini" in self.vertex_id.lower():
                # Gemini uses thinking_config
                budget_map = {"low": 1024, "medium": 8192, "high": 32768}
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": budget_map.get(self.thinking_level, 8192),
                }
            elif "claude" in self.vertex_id.lower():
                # Claude uses extended thinking
                budget_map = {"low": 2048, "medium": 10000, "high": 32000}
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": budget_map.get(self.thinking_level, 10000),
                }
        kwargs.update(self.extra_params)
        return kwargs


# Thinking level options per vendor
THINKING_LEVELS = {
    "Google": ["none", "low", "medium", "high"],
    "Anthropic": ["none", "low", "medium", "high"],
    "Meta": [],  # Llama doesn't support thinking
```

`ModelConfig` is a dataclass that holds everything `litellm.completion()` needs: the Vertex AI model ID, temperature, max_tokens, and an optional `thinking_level`. The `to_litellm_kwargs()` method converts it to a ready-to-unpack dict.

The `thinking_level` handling is the interesting part: Gemini and Claude both support extended reasoning ('thinking'), but their APIs differ. Gemini expects a `thinking.budget_tokens` parameter; Claude expects the same structure but with different token budgets. The same three levels ('low', 'medium', 'high') map to different token budgets per vendor. Llama does not support thinking at all (`THINKING_LEVELS` has an empty list for Meta).

### Pricing (`backend/pricing.py`)

Pricing data comes from the `llm-prices` git submodule — a folder of JSON files, one per vendor, each with a `price_history` array (newest entry first). The `ModelPrice` dataclass and `load_all_prices()` loader turn those JSON files into Python objects.

```bash
sed -n '1,35p' /home/runner/work/experiments/experiments/llm-classification-app/backend/pricing.py
```

```output
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


```

`ModelPrice.estimate_cost()` supports prompt caching: if `cached_input_tokens` is provided, those tokens are billed at the cheaper cached rate (`input_cached_per_mtok`) and the rest at the full `input_per_mtok` rate. This lets the UI show a 'with 80% prompt caching' cost estimate alongside the baseline cost.

`get_vertex_models()` is where model discovery happens — it calls `load_all_prices()` then assembles three sections: Gemini models (passed through with their IDs directly), Anthropic models (remapped to Vertex's versioned IDs via `VERTEX_MODEL_MAP`), and Llama models (hardcoded with approximate pricing).

```bash
sed -n '47,80p' /home/runner/work/experiments/experiments/llm-classification-app/backend/pricing.py
```

```output
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
```

`load_all_prices()` silently skips JSON files it can't parse (corrupted or unexpected format) and models with no price history — the `if not data_dir.exists(): return prices` guard means the entire app still runs if the `llm-prices` submodule hasn't been initialised, just without cost estimates.

---

## Step 3: Classification pipeline (`backend/classifier.py`)

This is the core of the app. The data flow is: **row → rendered prompt → LLM call → raw text response → fuzzy-matched label → ClassificationResult**.

```bash
sed -n '16,55p' /home/runner/work/experiments/experiments/llm-classification-app/backend/classifier.py
```

```output
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


```

`classify_single_row` is deliberately thin: it calls `litellm.completion()` with the pre-rendered prompt text, extracts the raw string response, then delegates to the fuzzy-match layer. Both `raw_response` and `matched_label` are stored — the raw response is shown in the UI so users can see exactly what the model said before any normalisation.

The `usage.prompt_tokens` / `usage.completion_tokens` values are surfaced as `input_tokens` / `output_tokens` for cost tracking. `litellm` normalises these field names across vendors.

`classify_rows` wraps the single-row function in a loop with an optional `max_rows` cap (for test runs) and a `progress_callback` for the Streamlit progress bar:

```bash
sed -n '57,100p' /home/runner/work/experiments/experiments/llm-classification-app/backend/classifier.py
```

```output
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
```

The `progress_callback` is a simple `Callable(current, total)` — no Streamlit-specific code in the backend. `app.py` passes in a lambda that calls `st.progress()`; tests or a future FastAPI endpoint can pass in anything else, or `None`.

### Token estimation

The UI shows a cost estimate *before* running any classifications. `estimate_tokens_from_sample` renders the prompt for a small sample of rows, calls `litellm.token_counter()` on each, and averages the counts:

```bash
sed -n '100,140p' /home/runner/work/experiments/experiments/llm-classification-app/backend/classifier.py
```

```output
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
        tokens = count_tokens_for_prompt(prompt_text, model_id)
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
```

`count_tokens_for_prompt` tries `litellm.token_counter()` first, then silently falls back to `len(text) // 4` (the rough rule-of-thumb that ~4 characters ≈ 1 token). This means cost estimates always display even for models whose tokenizer isn't available locally.

---

## Step 4: Fuzzy label matching (`backend/fuzzy_match.py`)

LLMs don't always return exactly the label you asked for. A model might capitalise differently, add punctuation, or include extra words. `fuzzy_match.py` handles this with a two-stage approach: exact match first, then `rapidfuzz` Levenshtein ratio.

```bash
cat /home/runner/work/experiments/experiments/llm-classification-app/backend/fuzzy_match.py
```

```output
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
```

`fuzzy_match_label`: first tries a case-insensitive exact match (cheapest); if that fails, uses `rapidfuzz.process.extractOne` with a `score_cutoff=60`. Scores below 60 return `None`, which causes `classify_single_row` to fall back to the raw LLM response — preserving the original output rather than silently mapping to a wrong category.

`fuzzy_match_multi_label`: splits the response on the delimiter, fuzzy-matches each part independently, and deduplicates. A label can only appear once in the output even if the model repeated it.

`find_safe_delimiter` is called before sending the multi-label prompt to ensure the delimiter chosen doesn't appear inside any category name (which would cause incorrect splits). It tries `|`, `||`, `;;`, `###`, `^^^` in order.

---

## Step 5: Arena mode (`backend/arena.py`)

The arena runs the same classification task against multiple model configurations and compiles comparative results.

```bash
sed -n '34,105p' /home/runner/work/experiments/experiments/llm-classification-app/backend/arena.py
```

```output
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
```

`run_arena` iterates over each model config and calls `classify_rows` for it. The `model_progress` inner closure converts the per-model progress (0 to `max_rows`) into an overall progress fraction that covers all models in sequence: `(model_idx * max_rows + current) / (total_models * max_rows)`. This keeps the Streamlit progress bar smooth across multiple models.

Token stats are collected per model and include both the sample cost (actual tokens used on the test rows) and an extrapolated full-dataset cost estimate.

### The judge

After the arena, an optional 'judge' LLM evaluates each model's classifications. It receives all models' outputs formatted together and is asked to respond in JSON naming the best model per row:

```bash
sed -n '104,155p' /home/runner/work/experiments/experiments/llm-classification-app/backend/arena.py
```

```output
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
```

The judge receives each row's source text and all models' labels, but *not* the category list — deliberately, to avoid biasing it towards whichever label is listed first. The default judge prompt asks for JSON output (`{"evaluations": [{"row": 0, "best_model": ..., "reason": ...}]}`), which could be parsed programmatically for scoring, though the current UI just renders the raw markdown response.

---

## Step 6: Batch jobs (`backend/batch.py`)

For large datasets, calling the LLM API row-by-row is slow and can't be resumed if it fails partway through. The batch module uses Vertex AI's native batch prediction endpoint instead.

```bash
sed -n '20,75p' /home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py
```

```output
def _ensure_batch_dir():
    BATCH_STATE_DIR.mkdir(parents=True, exist_ok=True)


def save_batch_id(batch_id: str, metadata: dict | None = None):
    """Persist a batch ID to file for recovery."""
    _ensure_batch_dir()
    record = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(),
        "status": "submitted",
        **(metadata or {}),
    }
    filepath = BATCH_STATE_DIR / f"{batch_id}.json"
    filepath.write_text(json.dumps(record, indent=2))


def update_batch_status(batch_id: str, status: str, extra: dict | None = None):
    """Update the status of a tracked batch."""
    filepath = BATCH_STATE_DIR / f"{batch_id}.json"
    if filepath.exists():
        record = json.loads(filepath.read_text())
    else:
        record = {"batch_id": batch_id}
    record["status"] = status
    record["updated_at"] = datetime.now().isoformat()
    if extra:
        record.update(extra)
    filepath.write_text(json.dumps(record, indent=2))


def load_tracked_batches() -> list[dict]:
    """Load all tracked batch records."""
    _ensure_batch_dir()
    batches = []
    for f in BATCH_STATE_DIR.glob("*.json"):
        try:
            batches.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(batches, key=lambda b: b.get("created_at", ""), reverse=True)


def cleanup_batch(batch_id: str):
    """Remove batch tracking file after completion."""
    filepath = BATCH_STATE_DIR / f"{batch_id}.json"
    if filepath.exists():
        filepath.unlink()


def prepare_batch_requests(
    df: pd.DataFrame,
    model_config: ModelConfig,
    prompt_template: PromptTemplate,
    categories: list[str],
    multi_label: bool = False,
```

State persistence is simple but effective: each submitted batch gets its own JSON file in the `batch_state/` directory. `save_batch_id` creates the file on submission; `update_batch_status` patches it; `load_tracked_batches` scans the directory on every page load so the UI always reflects current state. `cleanup_batch` deletes the file when done.

This file-based approach means jobs survive Streamlit restarts and page reloads — no database needed.

`prepare_batch_requests` formats each row as a JSONL entry in the OpenAI batch format:

```bash
sed -n '70,105p' /home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py
```

```output
def prepare_batch_requests(
    df: pd.DataFrame,
    model_config: ModelConfig,
    prompt_template: PromptTemplate,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
) -> list[dict]:
    """Prepare batch request payloads for Vertex AI batch prediction.

    Returns a list of request dicts in the format expected by Vertex AI
    batch prediction (JSONL format).
    """
    requests = []
    for idx, (_, row) in enumerate(df.iterrows()):
        prompt_text = prompt_template.render(
            row.to_dict(), categories, multi_label, delimiter
        )
        request = {
            "custom_id": f"row-{idx}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model_config.vertex_id.replace("vertex_ai/", ""),
                "messages": [{"role": "user", "content": prompt_text}],
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
            },
        }
        requests.append(request)
    return requests


def submit_batch(
    requests: list[dict],
    model_config: ModelConfig,
```

Each request gets a `custom_id` of `row-{idx}` so results can be matched back to the original rows after the job completes. The `vertex_ai/` prefix is stripped from the model ID because the batch API expects the bare model name without the provider prefix that litellm uses for routing.

`submit_batch` writes the requests to a temp JSONL file, calls `litellm.create_batch()`, saves the returned batch ID, and cleans up the temp file in a `finally` block:

```bash
sed -n '103,145p' /home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py
```

```output
def submit_batch(
    requests: list[dict],
    model_config: ModelConfig,
    description: str = "",
) -> str:
    """Submit a batch job to Vertex AI.

    Returns the batch ID for tracking.
    """
    import tempfile

    # Write requests to a JSONL file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    ) as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")
        jsonl_path = f.name

    try:
        # Use litellm's batch API
        batch_response = litellm.create_batch(
            input_file_id=jsonl_path,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": description},
        )
        batch_id = batch_response.id

        # Save batch ID for recovery
        save_batch_id(batch_id, {
            "model": model_config.vertex_id,
            "description": description,
            "num_requests": len(requests),
        })

        return batch_id
    finally:
        os.unlink(jsonl_path)


def check_batch_status(batch_id: str) -> dict:
    """Check the status of a batch job."""
```

The temp file is always cleaned up (even if `litellm.create_batch` raises) because the `os.unlink` is in `finally`. The `24h` completion window is Vertex AI's standard batch prediction SLA.

When results are ready, `retrieve_batch_results` downloads them from Vertex, parses each JSONL line, extracts the model's response text, runs it through the same `fuzzy_match` pipeline as the interactive path, and returns a list of dicts that can be turned into a DataFrame. Importantly, it calls `update_batch_status` so the UI always reflects the correct state.

---

## Step 7: Prompt feedback (`backend/feedback.py`)

A small but useful feature: ask an LLM to critique your classification prompt and categories before running it on the full dataset.

```bash
cat /home/runner/work/experiments/experiments/llm-classification-app/backend/feedback.py
```

```output
"""AI feedback on prompts and categories."""

import litellm
from backend.models import ModelConfig
from backend.prompt import FEEDBACK_PROMPT


def get_prompt_feedback(
    model_config: ModelConfig,
    prompt_template: str,
    categories: list[str],
    multi_label: bool = False,
) -> str:
    """Get AI feedback on the classification prompt and categories."""
    classification_type = "multi-label" if multi_label else "single-label"
    categories_str = "\n".join(f"- {cat}" for cat in categories)

    feedback_prompt = FEEDBACK_PROMPT.format(
        prompt=prompt_template,
        categories=categories_str,
        classification_type=classification_type,
    )

    kwargs = model_config.to_litellm_kwargs()
    # Override max_tokens for feedback - needs room for detailed response
    kwargs["max_tokens"] = 4096

    response = litellm.completion(
        messages=[{"role": "user", "content": feedback_prompt}],
        **kwargs,
    )

    return response.choices[0].message.content.strip()
```

`get_prompt_feedback` renders the `FEEDBACK_PROMPT` template (defined in `prompt.py`) with the user's prompt, categories, and classification type, then makes a litellm call with an overridden `max_tokens=4096` — larger than the classification calls, because feedback can be detailed. The function returns raw markdown from the model, which the UI renders directly with `st.markdown()`.

The `FEEDBACK_PROMPT` asks for structured critique across six dimensions: clarity, category overlap, missing catch-all category, prompt quality, category count, and a RAG recommendation if the prompt is very long.

---

## Step 8: The Streamlit frontend (`app.py`)

`app.py` is intentionally thin — its job is to collect user input, call backend functions, and display results. Here's how it's structured:

### Session state initialisation

Streamlit re-runs the entire script on every user interaction, so mutable state (the loaded DataFrame, classification results, arena results) must live in `st.session_state`:

```bash
sed -n '54,85p' /home/runner/work/experiments/experiments/llm-classification-app/app.py
```

```output

# ── Prompt caching helper ──────────────────────────────────────────────
def _prompt_cache_key(template: str, categories: list[str]) -> str:
    raw = template + "||" + "||".join(categories)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ── Session state defaults ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "results" not in st.session_state:
    st.session_state.results = None
if "arena_results" not in st.session_state:
    st.session_state.arena_results = None
if "prompt_cache" not in st.session_state:
    st.session_state.prompt_cache = {}


# ── Sidebar: Data Upload ───────────────────────────────────────────────
st.sidebar.title("📁 Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.sidebar.success(
        f"Loaded {len(st.session_state.df)} rows, "
        f"{len(st.session_state.df.columns)} columns"
    )

df = st.session_state.df

# ── Tabs ────────────────────────────────────────────────────────────────
tab_classify, tab_arena, tab_batch = st.tabs(
```

The `if 'key' not in st.session_state:` guards run on every script execution but only set the value on first load. A 12-character SHA-256 hash of the prompt + categories (`_prompt_cache_key`) is used as a dict key in `st.session_state.prompt_cache` — this stores the last used prompt/categories so the Arena and Batch tabs can pre-populate their fields from whatever was typed in the Classify tab.

The file uploader is in the sidebar so it persists across all three tabs. CSV upload stores the DataFrame in `st.session_state.df`, which all three tabs read from.

### The three tabs

`st.tabs()` declares all three tabs upfront; each is populated in its own `with tab_*:` block:

```bash
grep -n 'with tab_\|st\.tabs\|st\.header' /home/runner/work/experiments/experiments/llm-classification-app/app.py
```

```output
85:tab_classify, tab_arena, tab_batch = st.tabs(
93:with tab_classify:
94:    st.header("Text Classification")
378:with tab_arena:
379:    st.header("🏟️ Model Arena")
584:with tab_batch:
585:    st.header("📦 Batch Processing")
```

**Classify tab** (lines 93–376): Two-column layout. Left column: prompt template textarea with live validation + warnings, categories textarea, prompt preview (rendered from row 1). Right column: model selector, temperature slider, thinking level selector (only shown for Google/Anthropic), cost estimate, AI feedback button, test-run button (up to 50 rows), and a 'classify full dataset + download' button.

**Arena tab** (lines 378–582): Left column configures the shared prompt/categories; right column builds N model configurations (2–6) each with their own model, temperature, and thinking level selectors. Cost estimates are shown before running. After running, results are shown in a comparison table plus a token/cost stats table. An optional judge evaluation renders below the results.

**Batch tab** (lines 584–end): Left column submits new batch jobs; right column shows all tracked jobs from `load_tracked_batches()`, with per-job expanders containing 'Check Status', 'Get Results', and 'Cleanup' buttons.

### Cost estimation in the Classify tab

The cost estimate is computed before the user runs any rows, using the token-sampling approach from `classifier.py`:

```bash
sed -n '185,225p' /home/runner/work/experiments/experiments/llm-classification-app/app.py
```

```output
            thinking_options = THINKING_LEVELS.get(vendor, [])

            temperature = st.slider(
                "Temperature", 0.0, 1.0, 0.0, 0.1, key="classify_temp"
            )

            thinking_level = None
            if thinking_options:
                thinking_level = st.select_slider(
                    "Thinking level",
                    options=thinking_options,
                    value="none",
                    key="classify_thinking",
                )

            model_config = create_model_config(
                selected_model,
                temperature=temperature,
                thinking_level=thinking_level,
            )

            # Token estimation
            st.subheader("Cost Estimate")
            if not errors and categories:
                token_info = estimate_tokens_from_sample(
                    df, prompt_template, categories,
                    model_config.vertex_id, sample_size=5,
                )
                avg_in = token_info["avg_input_tokens"]
                # Rough output estimate for classification
                avg_out = 20  # classifications are short

                st.metric("Avg input tokens/row", f"{avg_in:.0f}")
                st.metric("Total rows", len(df))

                if selected_model.get("price"):
                    price = selected_model["price"]
                    full_cost = estimate_dataset_cost(
                        price, avg_in, avg_out, len(df)
                    )
                    st.metric("Estimated total cost", format_cost(full_cost))
```

The cost estimate samples 5 rows to measure real token counts, then multiplies by total dataset size. Output tokens are assumed to be 20 (reasonable for classification — labels are short). If the model has a cached input price, a second estimate is shown assuming 80% of the input tokens are cached (a realistic scenario when all rows share the same prompt template and categories).

This estimate displays *reactively* — whenever the model, temperature, prompt, or categories change, Streamlit re-runs the script and the estimate updates automatically.

---

## End-to-end flow summary

Here's the complete data flow from CSV upload to downloaded results:

1. **Upload CSV** → stored in `st.session_state.df`
2. **Write prompt template** → `PromptTemplate` extracts column names, validates against DataFrame columns
3. **Enter categories** → `find_safe_delimiter` picks a safe delimiter for multi-label mode
4. **Select model** → `get_available_models()` + `create_model_config()` builds `ModelConfig`
5. **Preview cost** → `estimate_tokens_from_sample()` samples 5 rows, multiplies by dataset size and token price
6. **Run Test / Classify** → `classify_rows()` renders each prompt → `litellm.completion()` → `fuzzy_match_label()` → `ClassificationResult`
7. **Apply results** → `apply_results_to_dataframe()` joins labels back to the original DataFrame
8. **Download** → CSV download button with `st.download_button()`

For large datasets, steps 4–7 can be replaced by the batch path: `prepare_batch_requests()` → `submit_batch()` → poll `check_batch_status()` → `retrieve_batch_results()` (which itself runs fuzzy matching on the returned labels).

---

## Tests

The `tests/` folder covers the pure-Python backend modules (no Streamlit required):

```bash
ls /home/runner/work/experiments/experiments/llm-classification-app/tests/
```

```output
test_batch.py
test_fuzzy_match.py
test_pricing.py
test_prompt.py
```

Each test file covers one backend module:
- `test_fuzzy_match.py` — exact match, fuzzy match, below-threshold returns None, multi-label splitting, delimiter safety
- `test_prompt.py` — column extraction, validation errors, render with missing columns, multi-label preview
- `test_pricing.py` — cost calculation (with and without caching), dataset cost estimation
- `test_batch.py` — JSONL request formatting, batch state file creation/update/load/cleanup

None of the tests require LLM API calls or a running Streamlit server — the clean backend separation makes this possible.
