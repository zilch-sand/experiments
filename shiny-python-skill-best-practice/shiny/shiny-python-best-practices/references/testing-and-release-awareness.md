# Testing and release-awareness notes

## Testing workflow

- Smoke test first: app starts, key page loads, critical inputs update outputs.
- Use `shiny add test` for initial Playwright test generation when useful.
- Review generated tests for selector robustness and deterministic assertions.
- Add targeted tests around business-critical reactive logic and module contracts.

## Practical command sequence

1. `shiny run app.py --reload`
2. `shiny add test --app app.py --provider ...`
3. `pytest <generated_test_file>`

## Keep guidance version-aware

Recent notable updates in modern Shiny releases include:

- AI-assisted test generation (`shiny add test`)
- Toolbar components (`ui.toolbar*`)
- `ui.input_code_editor()`
- OpenTelemetry controls (`SHINY_OTEL_COLLECT`, `otel.suppress`, `otel.collect`)

If code examples from older blogs conflict with current docs/changelog, prefer current official docs and release notes.
