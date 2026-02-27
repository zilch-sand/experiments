#!/usr/bin/env python3
"""
gather_links.py – extract metadata from all root-level .html files and write tools.json.

Adapted from https://github.com/simonw/tools/blob/main/gather_links.py
"""
import json
import html as html_module
import re
import subprocess
from pathlib import Path


def get_file_commit_dates(file_path: Path):
    """Return (created_iso, updated_iso) for a file from git history."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%aI", "--", str(file_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        dates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not dates:
            return None, None
        return dates[-1], dates[0]   # oldest = created, newest = updated
    except subprocess.CalledProcessError:
        return None, None


def extract_title(html_path: Path) -> str:
    """Return the text inside <title>…</title>, or the stem as fallback."""
    try:
        content = html_path.read_text("utf-8", errors="ignore")
    except OSError:
        return html_path.stem
    match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if match:
        return html_module.unescape(match.group(1).strip())
    return html_path.stem


def extract_description(docs_path: Path) -> str:
    """Return the first paragraph from a .docs.md file, if it exists."""
    if not docs_path.exists():
        return ""
    try:
        content = docs_path.read_text("utf-8").strip()
    except OSError:
        return ""
    # Strip HTML comments
    if "<!--" in content:
        content = content.split("<!--", 1)[0]
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        lines.append(stripped)
    return " ".join(lines)


def main():
    current_dir = Path.cwd()
    html_files = sorted(current_dir.glob("*.html"))

    tools = []
    for html_file in html_files:
        if html_file.name == "index.html":
            continue   # index is generated, not a tool

        created, updated = get_file_commit_dates(html_file)
        if not created and not updated:
            # Not tracked by git yet – use None dates but still include the file
            pass

        docs_path = html_file.with_suffix(".docs.md")
        description = extract_description(docs_path)
        slug = html_file.stem

        tools.append({
            "filename": html_file.name,
            "slug": slug,
            "title": extract_title(html_file),
            "description": description,
            "created": created,
            "updated": updated,
            "url": f"/{slug}",
        })

    # Stable alphabetical order by title
    tools.sort(key=lambda t: t["title"].lower())

    with open("tools.json", "w", encoding="utf-8") as f:
        json.dump(tools, f, indent=2)

    print(f"Wrote tools.json with {len(tools)} tool(s).")


if __name__ == "__main__":
    main()
