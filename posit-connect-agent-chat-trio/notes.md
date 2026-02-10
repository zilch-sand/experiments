# Notes

## 2026-02-10
- Started a new experiment folder: `posit-connect-agent-chat-trio`.
- Planned three deployable patterns for Posit Connect:
  1. Claude-style agent loop with an **R Shiny** chat UI.
  2. OpenAI Agents SDK with **NiceGUI**.
  3. LangGraph-based agent with **Gradio** as the third UI.
- Common requirements to include in each pattern:
  - Skill-style instructions (role/task constraints).
  - File tools (list/read/write in a sandbox directory).
  - Sensible lock-down controls (restricted toolset + network policy notes).
- Implemented `01-claude-r-shiny/app.R` with a direct Anthropic tool loop and max 5 tool iterations per turn.
- Implemented `02-openai-nicegui/main.py` using OpenAI Agents SDK function tools and NiceGUI chat logging.
- Implemented `03-langgraph-gradio/app.py` using LangGraph prebuilt ReAct agent with constrained tools.
- Added per-experiment READMEs with local `uv` instructions for Python apps and Connect deployment notes.
- Added a top-level README report summarizing all three patterns and shared lock-down guidance.
- Ran `uv lock` for both Python experiments to capture reproducible dependency graphs.
- Ran Python syntax checks with `python -m py_compile` on both Python apps.
- Attempted R parse validation, but R is not installed in the environment.
- Captured a screenshot of the NiceGUI app using Playwright.
