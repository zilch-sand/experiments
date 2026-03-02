# LLM Classification App

A **Shiny for Python** application for classifying tabular data using large language models via **Google Cloud Vertex AI**.

## Features

| Tab | Capability |
|---|---|
| **Setup & Test** | Upload CSV, build prompt with `{col}` placeholders, pick model + categories, run quick test |
| **Batch Run** | Submit full-dataset batch jobs to Vertex AI, monitor status, download results |
| **Arena** | Compare multiple models/settings head-to-head with a judge LLM |
| **AI Feedback** | Get GPT-quality critique of your classification prompt |

## Supported Models

| Model | Provider | Thinking |
|---|---|---|
| Gemini 2.0 Flash | Google | ✗ |
| Gemini 2.0 Flash Lite | Google | ✗ |
| Gemini 2.5 Pro | Google | ✓ |
| Claude 3.5 Sonnet (Vertex) | Anthropic | ✗ |
| Claude 3.7 Sonnet (Vertex) | Anthropic | ✓ |
| Llama 3.1 405B (Vertex) | Meta | ✗ |
| Llama 3.3 70B (Vertex) | Meta | ✗ |

Pricing is loaded at runtime from the bundled `llm-prices` submodule.

## Quick Start

### Demo mode (no GCP required)

```bash
cd llm-classification-app
uv venv .venv && source .venv/bin/activate
uv pip install -e .
shiny run src/llm_classifier/app.py --reload
```

Open http://localhost:8000. The app runs with mock responses by default (`DEMO_MODE=true`).

### With real Vertex AI

```bash
export GCP_PROJECT=my-project-id
export GCP_LOCATION=us-central1
export DEMO_MODE=false
gcloud auth application-default login
shiny run src/llm_classifier/app.py
```

## Prompt Template Format

Use `{column_name}` to reference CSV columns and `{label_options}` to insert the category list:

```
Classify the customer review into the best category.

Review: {review_text}
Product: {product_name}

{label_options}

Respond with only the category name.
```

## Configuration

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `GCP_PROJECT` | — | GCP project ID |
| `GCP_LOCATION` | `us-central1` | Vertex AI region |
| `GCS_BUCKET` | — | GCS bucket for batch output |
| `BQ_DATASET` | — | BigQuery dataset for Claude batch |
| `DEMO_MODE` | `true` | Use mock responses |
| `FUZZY_THRESHOLD` | `70` | Label matching threshold (0–100) |
| `BATCH_JOBS_FILE` | `batch_jobs.json` | Batch job persistence file |

## Architecture

```
src/llm_classifier/
├── app.py            – Shiny UI + server
├── models.py         – Model registry + pricing
├── prompt_builder.py – Prompt template engine
├── classification.py – Fuzzy label matching + row classification
├── vertex_client.py  – Gemini / Claude / Llama API calls
├── batch_manager.py  – Persistent batch job tracking
├── arena.py          – Multi-model comparison + judge
└── config.py         – Environment-based configuration
```

### Thinking Levels

| Level | Token Budget |
|---|---|
| 0 (off) | — |
| 1 (low) | 1,024 |
| 2 (medium) | 8,192 |
| 3 (high) | 32,768 |

### Fuzzy Label Matching

Model responses are matched to categories using `rapidfuzz` WRatio scorer. Matches below the threshold (default 70) are labelled `UNMATCHED`. Multi-label responses use `|` as delimiter.

## Development

```bash
uv pip install -e ".[dev]"
pytest
```

## Submodule

`llm-prices/` is a git submodule containing up-to-date model pricing data from [llm-prices](https://github.com/simonw/llm-prices) by Simon Willison.
