# Reactivity and state checklist

## Correct reactive intent

- `@reactive.calc`: derive values only (no side effects)
- `@reactive.effect`: side effects and orchestration
- `@render.*`: UI-facing output rendering

## Invalidation control

- Use `@reactive.event()` for user-triggered expensive work.
- Use `reactive.isolate()` when reading dependencies without subscribing.
- Use `req(...)` to halt until required state/input exists.
- Use `reactive.invalidate_later()` only when periodic recompute is intended.

## Mutable object safety

Avoid in-place mutation of lists/dicts stored in reactive state.

Prefer:

- `new_list = old_list + [item]`
- `new_list = [transform(x) for x in old_list]`
- `new_dict = {**old_dict, "k": v}`
- explicit `.copy()` where needed

Why: in-place mutation can fail to trigger invalidation and can leak changes into unrelated consumers.

## Module boundaries

- Encapsulate repeated reactive+UI patterns into modules.
- Keep IDs unique per module instance.
- Keep modules composable and narrowly scoped.
