# LLM Classification App

An LLM-based text classification application using Vertex AI, supporting multiple model providers (Google Gemini, Anthropic Claude, Meta Llama).

## Features

### 🏷️ Classification
- **CSV Upload**: Load a CSV file and classify text using LLM models
- **Prompt Builder**: Create prompts with `{column_name}` placeholders and `{label_options}` for categories
- **Single & Multi-Label**: Support for both single-label and multi-label classification with safe delimiters
- **Fuzzy Matching**: Automatically matches model outputs to categories using fuzzy string matching
- **Token Counting**: Estimates tokens and costs based on sample data
- **Progress Tracking**: Real-time progress bars during classification
- **Test Runs**: Test on first N rows before committing to full dataset
- **Auto-Save**: Download classified CSV with results

### 🏟️ Arena Mode
- **Model Comparison**: Compare multiple models (or same model with different parameters) side by side
- **Thinking Levels**: Configure thinking level/effort for models that support it
- **Judge Evaluation**: Use a judge model to evaluate classification quality (categories excluded from judge prompt)
- **Cost Estimates**: Per-model price estimates for the full dataset
- **Export**: Download arena comparison data as CSV

### 📦 Batch Processing
- **Vertex AI Batches**: Submit large datasets as batch jobs via Vertex AI
- **Batch Recovery**: Batch IDs persisted to `batch_state/` directory for recovery if app restarts
- **Multiple Batches**: Submit multiple batches before waiting for results
- **Auto-Cleanup**: Batch tracking files cleaned up after retrieval

### 🤖 AI Feedback
- **Prompt Review**: Get AI feedback on prompt clarity, category overlap, and completeness
- **RAG Recommendation**: Suggests RAG-based classification when prompts are too long

## Architecture

```
llm-classification-app/
├── app.py                   # Streamlit frontend
├── backend/                 # Separated backend for future API deployment
│   ├── arena.py             # Arena comparison + judge logic
│   ├── batch.py             # Batch processing + state persistence
│   ├── classifier.py        # Classification engine + token counting
│   ├── feedback.py          # AI prompt feedback
│   ├── fuzzy_match.py       # Fuzzy matching of model outputs
│   ├── models.py            # Model config + Vertex AI integration
│   ├── pricing.py           # Pricing data from llm-prices submodule
│   └── prompt.py            # Prompt template handling
├── batch_state/             # Persistent batch ID tracking
├── llm-prices/              # Git submodule: simonw/llm-prices
├── tests/                   # Unit tests
│   ├── test_batch.py
│   ├── test_fuzzy_match.py
│   ├── test_pricing.py
│   └── test_prompt.py
├── pyproject.toml
└── notes.md
```

### Separation of Concerns

The backend is completely independent of Streamlit. All business logic lives in the `backend/` package, making it straightforward to:
- Deploy the backend as a FastAPI service on Kubernetes
- Build a separate frontend that triggers workflows from Posit Connect
- Test backend logic without UI dependencies

## Setup

```bash
# Install dependencies
cd llm-classification-app
uv sync

# Run the app
uv run streamlit run app.py

# Run tests
uv run pytest tests/ -v
```

### Environment Variables

Set up Vertex AI authentication:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
export VERTEX_PROJECT=your-gcp-project
export VERTEX_LOCATION=us-central1
```

## Model Support

| Provider  | Models                          | Thinking Levels | Batch Support |
|-----------|--------------------------------|-----------------|---------------|
| Google    | Gemini 2.5 Pro/Flash, 2.0, 1.5 | ✅ low/med/high | ✅            |
| Anthropic | Claude 3.5/3.7 Sonnet, Haiku   | ✅ low/med/high | ✅            |
| Meta      | Llama 3.1 405B/70B/8B          | ❌              | ✅            |

## Pricing

Pricing data is sourced from [simonw/llm-prices](https://github.com/simonw/llm-prices) included as a git submodule. Update pricing data:

```bash
cd llm-prices && git pull origin main
```

## Key Design Decisions

1. **litellm**: Provides a unified interface across all model providers on Vertex AI
2. **Fuzzy matching** (rapidfuzz): Handles imperfect model outputs with configurable threshold
3. **Safe delimiters**: Auto-detects a delimiter for multi-label output that doesn't conflict with category names
4. **Max tokens = 4096**: Set high to avoid cut-off responses from thinking models
5. **Prompt caching**: SHA256 hash of prompt+categories for session-level caching
6. **Batch state persistence**: JSON files in `batch_state/` survive app restarts
