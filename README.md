# Research projects carried out by AI tools

Each directory in this repo is a separate research project carried out by an LLM tool. Every single line of text and code was written by an LLM.

See [Code research projects with async coding agents like Claude Code and Codex](https://simonwillison.net/2025/Nov/6/async-code-research/) for more details on how this works.

I try to include prompts and links to transcripts in the PRs and commits that added each report.

## Adding a new research project

1. Create a new folder at the repo root with a short, descriptive name.
2. Capture your work in a `notes.md` file as you go.
3. Publish your findings in a `README.md` in that same folder.
4. Include any code you wrote or small artifacts you produced (avoid copying large external repos; include diffs instead).

The README is auto-updated with a list of projects and short summaries using `cog` and GitHub Actions.

<!--[[[cog
import os
import re
import subprocess
import pathlib
from datetime import datetime, timezone

# Model to use for generating summaries
MODEL = "github/gpt-4.1"

# Get all subdirectories with their first commit dates
research_dir = pathlib.Path.cwd()
subdirs_with_dates = []

for d in research_dir.iterdir():
    if d.is_dir() and not d.name.startswith('.'):
        # Get the date of the first commit that touched this directory
        try:
            result = subprocess.run(
                ['git', 'log', '--diff-filter=A', '--follow', '--format=%aI', '--reverse', '--', d.name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                # Parse first line (oldest commit)
                date_str = result.stdout.strip().split('\n')[0]
                commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                subdirs_with_dates.append((d.name, commit_date))
            else:
                # No git history, use directory modification time
                subdirs_with_dates.append((d.name, datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc)))
        except Exception:
            # Fallback to directory modification time
            subdirs_with_dates.append((d.name, datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc)))

# Print the heading with count
print(f"## {len(subdirs_with_dates)} research projects\n")

# Sort by date, most recent first
subdirs_with_dates.sort(key=lambda x: x[1], reverse=True)

for dirname, commit_date in subdirs_with_dates:
    folder_path = research_dir / dirname
    readme_path = folder_path / "README.md"
    summary_path = folder_path / "_summary.md"

    date_formatted = commit_date.strftime('%Y-%m-%d')

    # Get GitHub repo URL
    github_url = None
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            origin = result.stdout.strip()
            # Convert SSH URL to HTTPS URL for GitHub
            if origin.startswith('git@github.com:'):
                origin = origin.replace('git@github.com:', 'https://github.com/')
            if origin.endswith('.git'):
                origin = origin[:-4]
            github_url = f"{origin}/tree/main/{dirname}"
    except Exception:
        pass

    if github_url:
        print(f"### [{dirname}]({github_url}) ({date_formatted})\n")
    else:
        print(f"### {dirname} ({date_formatted})\n")

    # Check if summary already exists
    if summary_path.exists():
        # Use cached summary
        with open(summary_path, 'r') as f:
            description = f.read().strip()
            if description:
                print(description)
            else:
                print("*No description available.*")
    elif readme_path.exists():
        # Generate new summary using llm command
        prompt = """Summarize this research project concisely. Write just 1 paragraph (3-5 sentences) followed by an optional short bullet list if there are key findings. Vary your opening - don't start with "This report" or "This research". Include 1-2 links to key tools/projects. Be specific but brief. No emoji."""
        result = subprocess.run(
            ['llm', '-m', MODEL, '-s', prompt],
            stdin=open(readme_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            error_msg = f"LLM command failed for {dirname} with return code {result.returncode}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr}"
            raise RuntimeError(error_msg)
        if result.stdout.strip():
            description = result.stdout.strip()
            print(description)
            # Save to cache file
            with open(summary_path, 'w') as f:
                f.write(description + '\n')
        else:
            raise RuntimeError(f"LLM command returned no output for {dirname}")
    else:
        print("*No description available.*")

    print()  # Add blank line between entries

# Add AI-generated note to all project README.md files
# Note: we construct these marker strings via concatenation to avoid the HTML comment close sequence
AI_NOTE_START = "<!-- AI-GENERATED-NOTE --" + ">"
AI_NOTE_END = "<!-- /AI-GENERATED-NOTE --" + ">"
AI_NOTE_CONTENT = """> [!NOTE]
> This is an AI-generated research report. All text and code in this report was created by an LLM (Large Language Model). For more information on how these reports are created, see the [main research repository](https://github.com/simonw/research)."""

for dirname, _ in subdirs_with_dates:
    folder_path = research_dir / dirname
    readme_path = folder_path / "README.md"

    if not readme_path.exists():
        continue

    content = readme_path.read_text()

    # Check if note already exists
    if AI_NOTE_START in content:
        # Replace existing note
        pattern = re.escape(AI_NOTE_START) + r'.*?' + re.escape(AI_NOTE_END)
        new_note = f"{AI_NOTE_START}\n{AI_NOTE_CONTENT}\n{AI_NOTE_END}"
        new_content = re.sub(pattern, new_note, content, flags=re.DOTALL)
        if new_content != content:
            readme_path.write_text(new_content)
    else:
        # Add note after first heading (# ...)
        lines = content.split('\n')
        new_lines = []
        note_added = False
        for i, line in enumerate(lines):
            new_lines.append(line)
            if not note_added and line.startswith('# '):
                # Add blank line, then note, then blank line
                new_lines.append('')
                new_lines.append(AI_NOTE_START)
                new_lines.append(AI_NOTE_CONTENT)
                new_lines.append(AI_NOTE_END)
                note_added = True

        if note_added:
            readme_path.write_text('\n'.join(new_lines))

]]]-->
## 6 research projects

### [posit_connect_static_tool_test](https://github.com/zilch-sand/experiments/tree/main/posit_connect_static_tool_test) (2026-02-23)

Hosting single-file, browser-heavy HTML tools on [Posit Connect](https://posit.co/products/connect/) is practical for most local page functionality, provided the current content security policy (CSP) allows inline scripting and standard browser APIs. The main obstacles observed in this stress-test are direct external API calls—blocked by CSP `connect-src`—and generic iframe embedding, which fails due to both host and target frame restrictions. Deploying a backend proxy API (e.g., [FastAPI](https://fastapi.tiangolo.com/)), which relays external requests server-side, reliably circumvents browser-side CORS and CSP blocks, but inherits any server/network egress constraints. Overall, feature-rich single-page tools can thrive if external integration is handled via a local proxy pattern.

**Key findings:**
- Core client-side behaviors (inline JS, localStorage, file input) work reliably within page origin.
- Direct browser calls to external APIs and generic iframes are restricted by CSP and frame policies.
- Integrating a proxy API enables controlled outbound requests with centralized access control.
- Server/network egress rules can still restrict external access even when using a proxy.

### [jsonforms-pydantic-demo](https://github.com/zilch-sand/experiments/tree/main/jsonforms-pydantic-demo) (2026-02-12)

Leveraging **Rodney** for Chrome automation and **Showboat** for executable markdown documentation, this project showcases a reproducible workflow for exploring and documenting the pydantic-jsonforms-demo—a full-stack app combining FastAPI/Pydantic on the backend with React/JSONForms on the frontend. The experiment illustrates how browser automation can capture application states, while Showboat ensures demonstrations remain verifiable and up-to-date as code evolves. Key features include single-source validation (Pydantic-defined), dynamic form generation, support for complex/nested data structures, and dual client-server validation. Despite environment limitations (no Chrome for Rodney), Playwright proved to be a viable alternative for browser automation.

Key findings:
- Automated documentation with [Showboat](https://github.com/unifyai/showboat) enhances reproducibility and maintenance.
- Rodney (or alternatives like Playwright) simplifies browser interaction for demos and testing ([Rodney](https://github.com/unifyai/rodney)).
- Dynamic forms generated from Pydantic schemas facilitate robust type-safe validation across frontend and backend.
- Treating documentation as code allows continual verification that walkthroughs remain accurate.

### [wos-fast5k-playwright](https://github.com/zilch-sand/experiments/tree/main/wos-fast5k-playwright) (2026-02-10)

Automating bulk exports from Web of Science, this experiment introduces a Playwright script that segments large result sets into precise 5,000-record batches for Fast 5K downloads, automatically handling the final batch size. The workflow requires the user to log in and conduct a search manually, after which the script reads the total record count, computes exact ranges, fills the export dialog, and sequentially saves batches with customizable file naming. Selector handling is robust but adaptable, providing reliability across varying Web of Science interfaces. The tool can be accessed via the provided [GitHub repository](https://github.com/your-repo/download_wos_fast5k) for deployment, with basic setup via Node.js and Playwright.

**Key Features and Findings:**
- Ensures accurate export batches, preventing over/under-collection in the final batch.
- Supports sequential file naming and customizable batch size.
- Efficient for exporting thousands of records from Web of Science without manual range entry.
- Selector tweaks may be required based on platform UI differences.

For more details on Playwright automation, see [Playwright documentation](https://playwright.dev/).

### [pydantic-jsonforms-demo](https://github.com/zilch-sand/experiments/tree/main/pydantic-jsonforms-demo) (2026-02-09)

Demonstrating an integrated approach, this project uses Pydantic models as the central source for data validation, automatically generating a JSON Schema to power dynamic forms via [JSONForms](https://jsonforms.io/). A FastAPI backend validates submitted form data using the same models, ensuring consistent rules for fields such as email, URLs, dates, and array lengths. While Pydantic handles all structural validation and most constraints, UI layout and complex interactions (such as grouping or custom display logic) are managed separately using the JSONForms UI schema. The demo features a browser client that fetches the schema from the API and validates user input server-side, streamlining form configuration and validation.

Key findings:
- Validation logic (types, required fields, constraints) is defined once in Pydantic, reducing duplication.
- UI schema for layout must be separately defined for JSONForms; not covered by Pydantic.
- Complex, cross-field validation (e.g., date ordering) can be expressed in Pydantic, but custom errors may need to be surfaced via the API.
- Example repo: [Pydantic](https://docs.pydantic.dev/latest/) + FastAPI + JSONForms vanilla demo.

### [cli-tools-pattern](https://github.com/zilch-sand/experiments/tree/main/cli-tools-pattern) (2026-02-09)

Demonstrating how to package multiple command-line tools in one Python package, this project leverages the `[project.scripts]` section in `pyproject.toml` to create distinct shell commands that map to individual Python functions. By installing the package into a virtual environment (via pip or [uv](https://github.com/astral-sh/uv)), users gain direct access to each tool (e.g., `hello-world`, `goodbye-world`) without needing command prefixes. Each entry point is defined as a callable in a shared module, allowing flexible organization within the package. The approach streamlines CLI tool distribution and avoids manual invocation, making integration into other projects straightforward.

**Key takeaways:**
- Use `[project.scripts]` to define multiple commands from one package.
- Installing in a virtualenv exposes tools directly on the system PATH.
- Each CLI entry point can be implemented in a single file or split across modules.  
- [uv](https://github.com/astral-sh/uv) can simplify environment setup and installation.

### [readme-summaries-setup](https://github.com/zilch-sand/experiments/tree/main/readme-summaries-setup) (2026-02-08)

Automated README summary generation is enabled in this project using a combination of GitHub Actions, the llm CLI, and the cog tool. Whenever code is pushed to the main branch, the workflow scans repository directories, reads each README, and—if a cached summary file is missing—uses the github/gpt-4.1 model (via the llm-github-models plugin) to generate concise summaries. This setup works seamlessly in CI environments with no extra API key required; locally, users must install dependencies from requirements.txt and configure llm with a GitHub token that allows access to GitHub Models. The process ensures that summaries are always current and automatically committed back to the repository. Find more details and setup instructions in the main README and recommended tools: [llm](https://github.com/llm-tools/llm), [cog](https://github.com/replicate/cog).

Key points:
- Action-based automation keeps README summaries updated on every push to main
- Uses github/gpt-4.1 model for summarization via [llm-github-models](https://github.com/llm-tools/llm-github-models)
- Local setup requires authenticated llm and dependencies from requirements.txt
- No reliance on Copilot; access is strictly tied to GitHub Models permissions

<!-- [[[end]]] -->
## 0 research projects
