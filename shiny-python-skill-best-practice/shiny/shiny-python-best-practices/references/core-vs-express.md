# Core vs Express decision guide

Use this quick decision matrix:

- Prefer **Express** when:
  - The app is small/prototype-stage.
  - Speed of authoring matters most.
  - Implicit output placement is acceptable.

- Prefer **Core** when:
  - App is medium/large or long-lived.
  - You need explicit UI/server separation.
  - You expect significant refactoring and modular decomposition.

- Migration principle:
  - Express and Core share reactive foundations.
  - Move to Core when structural clarity and explicit placement become more important than minimal syntax.

- R-to-Python caution:
  - In Python, outputs are primarily decorator-driven.
  - Input values are callables: `input.foo()`.
  - Keep namespace discipline with modules rather than ad-hoc ID prefixes.
