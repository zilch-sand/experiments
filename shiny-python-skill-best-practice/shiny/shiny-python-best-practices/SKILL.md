---
name: shiny-python-best-practices
description: Build and refactor Shiny for Python apps using current best practices for Core/Express architecture, reactivity, state safety, modularization, testing, and deployment. Use when designing new apps, migrating patterns from R Shiny, debugging reactive behavior, or preparing production-ready Python Shiny code.
metadata:
  author: experiments (derived from posit-dev/skills style + py-shiny docs)
  version: "1.0"
license: MIT
---

# Shiny for Python Best Practices

Use this skill to produce robust, maintainable Shiny for Python apps. Prioritize Python-native Shiny patterns, not one-to-one R Shiny translation.

## When to use this skill

- Creating a new Shiny for Python app (Core or Express)
- Migrating from R Shiny concepts to Python Shiny idioms
- Refactoring large apps for maintainability
- Debugging reactive invalidation, stale state, or performance issues
- Adding test coverage and deployment readiness

## Operating rules

1. Prefer official Shiny for Python docs and current release notes when guidance conflicts with older examples.
2. Treat R-to-Python mapping as conceptual only; implement with Python-native APIs (`@render.*`, `@reactive.*`, module decorators, `input.x()`).
3. Verify assumptions against app mode (Core vs Express), package version, and deployment target.
4. Keep advice actionable: architecture decisions first, code shape second, implementation details last.

## Required workflow

### 1) Discover context first

Before proposing changes, establish:

- App syntax mode: Core, Express, or mixed
- Shiny version and key dependencies
- Deployment target (cloud/on-prem/shinylive)
- Testing posture (none/manual/automated)
- App scale: single-file prototype vs module-based product app

If these are missing, ask concise clarifying questions.

### 2) Choose Core vs Express deliberately

Use `references/core-vs-express.md`.

- Prefer **Express** for rapid prototypes and simple apps.
- Prefer **Core** for explicit UI/server separation, large codebases, and easier structural refactoring.
- For larger systems, bias toward Core-style modular architecture even if starting in Express.

### 3) Enforce reactive correctness

Use `references/reactivity-and-state.md`.

- Use decorators correctly:
  - outputs: `@render.*`
  - computed values: `@reactive.calc`
  - side effects: `@reactive.effect`
- Trigger expensive work with `@reactive.event(...)`.
- Gate incomplete state with `req(...)`.
- Use `reactive.invalidate_later()` only for intentional polling/clock behavior.

### 4) Prevent mutable-state bugs

Use copy-safe updates for lists/dicts in `reactive.value` and results from `reactive.calc`.

- Avoid in-place mutation (`append`, item assignment, dict mutation) on shared reactive objects.
- Prefer copy-on-update patterns (`x + [item]`, comprehensions, `{**d, k: v}`, `.copy()` when needed).
- If practical, use immutable structures for shared reactive state.

### 5) Structure for growth with modules

- Introduce modules as soon as repeated UI/server patterns appear.
- Keep module boundaries domain-focused (filters, charts, tables, auth area, etc.).
- Ensure module IDs are unique and consistently paired between UI and server.
- Prefer composing many small modules over one large “god module”.

### 6) UI/layout and UX guidance

- Use modern layout primitives and clear hierarchy (sidebar + cards/nav patterns as appropriate).
- Keep input groups cohesive and visible near their affected outputs.
- Use progressive disclosure for advanced controls.
- Ensure accessible labels, meaningful text, and keyboard-friendly interactions.

### 7) Testing strategy

Use `references/testing-and-release-awareness.md`.

- Start with smoke tests for app startup and critical user flows.
- Use `shiny add test` to generate Playwright-based tests when helpful, then review/edit generated assertions.
- Add deterministic tests around core reactive logic and module behavior.
- Keep tests stable: avoid brittle selector coupling and timing assumptions.

### 8) Deployment readiness

- Confirm dependency isolation (virtual environment + pinned requirements where needed).
- Validate startup command and required environment variables.
- Match deployment model to constraints:
  - cloud hosting,
  - self-hosted (Shiny Server / Posit Connect),
  - shinylive static where compatible.
- Run a final checklist: local startup, critical flow test, error handling, and observability/logging readiness.

## Recent-version awareness

When relevant, account for modern capabilities in Shiny >= 1.5/1.6:

- `shiny add test` AI-assisted test scaffolding
- `ui.toolbar*` components
- `ui.input_code_editor()`
- OpenTelemetry controls (`SHINY_OTEL_COLLECT`, `otel.suppress`, `otel.collect`)

Do not force these features; recommend them only when they fit user goals.

## Common failure modes to catch

- Treating Python input values like attributes instead of callables (`input.x` vs `input.x()`).
- Using side effects inside `@reactive.calc`.
- In-place mutation of mutable reactive objects causing stale or leaky state.
- Overusing global variables instead of session-safe reactive state.
- Deferring module adoption until the app is already hard to refactor.

## Response style when this skill is active

1. Briefly summarize current architecture and risks.
2. Provide a prioritized plan (high impact first).
3. Give concrete, mode-appropriate implementation guidance.
4. Include verification steps (run/test/deploy checks).
5. Call out migration caveats from R Shiny when applicable.

## References

- `references/core-vs-express.md`
- `references/reactivity-and-state.md`
- `references/testing-and-release-awareness.md`
- https://shiny.posit.co/py/docs/express-vs-core.html
- https://shiny.posit.co/py/docs/reactive-patterns.html
- https://shiny.posit.co/py/docs/reactive-mutable.html
- https://shiny.posit.co/py/docs/modules.html
- https://shiny.posit.co/py/get-started/deploy.html
- https://github.com/posit-dev/py-shiny/blob/main/CHANGELOG.md
