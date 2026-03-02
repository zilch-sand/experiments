# Repository Code Walkthrough

*2026-03-02T11:34:58Z by Showboat 0.6.1*
<!-- showboat-id: c8454367-d894-44f9-9563-a8609220818f -->

## Overview

This repository is a collection of independent experiments, each exploring a different pattern or tool combination. The walkthrough below is a linear tour of every experiment — starting from the repo root and diving into each sub-folder, with real code excerpts at every step.

The experiments are:
1. **cli-tools-pattern** — how to package multiple CLI commands in a single Python package
2. **jsonforms-pydantic-demo** — a full-stack Pydantic → JSONForms form generator
3. **llm-classification-app** — a Streamlit/FastAPI app for LLM-based text classification
4. **posit_connect_static_tool_test** — stress-testing a static HTML tool deployed on Posit Connect
5. **pydantic-jsonforms-demo** — showboat + rodney documentation for the pydantic demo
6. **readme-summaries-setup** — GitHub Actions workflow that auto-generates README summaries with GPT-4.1
7. **simonw-tools-exploration** — analysis of Simon Willison's single-file browser tools infrastructure
8. **wos-fast5k-playwright** — Playwright script that bulk-exports Web of Science results in 5,000-record batches

Let's start at the repo root.

```bash
ls /home/runner/work/experiments/experiments/
```

```output
AGENTS.md
CLAUDE.md
README.md
cli-tools-pattern
code-walkthrough
jsonforms-pydantic-demo
llm-classification-app
posit_connect_static_tool_test
pydantic-jsonforms-demo
readme-summaries-setup
requirements.txt
simonw-tools-exploration
wos-fast5k-playwright
```

## Repo Root

The root contains a `requirements.txt` (shared dependencies for the readme-summaries automation), plus `AGENTS.md` / `CLAUDE.md` (guidelines for AI coding agents), and a top-level `README.md` that is itself auto-generated. Each sub-folder is a self-contained experiment.

```bash
cat /home/runner/work/experiments/experiments/requirements.txt
```

```output
cogapp
llm
llm-github-models
```

