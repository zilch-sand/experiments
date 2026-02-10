import os
from pathlib import Path

import gradio as gr
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", "./workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def safe_path(rel_path: str) -> Path:
    p = (WORKSPACE / rel_path).resolve()
    if WORKSPACE not in p.parents and p != WORKSPACE:
        raise ValueError("Path escapes workspace sandbox")
    return p


@tool
def list_files() -> str:
    """List all files under workspace."""
    return "\n".join(str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()) or "(empty workspace)"


@tool
def read_file(path: str) -> str:
    """Read UTF-8 text from workspace file."""
    p = safe_path(path)
    if not p.exists():
        return f"error: not found {path}"
    return p.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Write UTF-8 text into workspace file."""
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"ok: wrote {path}"


SYSTEM_SKILLS = """You are a constrained engineering assistant.
Skills:
- summarize intent before file edits
- keep changes minimal and reversible
- use only provided tools
- do not browse external sites or call network resources
"""

agent = create_react_agent(
    model=ChatOpenAI(model=MODEL, temperature=0),
    tools=[list_files, read_file, write_file],
    prompt=SYSTEM_SKILLS,
)


def chat(user_message: str, history):
    _ = history
    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
    return result["messages"][-1].content


demo = gr.ChatInterface(
    fn=chat,
    title="LangGraph + Gradio Locked-Down Agent",
    description=f"Sandbox root: {WORKSPACE}",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
