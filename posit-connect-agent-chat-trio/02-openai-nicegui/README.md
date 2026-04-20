# Experiment 02 — OpenAI Agents SDK + NiceGUI

This example uses the OpenAI Agents SDK with a NiceGUI chat interface.

## Security controls shown
- Strict tool allow-list (`list_files`, `read_file`, `write_file`).
- Sandboxed file access rooted in `AGENT_WORKSPACE`.
- Skill policy in agent instructions for conservative, auditable behavior.
- No shell tool and no network-capable tool exposed to the model.

## Local setup with `uv`
```bash
uv venv
source .venv/bin/activate
uv sync
export OPENAI_API_KEY=...
export AGENT_WORKSPACE=./workspace
python main.py
```

## Deploy on Posit Connect
- Publish as a Python API/app content item.
- Entry point: `main.py`.
- Environment variables:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (optional)
  - `AGENT_WORKSPACE` (optional)
  - `PORT` (Connect sets this automatically in many runtimes)