The root `requirements.txt` lists exactly three packages: `cogapp` (a code generation preprocessor), `llm` (Simon Willison's LLM CLI), and `llm-github-models` (the GitHub Models backend plugin). These three together power the automated README summary workflow covered later.

---

## 1. cli-tools-pattern

This experiment answers the question: *how do you ship multiple CLI commands inside one Python package?* The trick is `[project.scripts]` in `pyproject.toml`.

```bash
ls /home/runner/work/experiments/experiments/cli-tools-pattern/
```

```output
README.md
_summary.md
notes.md
pyproject.toml
src
```

### pyproject.toml — the entry-point declaration

The `pyproject.toml` maps command names to Python callables. When the package is installed (via `pip install -e .` or `uv pip install -e .`), those callables become executable commands on the system PATH.

```bash
cat /home/runner/work/experiments/experiments/cli-tools-pattern/pyproject.toml
```

```output
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "cli-tools-demo"
version = "0.1.0"
description = "Demo package with multiple CLI entry points."
readme = "README.md"
requires-python = ">=3.9"

[project.scripts]
hello-world = "cli_tools_demo.cli:hello_world"
goodbye-world = "cli_tools_demo.cli:goodbye_world"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

The `[project.scripts]` block is the core: `hello-world` maps to `cli_tools_demo.cli:hello_world` and `goodbye-world` maps to `cli_tools_demo.cli:goodbye_world`. Python's packaging machinery generates thin wrapper scripts that call those functions when you type the command name in a terminal.

```bash
cat /home/runner/work/experiments/experiments/cli-tools-pattern/src/cli_tools_demo/cli.py
```

```output
"""Console entry points for the demo package."""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Example CLI tools.")
    parser.add_argument(
        "--name",
        default="world",
        help="Name to greet or bid farewell (default: world).",
    )
    return parser


def hello_world() -> None:
    """Entry point for the hello-world CLI."""
    parser = build_parser()
    args = parser.parse_args()
    print(f"Hello, {args.name}!")


def goodbye_world() -> None:
    """Entry point for the goodbye-world CLI."""
    parser = build_parser()
    args = parser.parse_args()
    print(f"Goodbye, {args.name}!")
```

The implementation is deliberately minimal — both commands share a single `argparse` parser built by `build_parser()` and differ only in their output string. The real point of the experiment is the *packaging*, not the commands themselves. Notice there's no `if __name__ == '__main__'` guard — these are pure callables, which is exactly what `[project.scripts]` expects.

```bash
head -20 /home/runner/work/experiments/experiments/cli-tools-pattern/src/cli_tools_demo/cli.py
```

```output
"""Console entry points for the demo package."""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Example CLI tools.")
    parser.add_argument(
        "--name",
        default="world",
        help="Name to greet or bid farewell (default: world).",
    )
    return parser


def hello_world() -> None:
    """Entry point for the hello-world CLI."""
    parser = build_parser()
    args = parser.parse_args()
```

---

## 2. pydantic-jsonforms-demo

This experiment builds a full-stack form generator: a **Python Pydantic model** is the single source of truth. FastAPI exposes the JSON Schema derived from that model, and a **React + JSONForms + Material UI** frontend fetches it and renders a dynamic form — complete with live server-side validation.

```bash
ls /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/
```

```output
README.md
_summary.md
app.py
jsonforms-client
notes.md
pyproject.toml
schema.py
uv.lock
```

### schema.py — the single source of truth

All data models live in `schema.py`. Pydantic automatically generates a JSON Schema from these models, which is then served by FastAPI and consumed by the React frontend.

```bash
cat /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/schema.py
```

```output
from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator, model_validator
from datetime import date
from typing import Literal

# Data schema---------------------------------

class PortfolioMeta(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    owner_email: EmailStr
    created_on: date = Field(default_factory=date.today)
    visibility: Literal["private", "team", "public"] = "private"


class ProjectMeta(BaseModel):
    name: str = Field(..., min_length=3, max_length=60)
    status: Literal["planned", "active", "paused", "completed"]
    start_date: date
    end_date: date | None = None
    budget_usd: float = Field(..., ge=0, le=5_000_000)
    repo_url: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("tags")
    @classmethod
    def tags_unique_and_clean(cls, tags: list[str]) -> list[str]:
        cleaned = [tag.strip().lower() for tag in tags if tag.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("tags must be unique after normalization")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectMeta":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.status == "completed" and not self.end_date:
            raise ValueError("completed projects must include end_date")
        return self


class Project(BaseModel):
    meta: ProjectMeta
    summary: str = Field(..., min_length=10, max_length=400)
    contributors: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("contributors")
    @classmethod
    def contributors_non_empty(cls, contributors: list[str]) -> list[str]:
        cleaned = [name.strip() for name in contributors if name.strip()]
        if len(cleaned) < len(contributors):
            raise ValueError("contributors must not contain empty names")
        return cleaned


class Portfolio(BaseModel):
    meta: PortfolioMeta
    projects: list[Project] = Field(..., min_length=1, max_length=6)



# Visual schema---------------------------------

PORTFOLIO_UI_SCHEMA: dict = {
    "type": "VerticalLayout",
    "elements": [
        {
            "type": "Group",
            "label": "Portfolio",
            "elements": [
                {"type": "Control", "scope": "#/properties/meta/properties/title"},
                {"type": "Control", "scope": "#/properties/meta/properties/owner_email"},
                {"type": "Control", "scope": "#/properties/meta/properties/created_on"},
                {"type": "Control", "scope": "#/properties/meta/properties/visibility"},
            ],
        },
        {
            "type": "Group",
            "label": "Projects",
            "elements": [
                {
                    "type": "Control",
                    "scope": "#/properties/projects",
                    "options": {
                        "detail": {
                            "type": "VerticalLayout",
                            "elements": [
                                {
                                    "type": "Group",
                                    "label": "Project Meta",
                                    "elements": [
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/name",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/status",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/start_date",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/end_date",
                                            "rule": {
                                                "effect": "SHOW",
                                                "condition": {
                                                    "scope": "#/properties/meta/properties/status",
                                                    "schema": {"const": "completed"},
                                                },
                                            },
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/budget_usd",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/repo_url",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/tags",
                                        },
                                    ],
                                },
                                {"type": "Control", "scope": "#/properties/summary"},
                                {"type": "Control", "scope": "#/properties/contributors"},
                            ],
                        }
                    },
                }
            ],
        },
    ],
}

```

```bash
head -60 /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/schema.py
```

```output
from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator, model_validator
from datetime import date
from typing import Literal

# Data schema---------------------------------

class PortfolioMeta(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    owner_email: EmailStr
    created_on: date = Field(default_factory=date.today)
    visibility: Literal["private", "team", "public"] = "private"


class ProjectMeta(BaseModel):
    name: str = Field(..., min_length=3, max_length=60)
    status: Literal["planned", "active", "paused", "completed"]
    start_date: date
    end_date: date | None = None
    budget_usd: float = Field(..., ge=0, le=5_000_000)
    repo_url: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("tags")
    @classmethod
    def tags_unique_and_clean(cls, tags: list[str]) -> list[str]:
        cleaned = [tag.strip().lower() for tag in tags if tag.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("tags must be unique after normalization")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectMeta":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.status == "completed" and not self.end_date:
            raise ValueError("completed projects must include end_date")
        return self


class Project(BaseModel):
    meta: ProjectMeta
    summary: str = Field(..., min_length=10, max_length=400)
    contributors: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("contributors")
    @classmethod
    def contributors_non_empty(cls, contributors: list[str]) -> list[str]:
        cleaned = [name.strip() for name in contributors if name.strip()]
        if len(cleaned) < len(contributors):
            raise ValueError("contributors must not contain empty names")
        return cleaned


class Portfolio(BaseModel):
    meta: PortfolioMeta
    projects: list[Project] = Field(..., min_length=1, max_length=6)



# Visual schema---------------------------------
```

The models form a hierarchy: `Portfolio` → `Project` → `ProjectMeta`. Custom Pydantic validators enforce business rules (unique tags, date ordering, completed projects must have an end date) *at the Python level*, so those constraints are caught on both the API side and propagated as JSON Schema constraints to the frontend.

There's also a *visual schema* (defined later in schema.py) which is the JSONForms UI schema — a JSON tree describing how to lay out the fields in tabs, groups, and conditionally-shown controls. The 'end_date' field, for example, only appears when status is set to 'completed'.

### app.py — the FastAPI backend

The backend has three endpoints: `GET /schema` (returns JSON Schema + UI schema), `POST /validate` (validates a submitted portfolio), and `GET /` (serves the React app). Here are the key route handlers:

```bash
grep -n 'def \|@app\.' /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/app.py
```

```output
10:def flatten_nullable_anyof(schema: dict) -> dict:
66:@app.post("/validate")
67:async def validate_portfolio(payload: dict) -> dict:
75:@app.get("/schema")
76:async def portfolio_schema() -> dict:
81:@app.get("/ui-schema")
82:async def portfolio_ui_schema() -> dict:
```

```bash
sed -n '60,90p' /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/app.py
```

```output
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/validate")
async def validate_portfolio(payload: dict) -> dict:
    try:
        portfolio = Portfolio.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=jsonable_encoder(exc.errors()))
    return {"message": "Portfolio is valid", "portfolio": portfolio.model_dump()}


@app.get("/schema")
async def portfolio_schema() -> dict:
    schema = Portfolio.model_json_schema()
    return flatten_nullable_anyof(schema)


@app.get("/ui-schema")
async def portfolio_ui_schema() -> dict:
    return PORTFOLIO_UI_SCHEMA
```

`Portfolio.model_json_schema()` is the magic line — Pydantic generates the JSON Schema automatically from the Python types and `Field` constraints. The `flatten_nullable_anyof` helper post-processes the schema to simplify nullable field representations, making them more palatable for JSONForms.

The frontend is a Vite + React app. Its key file is `App.tsx`:

```bash
grep -n 'fetch\|JsonForms\|useEffect\|useState' /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/jsonforms-client/src/App.tsx | head -20
```

```output
3:import { JsonFormsDemo } from './components/JsonFormsDemo';
10:        <JsonFormsDemo />
```

```bash
grep -n 'fetch\|JsonForms\|useEffect\|useState\|schema\|validate' /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/jsonforms-client/src/components/JsonFormsDemo.tsx | head -25
```

```output
1:import { useEffect, useMemo, useState } from 'react';
2:import { JsonForms } from '@jsonforms/react';
49:export const JsonFormsDemo = () => {
50:  const [schema, setSchema] = useState<Record<string, unknown> | null>(null);
51:  const [uiSchema, setUiSchema] = useState<Record<string, unknown> | null>(null);
52:  const [data, setData] = useState(initialData);
53:  const [errors, setErrors] = useState<unknown[]>([]);
54:  const [apiStatus, setApiStatus] = useState<ApiStatus>({
59:  useEffect(() => {
61:      fetch(`${API_BASE}/schema`).then((response) => response.json()),
62:      fetch(`${API_BASE}/ui-schema`).then((response) => response.json()),
64:      .then(([schemaPayload, uiSchemaPayload]) => {
65:        setSchema(schemaPayload);
71:          message: `Failed to load schema: ${error.message}`,
88:      const response = await fetch(`${API_BASE}/validate`, {
124:  if (!schema || !uiSchema) {
128:          Loading schema from {API_BASE}...
164:          <JsonForms
165:            schema={schema}
166:            uischema={uiSchema}
```

```bash
sed -n '59,100p' /home/runner/work/experiments/experiments/pydantic-jsonforms-demo/jsonforms-client/src/components/JsonFormsDemo.tsx
```

```output
  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/schema`).then((response) => response.json()),
      fetch(`${API_BASE}/ui-schema`).then((response) => response.json()),
    ])
      .then(([schemaPayload, uiSchemaPayload]) => {
        setSchema(schemaPayload);
        setUiSchema(uiSchemaPayload);
      })
      .catch((error: Error) => {
        setApiStatus({
          state: 'error',
          message: `Failed to load schema: ${error.message}`,
        });
      });
  }, []);

  const stringifiedData = useMemo(
    () => JSON.stringify(data, null, 2),
    [data],
  );
  const stringifiedErrors = useMemo(
    () => JSON.stringify(errors, null, 2),
    [errors],
  );

  const handleValidate = async () => {
    setApiStatus({ state: 'loading', message: 'Validating...' });
    try {
      const response = await fetch(`${API_BASE}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const payload = await response.json();
      if (!response.ok) {
        const detail = payload?.detail;
        const detailMessage = Array.isArray(detail)
          ? detail
              .map((item) => {
                const path = Array.isArray(item?.loc)
                  ? item.loc.join('.')
```

On mount, the component fetches `/schema` and `/ui-schema` in parallel via `Promise.all`. The schema drives JSONForms' validation engine; the UI schema controls how fields are arranged. `handleValidate` sends the current form data to `POST /validate` and surfaces Pydantic errors (e.g. 'end_date cannot be before start_date') directly to the user.

This is the pattern's payoff: you write validation logic *once* in Python, and it is enforced both on the server and surfaced to the user through the React form.

---

## 3. llm-classification-app

The most substantial experiment — a multi-tab Streamlit web application for classifying text with LLMs. It covers single classification, a model comparison 'arena', batch processing via Vertex AI, and cost estimation.

```bash
ls /home/runner/work/experiments/experiments/llm-classification-app/
```

```output
README.md
app.py
backend
batch_state
llm-prices
notes.md
pyproject.toml
tests
```

```bash
ls /home/runner/work/experiments/experiments/llm-classification-app/backend/
```

```output
__init__.py
arena.py
batch.py
classifier.py
feedback.py
fuzzy_match.py
models.py
pricing.py
prompt.py
```

The app is split cleanly: `app.py` is the Streamlit front-end (3 tabs), and the `backend/` package contains all business logic. This separation means the backend could be served via FastAPI independently of Streamlit.

### backend/classifier.py — the classification engine

The core of the app. `classify` takes a text, a list of labels, and a prompt template, calls an LLM via `litellm`, and returns the best-matching label.

```bash
grep -n 'def \|class ' /home/runner/work/experiments/experiments/llm-classification-app/backend/classifier.py
```

```output
16:class ClassificationResult:
24:def classify_single_row(
56:def classify_rows(
100:def count_tokens_for_prompt(prompt_text: str, model_id: str) -> int:
112:def estimate_tokens_from_sample(
137:def apply_results_to_dataframe(
```

```bash
sed -n '16,55p' /home/runner/work/experiments/experiments/llm-classification-app/backend/classifier.py
```

```output
class ClassificationResult:
    row_index: int
    raw_response: str
    matched_label: str | list[str]
    input_tokens: int
    output_tokens: int


def classify_single_row(
    model_config: ModelConfig,
    prompt_text: str,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
) -> ClassificationResult:
    """Classify a single row using litellm."""
    kwargs = model_config.to_litellm_kwargs()

    response = litellm.completion(
        messages=[{"role": "user", "content": prompt_text}],
        **kwargs,
    )

    raw = response.choices[0].message.content.strip()
    usage = response.usage

    if multi_label:
        matched = fuzzy_match_multi_label(raw, categories, delimiter)
    else:
        matched = fuzzy_match_label(raw, categories) or raw

    return ClassificationResult(
        row_index=0,
        raw_response=raw,
        matched_label=matched,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )


```

`classify_single_row` sends a prompt to any LLM supported by `litellm`, extracts the raw text response, then passes it through `fuzzy_match_label` (or `fuzzy_match_multi_label` for multi-label tasks) to map the free-text response to one of the valid labels. This is important because LLMs don't always return exactly the label text you asked for.

### backend/fuzzy_match.py — tolerant label matching

Because LLM responses are free text, the app uses fuzzy matching (via `rapidfuzz`) to map the model's response to the closest valid label.

```bash
cat /home/runner/work/experiments/experiments/llm-classification-app/backend/fuzzy_match.py
```

```output
"""Fuzzy matching for classification results against known categories."""

from rapidfuzz import fuzz, process


def fuzzy_match_label(
    prediction: str,
    categories: list[str],
    threshold: int = 60,
) -> str | None:
    """Match a prediction to the closest category using fuzzy matching.

    Returns the matched category or None if no match above threshold.
    """
    if not prediction or not categories:
        return None

    prediction = prediction.strip()

    # Exact match first (case-insensitive)
    for cat in categories:
        if prediction.lower() == cat.lower():
            return cat

    # Fuzzy match
    result = process.extractOne(
        prediction, categories, scorer=fuzz.ratio, score_cutoff=threshold
    )
    if result:
        return result[0]
    return None


def fuzzy_match_multi_label(
    prediction: str,
    categories: list[str],
    delimiter: str = "|",
    threshold: int = 60,
) -> list[str]:
    """Match multi-label predictions to categories.

    Splits prediction by delimiter and fuzzy-matches each part.
    """
    if not prediction:
        return []

    parts = [p.strip() for p in prediction.split(delimiter) if p.strip()]
    matched = []
    for part in parts:
        match = fuzzy_match_label(part, categories, threshold)
        if match and match not in matched:
            matched.append(match)
    return matched


def find_safe_delimiter(categories: list[str]) -> str:
    """Find a delimiter that doesn't appear in any category label."""
    candidates = ["|", "||", ";;", "###", "^^^"]
    for delim in candidates:
        if not any(delim in cat for cat in categories):
            return delim
    return "|||"
```

```bash
head -35 /home/runner/work/experiments/experiments/llm-classification-app/backend/fuzzy_match.py
```

```output
"""Fuzzy matching for classification results against known categories."""

from rapidfuzz import fuzz, process


def fuzzy_match_label(
    prediction: str,
    categories: list[str],
    threshold: int = 60,
) -> str | None:
    """Match a prediction to the closest category using fuzzy matching.

    Returns the matched category or None if no match above threshold.
    """
    if not prediction or not categories:
        return None

    prediction = prediction.strip()

    # Exact match first (case-insensitive)
    for cat in categories:
        if prediction.lower() == cat.lower():
            return cat

    # Fuzzy match
    result = process.extractOne(
        prediction, categories, scorer=fuzz.ratio, score_cutoff=threshold
    )
    if result:
        return result[0]
    return None


def fuzzy_match_multi_label(
    prediction: str,
```

The matching strategy is: exact match first (case-insensitive), then fuzzy match via `rapidfuzz` Levenshtein ratio with a threshold of 60. For multi-label tasks the model response is split by a delimiter (defaulting to '|') and each part is fuzzy-matched independently. `find_safe_delimiter` picks a delimiter that doesn't appear in any of the actual category names, preventing ambiguous splits.

### backend/arena.py — model comparison

The arena lets you run the same classification on two different models side-by-side, then optionally ask a third 'judge' LLM to decide which result is better.

```bash
grep -n 'def \|class ' /home/runner/work/experiments/experiments/llm-classification-app/backend/arena.py
```

```output
34:def run_arena(
58:        def model_progress(current, total):
104:def judge_arena_results(
153:def export_arena_data(
```

```bash
sed -n '34,103p' /home/runner/work/experiments/experiments/llm-classification-app/backend/arena.py
```

```output
def run_arena(
    df: pd.DataFrame,
    model_configs: list[ModelConfig],
    prompt_template: PromptTemplate,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
    max_rows: int = 10,
    progress_callback=None,
) -> dict:
    """Run classification with multiple models for comparison.

    Returns a dict with results from each model and aggregated data.
    """
    all_results = {}
    token_stats = {}
    total_models = len(model_configs)

    for model_idx, config in enumerate(model_configs):
        model_key = f"{config.display_name} (T={config.temperature}"
        if config.thinking_level:
            model_key += f", think={config.thinking_level}"
        model_key += ")"

        def model_progress(current, total):
            if progress_callback:
                overall = (model_idx * max_rows + current) / (total_models * max_rows)
                progress_callback(overall)

        results = classify_rows(
            df=df,
            model_config=config,
            prompt_template=prompt_template,
            categories=categories,
            multi_label=multi_label,
            delimiter=delimiter,
            max_rows=max_rows,
            progress_callback=model_progress,
        )

        all_results[model_key] = results

        # Calculate token stats
        total_input = sum(r.input_tokens for r in results)
        total_output = sum(r.output_tokens for r in results)
        avg_input = total_input / len(results) if results else 0
        avg_output = total_output / len(results) if results else 0

        token_stats[model_key] = {
            "avg_input_tokens": avg_input,
            "avg_output_tokens": avg_output,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "sample_cost": config.price.estimate_cost(total_input, total_output)
            if config.price
            else 0,
            "estimated_full_cost": estimate_dataset_cost(
                config.price, avg_input, avg_output, len(df)
            )
            if config.price
            else 0,
        }

    return {
        "results": all_results,
        "token_stats": token_stats,
        "num_rows_tested": min(max_rows, len(df)),
    }


```

`run_arena` iterates over multiple model configs and calls `classify_rows` for each, collecting results and computing token usage stats. The progress callback allows the Streamlit UI to show a live progress bar scaled across *all* models. Cost estimation is done by multiplying token counts by the per-token prices from the `llm-prices` submodule.

### backend/batch.py — Vertex AI batch jobs

For large datasets, the app can submit a Vertex AI batch prediction job instead of calling the API row-by-row. State is persisted to a JSON file so the UI can track job status across page reloads.

```bash
grep -n 'def \|class ' /home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py
```

```output
20:def _ensure_batch_dir():
24:def save_batch_id(batch_id: str, metadata: dict | None = None):
37:def update_batch_status(batch_id: str, status: str, extra: dict | None = None):
51:def load_tracked_batches() -> list[dict]:
63:def cleanup_batch(batch_id: str):
70:def prepare_batch_requests(
103:def submit_batch(
144:def check_batch_status(batch_id: str) -> dict:
161:def retrieve_batch_results(
```

```bash
sed -n '70,145p' /home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py
```

```output
def prepare_batch_requests(
    df: pd.DataFrame,
    model_config: ModelConfig,
    prompt_template: PromptTemplate,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
) -> list[dict]:
    """Prepare batch request payloads for Vertex AI batch prediction.

    Returns a list of request dicts in the format expected by Vertex AI
    batch prediction (JSONL format).
    """
    requests = []
    for idx, (_, row) in enumerate(df.iterrows()):
        prompt_text = prompt_template.render(
            row.to_dict(), categories, multi_label, delimiter
        )
        request = {
            "custom_id": f"row-{idx}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model_config.vertex_id.replace("vertex_ai/", ""),
                "messages": [{"role": "user", "content": prompt_text}],
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
            },
        }
        requests.append(request)
    return requests


def submit_batch(
    requests: list[dict],
    model_config: ModelConfig,
    description: str = "",
) -> str:
    """Submit a batch job to Vertex AI.

    Returns the batch ID for tracking.
    """
    import tempfile

    # Write requests to a JSONL file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    ) as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")
        jsonl_path = f.name

    try:
        # Use litellm's batch API
        batch_response = litellm.create_batch(
            input_file_id=jsonl_path,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": description},
        )
        batch_id = batch_response.id

        # Save batch ID for recovery
        save_batch_id(batch_id, {
            "model": model_config.vertex_id,
            "description": description,
            "num_requests": len(requests),
        })

        return batch_id
    finally:
        os.unlink(jsonl_path)


def check_batch_status(batch_id: str) -> dict:
    """Check the status of a batch job."""
```

The batch flow: `prepare_batch_requests` renders each row's prompt and formats it as a JSONL entry in the OpenAI batch format. `submit_batch` writes those requests to a temp file and calls `litellm.create_batch`, then saves the batch ID to `batch_state/` for recovery. `check_batch_status` and `retrieve_batch_results` let the UI poll for completion and download results, running through the same fuzzy-match pipeline as the interactive path.

### app.py — the Streamlit UI

The Streamlit app wires everything together in three tabs: **Classify** (interactive single/CSV classification), **Arena** (side-by-side model comparison), and **Batch Jobs** (Vertex AI async jobs).

```bash
grep -n 'st\.tab\|tab1\|tab2\|tab3\|with tab' /home/runner/work/experiments/experiments/llm-classification-app/app.py | head -20
```

```output
85:tab_classify, tab_arena, tab_batch = st.tabs(
93:with tab_classify:
378:with tab_arena:
534:            st.table(pd.DataFrame(stats_rows))
584:with tab_batch:
```

```bash
sed -n '85,95p' /home/runner/work/experiments/experiments/llm-classification-app/app.py
```

```output
tab_classify, tab_arena, tab_batch = st.tabs(
    ["🏷️ Classify", "🏟️ Arena", "📦 Batch Jobs"]
)


# =========================================================================
#  CLASSIFY TAB
# =========================================================================
with tab_classify:
    st.header("Text Classification")

```

Each `with tab_*:` block is fully self-contained — Streamlit re-renders only the active tab's widgets. The three tabs correspond directly to the three backend modules: `classifier.py` → Classify tab, `arena.py` → Arena tab, `batch.py` → Batch Jobs tab.

---

## 4. posit_connect_static_tool_test

A focused stress test of what a single-file HTML tool can and cannot do when hosted as a static asset on Posit Connect. The experiment found that most browser features work, but external API calls fail due to CSP/CORS restrictions — requiring a proxy.

```bash
ls /home/runner/work/experiments/experiments/posit_connect_static_tool_test/
```

```output
README.md
_summary.md
app.py
notes.md
requirements.txt
static
```

```bash
grep -n 'def \|@app\.' /home/runner/work/experiments/experiments/posit_connect_static_tool_test/app.py
```

```output
15:@app.get("/")
16:async def index():
22:@app.get("/index.html")
23:async def index_html():
33:@app.get("/api/proxy")
34:async def proxy(url: str = Query(..., description="Absolute URL to fetch server-side")):
```

```bash
cat /home/runner/work/experiments/experiments/posit_connect_static_tool_test/app.py
```

```output
# app.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
import httpx
from pathlib import Path

app = FastAPI(title="Connect Proxy Test")

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "static" / "index.html"


@app.get("/")
async def index():
    if not HTML_FILE.exists():
        raise HTTPException(status_code=500, detail=f"HTML file not found: {HTML_FILE}")
    return FileResponse(HTML_FILE, media_type="text/html")


@app.get("/index.html")
async def index_html():
    return await index()

# Optional: keep this permissive for testing, then lock it down later.
ALLOWED_HOSTS = {
    "api.github.com",
    "httpbin.org",
    "raw.githubusercontent.com",
}

@app.get("/api/proxy")
async def proxy(url: str = Query(..., description="Absolute URL to fetch server-side")):
    # Basic validation
    try:
        u = httpx.URL(url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL")

    if u.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http/https supported")

    host = (u.host or "").lower()
    if host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail=f"Host not allowed: {host}")

    # Fetch server-side (CSP does not apply here)
    timeout = httpx.Timeout(20.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            r = await client.get(str(u), headers={"User-Agent": "connect-proxy-test/1.0"})
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}")

    # Return response with the upstream content-type if present
    content_type = r.headers.get("content-type", "text/plain; charset=utf-8")

    # Safety: cap response size to keep the demo from pulling huge bodies
    body = r.content
    max_bytes = 1_000_000
    if len(body) > max_bytes:
        body = body[:max_bytes]

    return Response(
        content=body,
        status_code=r.status_code,
        media_type=content_type.split(";")[0].strip(),
        headers={"X-Upstream-Status": str(r.status_code)},
    )```
```

The FastAPI backend has one important endpoint: `GET /api/proxy?url=...`. The static HTML page calls this endpoint instead of calling external APIs directly. The proxy validates:

1. The URL is a valid http/https URL
2. The host is in an explicit allowlist (`ALLOWED_HOSTS`)
3. The response body is capped at 1 MB

This sidesteps the browser's CSP restrictions because the network request is made server-side. The pattern is: static HTML for UI logic, thin Python proxy for anything that needs to cross origin boundaries.

---

## 5. readme-summaries-setup

This experiment automates README summary generation for every sub-folder in the repo. It runs in GitHub Actions on every push to main.

```bash
ls /home/runner/work/experiments/experiments/readme-summaries-setup/
```

```output
README.md
_summary.md
notes.md
```

```bash
cat /home/runner/work/experiments/experiments/.github/workflows/update-readme.yml
```

```output
name: Update README with cogapp

on:
  push:
    branches:
      - main

permissions:
  contents: write
  models: read

jobs:
  update-readme:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 0  # Fetch all history for git log dates

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: 'requirements.txt'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run cogapp to update README
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cog -r -P README.md

      - name: Commit and push if changed
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add README.md
          git add */_summary.md 2>/dev/null || true
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Auto-update README with cogapp [skip ci]"
            git push
          fi
```

The workflow runs `cog -r -P README.md` — the `-r` flag means *rewrite in place*, and `-P` means *pass the file through cog's preprocessor*. Cog finds special `[[[cog ... ]]] ... [[[end]]]` markers in the README and replaces the content between them with the output of the embedded Python code.

No API key is needed because the workflow uses `GITHUB_TOKEN` and the `llm-github-models` plugin, which authenticates against the GitHub Models API using the built-in token.

Let's see the README's cog block:

```bash
grep -n 'cog\|llm\|summary' /home/runner/work/experiments/experiments/README.md | head -20
```

```output
16:The README is auto-updated with a list of projects and short summaries using `cog` and GitHub Actions.
18:<!--[[[cog
63:    summary_path = folder_path / "_summary.md"
92:    # Check if summary already exists
93:    if summary_path.exists():
94:        # Use cached summary
95:        with open(summary_path, 'r') as f:
102:        # Generate new summary using llm command
105:            ['llm', '-m', MODEL, '-s', prompt],
120:            with open(summary_path, 'w') as f:
238:Automated README summary generation is enabled in this project using a combination of GitHub Actions, the llm CLI, and the cog tool. Whenever code is pushed to the main branch, the workflow scans repository directories, reads each README, and—if a cached summary file is missing—uses the github/gpt-4.1 model (via the llm-github-models plugin) to generate concise summaries. This setup works seamlessly in CI environments with no extra API key required; locally, users must install dependencies from requirements.txt and configure llm with a GitHub token that allows access to GitHub Models. The process ensures that summaries are always current and automatically committed back to the repository. Find more details and setup instructions in the main README and recommended tools: [llm](https://github.com/llm-tools/llm), [cog](https://github.com/replicate/cog).
242:- Uses github/gpt-4.1 model for summarization via [llm-github-models](https://github.com/llm-tools/llm-github-models)
243:- Local setup requires authenticated llm and dependencies from requirements.txt
```

```bash
sed -n '18,130p' /home/runner/work/experiments/experiments/README.md
```

```output
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
```

The cog Python block does all the heavy lifting:
1. Walks subdirectories, getting their first git commit date for ordering
2. For each folder, checks if a `_summary.md` cache file exists
3. If no cache: calls `llm -m github/gpt-4.1` with the folder's README piped to stdin, saves the output to `_summary.md`
4. Prints the folder name (as a link), date, and summary into the README

The caching is important — without it, the workflow would call the LLM API for every folder on every push to main.

---

## 6. simonw-tools-exploration

An exploration of how Simon Willison builds a directory of single-file browser utilities. The experiment reverse-engineers the infrastructure (build scripts, metadata, index generation) into a reusable bare-bones template.

```bash
ls /home/runner/work/experiments/experiments/simonw-tools-exploration/
```

```output
README.md
_summary.md
bare-bones-site
notes.md
```

```bash
ls /home/runner/work/experiments/experiments/simonw-tools-exploration/bare-bones-site/
```

```output
README.md
_config.yml
build.sh
build_index.py
gather_links.py
sample-tool.html
```

The bare-bones site is designed to be forked. It contains:
- `sample-tool.html` — a self-contained HTML tool (no build step, no npm)
- `gather_links.py` — scrapes links from each HTML file's head
- `build_index.py` — generates an `index.md` listing all tools with their metadata
- `build.sh` — runs both Python scripts in sequence
- `_config.yml` — Jekyll config for GitHub Pages
- A `pages.yml` GitHub Actions workflow (in .github/workflows) for automatic deployment

Let's look at the build chain:

```bash
cat /home/runner/work/experiments/experiments/simonw-tools-exploration/bare-bones-site/build.sh
```

```output
#!/bin/bash
# build.sh – orchestrate the bare-bones tools site build
set -e

# Make sure we have full git history so commit dates are accurate
if [ -f .git/shallow ]; then
    git fetch --unshallow
fi

echo "=== Gathering tool metadata ==="
python gather_links.py

echo "=== Building index.html ==="
python build_index.py

echo "=== Done! ==="
```

```bash
cat /home/runner/work/experiments/experiments/simonw-tools-exploration/bare-bones-site/gather_links.py
```

```output
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
```

`gather_links.py` scans all HTML files (excluding index.html), reads the `<title>` tag, looks for a companion `.docs.md` file for descriptions, queries git for creation/update dates, and writes all metadata to `tools.json`. Then `build_index.py` reads `tools.json` and generates the `index.html` listing. The whole chain is pure Python + standard library — no npm, no bundler. The GitHub Actions `pages.yml` workflow runs `build.sh` and deploys the output to GitHub Pages.

---

## 7. wos-fast5k-playwright

A Playwright (Node.js) script that bulk-exports Web of Science search results in precise 5,000-record batches. Web of Science caps exports at 1,000 records by default, but allows up to 5,000 if you specify a custom range — this script automates that entirely.

```bash
ls /home/runner/work/experiments/experiments/wos-fast5k-playwright/
```

```output
README.md
_summary.md
download_wos_fast5k.js
notes.md
searchstring.sql
```

```bash
grep -n 'const\|function\|async\|await\|export\|let\|var' /home/runner/work/experiments/experiments/wos-fast5k-playwright/download_wos_fast5k.js | head -40
```

```output
3: * Automate Web of Science "Fast 5K" exports in exact 5,000-document batches.
8: * - The page supports Fast 5K export with a custom record range.
11: *   node download_wos_fast5k.js --base-name "my_wos_export"
15:const fs = require('node:fs');
16:const path = require('node:path');
17:const { chromium } = require('playwright');
19:function loadDotEnv(dotEnvPath) {
21:  // variable is not already defined in the environment.
24:    const raw = fs.readFileSync(dotEnvPath, 'utf8');
25:    const lines = raw.split(/\r?\n/);
27:    for (const line of lines) {
28:      const trimmed = line.trim();
31:      const noExport = trimmed.startsWith('export ') ? trimmed.slice('export '.length) : trimmed;
32:      const eqIdx = noExport.indexOf('=');
35:      const key = noExport.slice(0, eqIdx).trim();
38:      let val = noExport.slice(eqIdx + 1).trim();
52:function parseArgs(argv) {
53:  const args = {
65:  for (let i = 2; i < argv.length; i += 1) {
66:    const arg = argv[i];
71:      const val = Number(argv[i + 1]);
80:      const raw = argv[i + 1] || '';
87:      const val = Number(argv[i + 1]);
95:      const val = Number(argv[i + 1]);
120:function batchRanges(total, batchSize) {
121:  const ranges = [];
122:  for (let start = 1; start <= total; start += batchSize) {
123:    const end = Math.min(start + batchSize - 1, total);
129:async function findTotalDocumentCount(page) {
130:  const candidateLocators = [
137:  for (const locator of candidateLocators) {
138:    const count = await locator.count();
140:      const text = (await locator.first().innerText()).trim();
141:      const numbers = text.match(/\d{1,3}(?:,\d{3})*|\d+/g);
143:        const parsed = Number(numbers[numbers.length - 1].replace(/,/g, ''));
151:  const bodyText = await page.locator('body').innerText();
152:  const patterns = [
157:  for (const pattern of patterns) {
158:    const matches = [...bodyText.matchAll(pattern)];
160:      for (const m of matches) {
```

```bash
sed -n '120,135p' /home/runner/work/experiments/experiments/wos-fast5k-playwright/download_wos_fast5k.js
```

```output
function batchRanges(total, batchSize) {
  const ranges = [];
  for (let start = 1; start <= total; start += batchSize) {
    const end = Math.min(start + batchSize - 1, total);
    ranges.push({ start, end });
  }
  return ranges;
}

async function findTotalDocumentCount(page) {
  const candidateLocators = [
    page.getByText(/\b\d{1,3}(?:,\d{3})*\s+documents?\b/i),
    page.getByText(/\bdocuments?\s*\(\s*\d{1,3}(?:,\d{3})*\s*\)/i),
    page.getByText(/\bresults?\s*\(\s*\d{1,3}(?:,\d{3})*\s*\)/i),
    page.getByText(/\bof\s+\d{1,3}(?:,\d{3})*\b/i),
  ];
```

`batchRanges(total, batchSize)` is the key math: it generates an array of `{start, end}` pairs that cover `1..total` in non-overlapping windows of `batchSize`. The final batch is automatically trimmed by `Math.min`.

`findTotalDocumentCount` is a robust scraper that tries multiple Playwright locators (matching different text patterns like '12,345 documents' or 'Results (12,345)') before falling back to a full-body text regex scan. This resilience is important because Web of Science's UI varies between institutional licenses.

```bash
grep -n 'for.*range\|exportBatch\|download\|batch' /home/runner/work/experiments/experiments/wos-fast5k-playwright/download_wos_fast5k.js | head -20
```

```output
3: * Automate Web of Science "Fast 5K" exports in exact 5,000-document batches.
11: *   node download_wos_fast5k.js --base-name "my_wos_export"
12: *   node download_wos_fast5k.js --headless false
55:    batchSize: 5000,
70:    } else if (arg === '--batch-size') {
73:        args.batchSize = val;
75:        throw new Error('--batch-size must be a positive number <= 50000');
120:function batchRanges(total, batchSize) {
122:  for (let start = 1; start <= total; start += batchSize) {
123:    const end = Math.min(start + batchSize - 1, total);
283:    // VS Code SQL formatters sometimes rewrite year ranges like:
404:  const [download] = await Promise.all([
405:    page.waitForEvent('download', { timeout: timeoutMs }),
411:  const suggested = path.basename(download.suggestedFilename());
419:  const savePath = path.resolve('./downloads', outputName);
420:  await download.saveAs(savePath);
440:  fs.mkdirSync(path.resolve('./downloads'), { recursive: true });
492:  const ranges = batchRanges(total, args.batchSize);
493:  console.log(`Preparing ${ranges.length} Fast 5K batch export(s):`, ranges);
501:  for (let i = 0; i < ranges.length; i += 1) {
```

```bash
sed -n '490,525p' /home/runner/work/experiments/experiments/wos-fast5k-playwright/download_wos_fast5k.js
```

```output
  console.log(`Detected total documents: ${total}`);

  const ranges = batchRanges(total, args.batchSize);
  console.log(`Preparing ${ranges.length} Fast 5K batch export(s):`, ranges);

  await page.evaluate(() => {
    const el = document.querySelector('body');
    if (!el) return;
    // no-op to keep lint happy in plain Node execution contexts
  });

  for (let i = 0; i < ranges.length; i += 1) {
    const range = ranges[i];
    console.log(`\n[${i + 1}/${ranges.length}] Exporting ${range.start}-${range.end}`);

    await openFast5kDialog(page, args.timeoutMs);
    await setRangeAndFileName(page, {
      ...range,
      baseName: args.baseName,
      index: i,
      timeoutMs: args.timeoutMs,
    });

    const fileName = await exportSingleBatch(page, {
      timeoutMs: args.timeoutMs,
      index: i,
      totalBatches: ranges.length,
      baseName: args.baseName,
    });
    console.log(`Downloaded: ${fileName}`);
  }

  console.log('\nAll Fast 5K exports completed successfully.');
  await browser.close();
}

```

The main loop is clean and readable: for each range, it opens the Fast 5K export dialog (`openFast5kDialog`), sets the start/end values and filename (`setRangeAndFileName`), then waits for the download event (`exportSingleBatch`). Playwright's `Promise.all([page.waitForEvent('download'), page.click(submit)])` ensures no race condition between triggering the download and listening for it.

Files are saved to `./downloads/` with sequential names so they can be easily merged later.

---

## 8. jsonforms-pydantic-demo

This folder contains executable documentation (a showboat `demo.md`) for the `pydantic-jsonforms-demo` app. It's a meta-experiment: using showboat + rodney (or Playwright) to *prove* a web application works by capturing live screenshots into the markdown.

```bash
ls /home/runner/work/experiments/experiments/jsonforms-pydantic-demo/
```

```output
README.md
_summary.md
demo.md
form-expanded.png
form-initial.png
form-validated.png
notes.md
```

```bash
head -60 /home/runner/work/experiments/experiments/jsonforms-pydantic-demo/demo.md
```

````output
# JSONForms + Pydantic Integration Demo

*2026-02-16T00:42:36Z by Showboat 0.5.0*

This demo showcases a full-stack integration between Pydantic models and JSONForms. The backend uses FastAPI with Pydantic for data validation, and the frontend uses React with JSONForms to dynamically generate forms from JSON Schema.

We'll use **rodney** (CLI browser automation) and **showboat** (executable documentation) to demonstrate the application.

## Starting the Backend

First, let's start the FastAPI backend which provides JSON Schema and validation endpoints.

```bash
curl -s http://localhost:8000/schema | python3 -m json.tool | head -40
```

```output
{
    "$defs": {
        "PortfolioMeta": {
            "properties": {
                "title": {
                    "maxLength": 80,
                    "minLength": 3,
                    "title": "Title",
                    "type": "string"
                },
                "owner_email": {
                    "format": "email",
                    "title": "Owner Email",
                    "type": "string"
                },
                "created_on": {
                    "format": "date",
                    "title": "Created On",
                    "type": "string"
                },
                "visibility": {
                    "default": "private",
                    "enum": [
                        "private",
                        "team",
                        "public"
                    ],
                    "title": "Visibility",
                    "type": "string"
                }
            },
            "required": [
                "title",
                "owner_email"
            ],
            "title": "PortfolioMeta",
            "type": "object"
        },
        "Project": {
            "properties": {
```

## Using Rodney for Browser Automation
````

The `demo.md` file is itself a showboat document — it mixes explanatory text with ```bash``` code blocks whose outputs are recorded inline. This means anyone can run `showboat verify demo.md` to re-execute all the commands and confirm the outputs still match. The screenshots (`form-initial.png`, `form-expanded.png`, `form-validated.png`) were captured by `rodney` (or Playwright) and embedded with `showboat image`.

```bash
grep -n 'image\|screenshot\|png' /home/runner/work/experiments/experiments/jsonforms-pydantic-demo/demo.md | head -15
```

```output
93:![Initial Form State](form-initial.png)
105:![Form Validation Success](form-validated.png)
117:![Expanded Project Form](form-expanded.png)
```

The three screenshots capture the key states of the form: initial empty state, successful validation response, and the expanded project sub-form. This is the core value proposition: the documentation is *executable* — it proves the app actually works at the time the document was last verified.

---

## Patterns and Themes

Looking across all 8 experiments, a few recurring patterns emerge:

**1. Separation of concerns**: Every experiment with a UI keeps business logic in a separate backend module (classifier.py, batch.py, arena.py, app.py). The Streamlit/React/HTML layer is thin.

**2. Single source of truth**: The pydantic-jsonforms-demo's Pydantic models define validation *once* and serve both the API and the UI form. The cli-tools-pattern's pyproject.toml defines command names *once* and the toolchain handles the rest.

**3. Executable documentation**: The jsonforms-pydantic-demo uses showboat to make documentation verifiable. The readme-summaries-setup uses cog to make the README self-updating.

**4. Robust external integrations**: The wos-playwright script uses multiple fallback locators. The fuzzy_match module handles imperfect LLM outputs. The proxy endpoint validates/restricts URLs. Every integration that touches an external system has explicit error handling.

**5. Minimal dependencies**: The simonw-tools template avoids npm entirely. The bare-bones-site runs on pure Python + standard library for the build chain.
