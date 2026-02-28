# Experiment 01 — Claude-style agent loop + R Shiny

This example demonstrates a chat UI in **R Shiny** with a Claude-compatible tool loop.

## Why this pattern
- Keeps UI in native R for Posit Connect.
- Uses explicit tool declarations (`list_files`, `read_file`, `write_file`).
- Implements sandboxed file operations rooted at `AGENT_WORKSPACE`.

## Security controls shown
- **Tool allow-list only**: the model can only call 3 local file tools.
- **Path sandboxing**: rejects any path escaping `AGENT_WORKSPACE`.
- **No generic shell/network tool**: model cannot run arbitrary commands.
- **Instructional skill policy** in `SKILLS_PROMPT` to reinforce safe behavior.

## Run locally
```bash
export ANTHROPIC_API_KEY=...
export AGENT_WORKSPACE=./workspace
R -e "shiny::runApp('app.R', host='0.0.0.0', port=8001)"
```

## Deploy on Posit Connect
- Deploy as an R Shiny content item.
- Set environment variables:
  - `ANTHROPIC_API_KEY`
  - `CLAUDE_MODEL` (optional)
  - `AGENT_WORKSPACE` (optional)

