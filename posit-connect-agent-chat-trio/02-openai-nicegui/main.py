import os
from pathlib import Path

from nicegui import ui
from agents import Agent, Runner, function_tool

WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", "./workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _safe_path(rel_path: str) -> Path:
    p = (WORKSPACE / rel_path).resolve()
    if WORKSPACE not in p.parents and p != WORKSPACE:
        raise ValueError("Path escapes workspace sandbox")
    return p


@function_tool
def list_files() -> str:
    """List files under the workspace sandbox."""
    return "\n".join(
        str(p.relative_to(WORKSPACE))
        for p in sorted(WORKSPACE.rglob("*"))
        if p.is_file()
    ) or "(empty workspace)"


@function_tool
def read_file(path: str) -> str:
    """Read a text file from the workspace sandbox."""
    p = _safe_path(path)
    if not p.exists():
        return f"error: not found: {path}"
    return p.read_text(encoding="utf-8")


@function_tool
def write_file(path: str, content: str) -> str:
    """Write a text file to the workspace sandbox."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"ok: wrote {path}"


AGENT = Agent(
    name="LockedDownOpenAIAgent",
    model=MODEL,
    instructions=(
        "You are a careful file assistant.\n"
        "Skills:\n"
        "1) Explain intended file changes before writing.\n"
        "2) Prefer minimal edits.\n"
        "3) Never claim to have used tools you did not use.\n"
        "4) Do not access network resources; only use provided tools."
    ),
    tools=[list_files, read_file, write_file],
)


async def ask_agent(user_text: str) -> str:
    result = await Runner.run(AGENT, user_text)
    return result.final_output


ui.label("OpenAI Agents SDK + NiceGUI")
ui.markdown(f"**Sandbox root:** `{WORKSPACE}`")
chat_log = ui.log(max_lines=500).classes("w-full h-96")

input_box = ui.textarea(label="Prompt", placeholder="Ask the agent to inspect or edit files").classes("w-full")


async def on_send() -> None:
    prompt = (input_box.value or "").strip()
    if not prompt:
        return
    chat_log.push(f"USER: {prompt}")
    reply = await ask_agent(prompt)
    chat_log.push(f"AGENT: {reply}")
    input_box.value = ""


ui.button("Send", on_click=on_send)

ui.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), title="OpenAI NiceGUI Agent")
