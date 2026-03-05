# Code Walkthrough Notes

## Goal
Create a showboat walkthrough.md that explains the `llm-classification-app` in detail, covering every backend module and the Streamlit frontend, with screenshots of the rendered walkthrough embedded via rodney.

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

## Build Process
1. `showboat init` + `showboat note` + `showboat exec bash` to build the doc
2. `grip --export` to render walkthrough.md as self-contained HTML
3. `rodney start --local` to launch headless browser
4. `rodney open file://...` to load the HTML
5. `rodney js scrollIntoView` to position each section
6. `rodney screenshot` to capture each section
7. `showboat image` to copy screenshots into the doc and embed them

## Key Insight
The clean separation of `backend/` from `app.py` means backend modules have no Streamlit imports and are fully testable without running the UI.
