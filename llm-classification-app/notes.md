# LLM Classification App – Implementation Notes

## Architecture Decisions

### Demo Mode
- `DEMO_MODE=true` (default) allows the app to run fully without GCP credentials.
- `vertex_client.py` returns randomised mock responses in demo mode.
- Flip to `DEMO_MODE=false` and set `GCP_PROJECT` env var to use real Vertex AI.

### Model Registry (`models.py`)
- Pricing loaded at runtime from `llm-prices/data/*.json` (submodule).
- `get_price(model_id)` returns (input, output) per-million-token rates.
- Models added: Gemini 2.0 Flash, 2.0 Flash Lite, 2.5 Pro, Claude 3.5/3.7 Sonnet (Vertex), Llama 3.1 405B / 3.3 70B (Vertex).

### Prompt Builder (`prompt_builder.py`)
- `{col_name}` placeholders replaced from CSV row dict.
- `{label_options}` is a reserved placeholder – renders formatted category list.
- Validation warns on missing columns, missing `{label_options}`, and collisions.

### Classification (`classification.py`)
- `fuzzy_match_label` uses `rapidfuzz.process.extractOne` with WRatio scorer.
- Threshold: 70 (configurable via `FUZZY_THRESHOLD` env var).
- Multi-label: splits on `|` and matches each segment independently.

### Vertex Client (`vertex_client.py`)
- Gemini: `vertexai.generative_models.GenerativeModel`
- Claude: `anthropic.AnthropicVertex`
- Llama: OpenAI-compatible endpoint on Vertex AI Model Garden
- Thinking: Gemini uses `thinking_config`, Claude uses `thinking` block.
- Token counting: Gemini native → tiktoken cl100k fallback → word estimate.

### Batch Manager (`batch_manager.py`)
- Persists to `batch_jobs.json` in CWD.
- Simple JSON file; no DB dependency.

### Arena (`arena.py`)
- Runs each contestant on the same prompt independently.
- Judge sees all responses without the category list.
- Default judge prompt is configurable in the UI.

### Shiny App (`app.py`)
- `page_navbar` with 4 tabs: Setup & Test, Batch Run, Arena, AI Feedback.
- Uses `shinyswatch.theme.flatly()` for styling.
- Reactive values: `loaded_df`, `test_results`, `arena_results`, `arena_contestants`, `feedback_text`.
- Cost estimation: first row used as sample for token count × total rows.
- AI Feedback from Tab 1 navigates to Tab 4 automatically.

## Updates (2026-03-02)

- Fixed duplicate `thinking_level` input ID between Setup & Test and Arena tabs — arena now uses `arena_thinking_level`.
- Fixed inline relative imports in `app.py` server functions (they caused runtime errors when running via `shiny run`). All vertex_client imports moved to top-level try/except block.
- Fixed demo mode returning random labels from a hardcoded list — now uses `_extract_categories_from_prompt()` to parse actual categories from the rendered prompt.
- Added `_DEMO_FEEDBACK` constant and system-prompt-based detection so AI Feedback tab returns meaningful structured feedback in demo mode instead of a random label.
- Improved `feedback_output` renderer to parse `**bold**` markers into `<strong>` HTML tags.

1. Batch jobs table does not auto-refresh (click "Refresh Status").
2. Dynamic remove-contestant buttons rely on `getattr(input, btn_id)` which may not
   trigger properly with current Shiny for Python reactive model – may need workaround.
3. GCS/BQ cleanup (`cleanup_completed_job`) is a stub.
4. Llama batch jobs not yet implemented (raises `NotImplementedError`).
5. Prompt caching: Gemini natively caches system prompts for large contexts –
   enable via `cached_content` parameter on `GenerativeModel` when needed.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GCP_PROJECT` | `""` | GCP project ID |
| `GCP_LOCATION` | `us-central1` | Vertex AI region |
| `GCS_BUCKET` | `""` | Default GCS bucket for batch output |
| `BQ_DATASET` | `""` | Default BigQuery dataset |
| `DEMO_MODE` | `true` | Run with mock responses |
| `FUZZY_THRESHOLD` | `70` | Minimum fuzzy match score (0-100) |
| `BATCH_JOBS_FILE` | `batch_jobs.json` | Path to persistent batch jobs file |

## Running Locally

```bash
cd llm-classification-app
uv venv .venv && source .venv/bin/activate
uv pip install -e .
shiny run src/llm_classifier/app.py --reload
```
