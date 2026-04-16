# Notes: Shiny for Python Skill (best practices)

## 2026-04-16
- Task: create a high-quality Claude Skill for Shiny for Python best practices, informed by existing posit-dev/skills Shiny skills and current py-shiny docs/changelog.
- Constraints: do not vendor external repos; include only authored artifacts in this experiment folder.
- Examined `posit-dev/skills` format and Shiny category content:
  - Skills use `SKILL.md` with YAML frontmatter (`name`, `description`, optional `metadata`, `license`).
  - Existing Shiny skills are R-focused (`shiny-bslib`, `shiny-bslib-theming`) and not a direct fit for Python app architecture/reactivity workflow.
- Gathered current Shiny for Python guidance from official docs:
  - Core vs Express tradeoffs and migration path.
  - Reactive patterns (`@reactive.event`, `reactive.isolate`, `req`, `invalidate_later`, `file_reader`, `poll`).
  - Module patterns and namespacing in Core and Express.
  - Mutable-state pitfalls and copy-on-update practices.
  - Deployment options: cloud, self-hosted, and shinylive static.
- Gathered current release context:
  - Latest release: `shiny` v1.6.0.
  - Notable recent capabilities to reflect in best practices: toolbar APIs, `input_code_editor`, OpenTelemetry controls (`SHINY_OTEL_COLLECT`, `otel.suppress`, `otel.collect`).
- Installed tooling and validated practical workflow in this experiment folder:
  - Installed `uv` (v0.11.7).
  - Created local `.venv` via `uv venv`.
  - Installed `shiny` via `uv pip install shiny` (installed version: `1.6.0`).
  - Ran `shiny create --template dashboard --mode core --dir sample-dashboard-app`.
  - Initial run failed due missing template deps (`seaborn`), then succeeded after `uv pip install -r sample-dashboard-app/requirements.txt`.
  - Confirmed server startup with `uv run shiny run sample-dashboard-app/app.py`.
- Inspected testing CLI workflow:
  - `shiny add test` supports AI-generated Playwright tests with Anthropic/OpenAI providers.
- Ran requested helper-tool checks:
  - `uvx showboat --help` works.
  - `uvx rodney --help` works.
