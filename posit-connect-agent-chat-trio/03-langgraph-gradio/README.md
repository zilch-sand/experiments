# Experiment 03 — LangGraph Agent + Gradio

This example provides a third stack: LangGraph (agent orchestration) and Gradio (chat UI).

## Security controls shown
- Explicit tool allow-list only.
- Filesystem sandbox via `AGENT_WORKSPACE` path checks.
- Skill-like system prompt to enforce careful behavior.
- No shell execution tool exposed.

## Local setup with `uv`
```bash
uv venv
source .venv/bin/activate
uv sync
export OPENAI_API_KEY=...
export AGENT_WORKSPACE=./workspace
python app.py
```

## Deploy on Posit Connect
- Deploy as Python content with `app.py` as entry point.
- Configure env vars:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (optional)
  - `AGENT_WORKSPACE` (optional)
  - `PORT`
