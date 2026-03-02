# Code Walkthrough

A linear, code-inclusive tour of every experiment in this repository, built with [showboat](https://github.com/simonw/showboat).

## What's here

- **[walkthrough.md](walkthrough.md)** — the main document: commentary + real code excerpts for all 8 experiments
- **[notes.md](notes.md)** — working notes from building the walkthrough

## How it was built

The walkthrough was built entirely using `showboat`:

- `showboat init` — created the document with a title and timestamp
- `showboat note` — added commentary sections explaining each experiment
- `showboat exec bash` — ran `cat`, `grep`, `sed`, and `head` commands to pull real code snippets from the source files directly into the document

This means the walkthrough is *verifiable*: run `uvx showboat verify walkthrough.md` to re-execute every code block and confirm the outputs still match.

## Experiments covered

| # | Experiment | Key pattern |
|---|-----------|-------------|
| 1 | cli-tools-pattern | `[project.scripts]` entry points in pyproject.toml |
| 2 | pydantic-jsonforms-demo | Pydantic → JSON Schema → React forms |
| 3 | llm-classification-app | Streamlit + FastAPI + LLM classification |
| 4 | posit_connect_static_tool_test | Static HTML + server-side proxy |
| 5 | readme-summaries-setup | cog + GitHub Actions auto-generated README |
| 6 | simonw-tools-exploration | Flat HTML files + Python build chain |
| 7 | wos-fast5k-playwright | Playwright bulk export automation |
| 8 | jsonforms-pydantic-demo | Showboat executable documentation |
