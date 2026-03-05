# Code Walkthrough — LLM Classification App

A linear, code-inclusive walkthrough of the `llm-classification-app` experiment, built with [showboat](https://github.com/simonw/showboat). Screenshots of the rendered document (taken with [rodney](https://github.com/nicholasgriffen/rodney)) are embedded throughout to show the walkthrough in action.

## What's here

- **[walkthrough.md](walkthrough.md)** — the main document: commentary + real code excerpts + embedded screenshots at each major section
- **[notes.md](notes.md)** — working notes from building the walkthrough
- **`*.png`** — screenshots taken with rodney and embedded via `showboat image`

## How it was built

The walkthrough was built using `showboat` and `rodney`:

1. `showboat init` — created the document with a title and timestamp
2. `showboat note` — added commentary sections explaining each module
3. `showboat exec bash` — ran `cat`, `sed`, `grep`, and `head` commands to pull real code snippets from the source files directly into the document
4. `grip --export` — rendered the walkthrough as HTML
5. `rodney start` / `rodney open` — opened the rendered HTML in a headless browser
6. `rodney screenshot` — captured key sections of the rendered walkthrough
7. `showboat image` — copied each screenshot into the document directory and embedded it

This means the walkthrough is *verifiable*: run `uvx showboat verify walkthrough.md` to re-execute every code block and confirm the outputs still match.

## Modules covered

| Module | What's highlighted |
|---|---|
| `backend/prompt.py` | PromptTemplate: placeholder extraction, validation, render |
| `backend/models.py` | ModelConfig dataclass, thinking-level budget mapping per vendor |
| `backend/pricing.py` | ModelPrice, llm-prices submodule loading, Vertex AI model discovery |
| `backend/classifier.py` | classify_single_row, classify_rows, token estimation with fallback |
| `backend/fuzzy_match.py` | Two-stage matching: exact → rapidfuzz; safe delimiter selection |
| `backend/arena.py` | Multi-model comparison loop, scaled progress, judge evaluation |
| `backend/batch.py` | JSONL request prep, file-based state persistence, Vertex AI batch API |
| `backend/feedback.py` | AI prompt critique via FEEDBACK_PROMPT |
| `app.py` | Session state, 3-tab Streamlit UI, cost estimation, CSV download |
