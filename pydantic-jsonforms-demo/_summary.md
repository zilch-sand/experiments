Demonstrating an integrated approach, this project uses Pydantic models as the central source for data validation, automatically generating a JSON Schema to power dynamic forms via [JSONForms](https://jsonforms.io/). A FastAPI backend validates submitted form data using the same models, ensuring consistent rules for fields such as email, URLs, dates, and array lengths. While Pydantic handles all structural validation and most constraints, UI layout and complex interactions (such as grouping or custom display logic) are managed separately using the JSONForms UI schema. The demo features a browser client that fetches the schema from the API and validates user input server-side, streamlining form configuration and validation.

Key findings:
- Validation logic (types, required fields, constraints) is defined once in Pydantic, reducing duplication.
- UI schema for layout must be separately defined for JSONForms; not covered by Pydantic.
- Complex, cross-field validation (e.g., date ordering) can be expressed in Pydantic, but custom errors may need to be surfaced via the API.
- Example repo: [Pydantic](https://docs.pydantic.dev/latest/) + FastAPI + JSONForms vanilla demo.
