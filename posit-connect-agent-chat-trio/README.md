# Posit Connect Agent Chat Experiments (3 patterns)

This report contains **three new experiments**, each showing a different agent + UI combination suitable for Posit Connect deployment.

## 1) Claude-style agent SDK pattern + R Shiny
**Folder:** `01-claude-r-shiny/`

- R Shiny chat UI.
- Claude-compatible tool loop over Anthropic Messages API.
- Skills policy prompt and strict local file tools.
- Path-safe sandbox rooted in `AGENT_WORKSPACE`.

## 2) OpenAI Agents SDK + NiceGUI
**Folder:** `02-openai-nicegui/`

- NiceGUI web chat interface.
- OpenAI Agents SDK `Agent` + `Runner` flow.
- Skill instructions embedded in the agent policy.
- File list/read/write tools with sandbox enforcement.

## 3) LangGraph + Gradio (something else)
**Folder:** `03-langgraph-gradio/`

- Gradio `ChatInterface` UI.
- LangGraph `create_react_agent` orchestration.
- Skill-style system prompt and constrained tools.
- File sandbox and no arbitrary shell/network tooling.

---

## Common lock-down pattern used across all three

1. **Tool allow-list only**: no generic shell execution.
2. **Path sanitization**: block `..`/escape patterns by checking resolved paths remain under `AGENT_WORKSPACE`.
3. **Network minimization**: only model API traffic from app runtime; do not provide web-fetch tools to model.
4. **Skill constraints**: explicit behavior rules (minimal edits, explain before write, truthful tool reporting).

## Posit Connect notes

- Each experiment is independently deployable.
- Use environment variables for API keys and model names.
- Point writable storage to a controlled path via `AGENT_WORKSPACE`.
- Prefer service-level egress controls in Connect/Kubernetes/network policy to enforce outbound restrictions globally.

## Included artifacts
- `notes.md`: work log and findings.
- Per-experiment source code and setup instructions.
- No vendored external repositories.
