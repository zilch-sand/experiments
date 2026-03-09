"""Prompt template handling with {col} placeholders and {label_options}."""

import re
from dataclasses import dataclass, field


DEFAULT_CLASSIFICATION_PROMPT = """
You are a precise document classifier.  Classify the document below into \
exactly ONE of the provided categories.

## Categories
{label_options}

## Document
{text}

## Instructions
- Return the single best-matching category from the list above.
- Use the category name EXACTLY as listed — do not paraphrase or abbreviate.
- Return ONLY the category. No markdown fences, no commentary.
"""

DEFAULT_MULTI_LABEL_PROMPT = """
You are a precise document classifier.  For the document below, assign \
ALL categories that apply from the provided list.

## Categories
{label_options}

## Document
{text}

## Instructions
- For the document, return ALL categories that are relevant, separated by '|'.
- A document may match one, or several.
- Only include categories with meaningful relevance — do not force matches.
- Use the category name EXACTLY as listed — do not paraphrase or abbreviate.
- If no categories apply, return "Other". Do not return "Other" AND other categories.
- Return your answer as valid JSON matching this schema:
{{"categories": [{{"category": "<name>"}}, ...]}}
- Return ONLY the JSON object.  No markdown fences, no commentary.
"""


@dataclass
class PromptTemplate:
    template: str
    columns_used: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.columns_used = self.extract_columns()

    def extract_columns(self) -> list[str]:
        """Extract column placeholders from template, excluding label_options."""
        placeholders = re.findall(r"\{(\w+)\}", self.template)
        return [p for p in placeholders if p != "label_options"]

    def validate(self, available_columns: list[str]) -> list[str]:
        """Validate template against available columns. Returns list of errors."""
        errors = []
        for col in self.columns_used:
            if col not in available_columns:
                errors.append(f"Column '{col}' not found in dataset")
        if "{label_options}" not in self.template:
            errors.append("Template should include {label_options} placeholder")
        return errors

    def check_warnings(self, available_columns: list[str]) -> list[str]:
        """Check for warnings (non-fatal issues)."""
        warnings = []
        if "label_options" in available_columns:
            warnings.append(
                "⚠️ 'label_options' is both a column name and a special placeholder. "
                "The placeholder {label_options} will be replaced with categories, "
                "not the column value."
            )
        return warnings

    def render(
        self, row: dict, categories: list[str], multi_label: bool = False,
        delimiter: str = "|",
    ) -> str:
        """Render the prompt for a specific row."""
        label_str = "\n".join(categories)
        values = {"label_options": label_str}
        for col in self.columns_used:
            values[col] = str(row.get(col, f"[missing:{col}]"))
        try:
            return self.template.format(**values)
        except KeyError as e:
            return f"Error rendering prompt: missing key {e}"

    def preview(
        self, first_row: dict, categories: list[str], multi_label: bool = False,
        delimiter: str = "|",
    ) -> str:
        """Preview the prompt using the first row of data."""
        return self.render(first_row, categories, multi_label, delimiter)


FEEDBACK_PROMPT = """You are an expert in prompt engineering and text classification. 
Please review the following classification prompt and categories, then provide feedback.

PROMPT TEMPLATE:
{prompt}

CATEGORIES:
{categories}

CLASSIFICATION TYPE: {classification_type}

Please evaluate and provide feedback on:
1. **Clarity**: Is the prompt clear and unambiguous?
2. **Category Overlap**: Are any categories overlapping or ambiguous?
3. **Missing Categories**: Is an "Other" or catch-all category needed?
4. **Prompt Quality**: Any suggestions to improve classification accuracy?
5. **Category Count**: Are there too many or too few categories?
6. **RAG Recommendation**: If the prompt and categories are very long (combined >2000 tokens), recommend using RAG-based classification instead.

Provide specific, actionable suggestions."""
