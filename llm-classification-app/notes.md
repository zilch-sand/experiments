# LLM Classification App - Development Notes

## Architecture Decisions

### Tech Stack
- **Frontend**: Streamlit - chosen for rapid data app development with built-in CSV upload, tables, progress bars
- **Backend**: Separate Python package for future front/back-end split
- **LLM Integration**: litellm - unified interface for multiple model providers on Vertex AI
- **Fuzzy Matching**: rapidfuzz - fast fuzzy string matching for classification labels
- **Pricing**: llm-prices submodule by simonw - maintained pricing data for LLM models

### Separation of Concerns
Backend is fully independent of Streamlit. All business logic lives in `backend/`:
- `pricing.py` - pricing data loading and cost estimation
- `prompt.py` - prompt template handling with {col} placeholders
- `fuzzy_match.py` - fuzzy matching of model outputs to categories
- `models.py` - model configuration, Vertex AI integration via litellm
- `classifier.py` - single/multi-label classification, token counting
- `batch.py` - Vertex AI batch endpoints, batch ID persistence
- `arena.py` - model comparison arena with judge
- `feedback.py` - AI feedback on prompt quality

### Key Design Choices
1. **Prompt caching**: SHA256 hash of prompt+categories used as cache key in session state
2. **Fuzzy matching**: Uses rapidfuzz with configurable threshold (default 60) to handle imperfect model outputs
3. **Safe delimiters**: Auto-detects safe delimiter for multi-label that doesn't appear in category names
4. **Batch recovery**: Batch IDs written to `batch_state/` directory as JSON files for recovery if app restarts
5. **Max tokens**: Set to 4096 by default to avoid cut-off responses from thinking models
6. **litellm**: Provides unified interface across Gemini, Claude (via Vertex), and Llama (via Vertex Model Garden)

### Vertex AI Model Support
- **Google**: Gemini models (direct Vertex AI)
- **Anthropic**: Claude models (via Vertex AI Model Garden)
- **Meta**: Llama models (via Vertex AI Model Garden)

### Prompt Caching on Vertex AI
- Gemini models support context caching via `input_cached` pricing
- Claude on Vertex supports prompt caching for repeated system prompts
- litellm handles caching configuration transparently

## Development Log
- Created project structure with uv
- Added llm-prices as git submodule
- Implemented all backend modules
- Created Streamlit app with 3 tabs: Classify, Arena, Batch Jobs
- Added tests for prompt, fuzzy_match, pricing, and batch modules
- Created walkthrough.md using showboat with full linear code walkthrough, live code demos, and screenshots captured with rodney
