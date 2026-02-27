#!/usr/bin/env python3
"""
build_index.py – convert README.md to index.html, injecting recently-added/updated sections.

Adapted from https://github.com/simonw/tools/blob/main/build_index.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

try:
    import markdown
except ModuleNotFoundError as exc:
    raise SystemExit(
        "The 'markdown' package is required.  Install it with: pip install markdown"
    ) from exc

README_PATH = Path("README.md")
TOOLS_JSON_PATH = Path("tools.json")
OUTPUT_PATH = Path("index.html")

START_MARKER = "<!-- recently starts -->"
END_MARKER = "<!-- recently stops -->"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _fmt_date(dt: datetime) -> str:
    return f"{_ordinal(dt.day)} {dt.strftime('%B %Y')}"


def _select_recent(tools: list[dict], key: str, limit: int, exclude: set[str] | None = None) -> list[dict]:
    exclude = exclude or set()
    dated = [(t, _parse_date(t.get(key))) for t in tools if t.get(key)]
    dated = [(t, d) for t, d in dated if d is not None and t.get("slug") not in exclude]
    dated.sort(key=lambda x: x[1], reverse=True)
    result = []
    for tool, dt in dated[:limit]:
        entry = dict(tool)
        entry["_parsed_date"] = dt
        result.append(entry)
    return result


def _render_list(tools: list[dict]) -> str:
    if not tools:
        return "<li>No entries yet.</li>"
    items = []
    for t in tools:
        url = t.get("url", "#")
        slug = t.get("slug", "")
        dt: datetime | None = t.get("_parsed_date")
        date_html = f' <span style="color:#666;font-size:0.85em">— {_fmt_date(dt)}</span>' if dt else ""
        items.append(f'<li><a href="{url}">{slug}</a>{date_html}</li>')
    return "\n".join(items)


def _build_recent_section(tools: list[dict]) -> str:
    recently_added = _select_recent(tools, key="created", limit=5)
    added_slugs = {t.get("slug") for t in recently_added}
    # Only show updates that differ from creation date
    updatable = [t for t in tools if _parse_date(t.get("updated")) != _parse_date(t.get("created"))]
    recently_updated = _select_recent(updatable, key="updated", limit=5, exclude=added_slugs)

    return f"""
<div style="display:flex;gap:2rem;flex-wrap:wrap;margin:1rem 0 1.5rem">
  <div>
    <h2>Recently added</h2>
    <ul>{_render_list(recently_added)}</ul>
  </div>
  <div>
    <h2>Recently updated</h2>
    <ul>{_render_list(recently_updated)}</ul>
  </div>
</div>
"""


def build_index() -> None:
    if not README_PATH.exists():
        raise FileNotFoundError("README.md not found")

    md_text = README_PATH.read_text("utf-8")
    md = markdown.Markdown(extensions=["extra"])
    body_html = md.convert(md_text)

    tools: list[dict] = []
    if TOOLS_JSON_PATH.exists():
        tools = json.loads(TOOLS_JSON_PATH.read_text("utf-8"))

    recent_html = _build_recent_section(tools)

    # Inject between marker comments
    if START_MARKER in body_html and END_MARKER in body_html:
        before, rest = body_html.split(START_MARKER, 1)
        _, after = rest.split(END_MARKER, 1)
        body_html = before + START_MARKER + recent_html + END_MARKER + after

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Tools</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      max-width: 850px;
      margin: 2rem auto;
      padding: 0 1rem;
      line-height: 1.6;
    }}
    a {{ color: #0969da; }}
    h1 {{ border-bottom: 1px solid #eee; padding-bottom: 0.4rem; }}
    h2 {{ margin-top: 1.5rem; }}
    ul {{ padding-left: 1.4rem; }}
  </style>
</head>
<body>
{body_html}
</body>
</html>
"""
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    build_index()
