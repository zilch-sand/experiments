# Code Walkthrough Notes

## Goal
Create a showboat walkthrough.md that explains the `llm-classification-app` in detail, covering every backend module and the Streamlit frontend.

## App Architecture
- `app.py` — Streamlit frontend, 3 tabs
- `backend/prompt.py` — PromptTemplate dataclass
- `backend/models.py` — ModelConfig + thinking-level handling
- `backend/pricing.py` — ModelPrice, llm-prices submodule loader, Vertex AI model list
- `backend/classifier.py` — classify_single_row, classify_rows, token estimation
- `backend/fuzzy_match.py` — rapidfuzz-based label normalisation
- `backend/arena.py` — multi-model comparison + judge
- `backend/batch.py` — Vertex AI async batch jobs with file-based state
- `backend/feedback.py` — AI critique of prompt + categories

## Showboat Plan
- Use `showboat note` for explanations of each module
- Use `showboat exec bash` with sed/grep/cat to embed real code snippets

## Key Insight
The clean separation of `backend/` from `app.py` means backend modules have no Streamlit imports and are fully testable without running the UI.
