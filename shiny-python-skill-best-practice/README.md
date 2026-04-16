# Shiny for Python Skill: Best Practices

<!-- AI-GENERATED-NOTE -->
> [!NOTE]
> This is an AI-generated research report. All text and code in this report was created by an LLM (Large Language Model). For more information on how these reports are created, see the [main research repository](https://github.com/simonw/research).
<!-- /AI-GENERATED-NOTE -->

## Goal

Create a production-ready Claude Skill focused on **Shiny for Python best practices**, informed by:

1. Existing Shiny skills in `posit-dev/skills`
2. Hands-on verification with installed `shiny`
3. Current official docs and latest release/changelog context

## What I produced

A reusable skill package at:

- `shiny/shiny-python-best-practices/SKILL.md`
- `shiny/shiny-python-best-practices/references/core-vs-express.md`
- `shiny/shiny-python-best-practices/references/reactivity-and-state.md`
- `shiny/shiny-python-best-practices/references/testing-and-release-awareness.md`

This skill is written for Claude/agent execution style and emphasizes:

- Core vs Express decision-making
- Reactive correctness and state-safety (mutable object pitfalls)
- Module-first scaling patterns
- Testing and deployment readiness
- Version-aware recommendations (including Shiny 1.6-era features)

## Validation performed

- Installed `uv` and created local environment in this folder.
- Installed `shiny` (`1.6.0`).
- Scaffolded an app via:
  - `shiny create --template dashboard --mode core --dir sample-dashboard-app`
- Resolved template dependency gap by installing generated requirements.
- Verified app startup with `shiny run sample-dashboard-app/app.py`.
- Checked CLI docs for `shiny add test`.
- Ran `uvx showboat --help` and `uvx rodney --help` as requested by repo instructions.

## Key findings used in the skill

- Existing `posit-dev/skills` Shiny skills are primarily R/bslib-focused; Python needs dedicated guidance.
- Python Shiny best practice requires explicit handling of mutable-state hazards in reactivity.
- Core and Express are both valid; architecture guidance should be context-driven, not dogmatic.
- Current release awareness matters (e.g., AI test generation, toolbar APIs, code editor input, OpenTelemetry controls).

## External references

- `posit-dev/skills` Shiny category and contribution format
- Shiny for Python docs: overview, R-vs-Python differences, Express-vs-Core, modules, reactive patterns, reactive mutability, deployment
- `posit-dev/py-shiny` latest release + `CHANGELOG.md`

## Notes

Detailed step-by-step investigation notes are in `notes.md`.
