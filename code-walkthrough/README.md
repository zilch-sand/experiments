# Code Walkthrough — LLM Classification App

A linear, code-inclusive walkthrough of the `llm-classification-app` experiment, built with [showboat](https://github.com/simonw/showboat).

## What's here

- **[walkthrough.md](walkthrough.md)** — the main document: commentary + real code excerpts walking through every layer of the app
- **[notes.md](notes.md)** — working notes from building the walkthrough

## How it was built

The walkthrough was built entirely using `showboat`:

- `showboat init` — created the document with a title and timestamp
- `showboat note` — added commentary sections explaining each module
- `showboat exec bash` — ran `cat`, `sed`, `grep`, and `head` commands to pull real code snippets from the source files directly into the document

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
