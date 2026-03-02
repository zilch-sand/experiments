"""
Prompt template building and validation utilities.
"""
from __future__ import annotations

import re


_PLACEHOLDER_RE = re.compile(r"\{([^}]+)\}")


def get_prompt_columns(template: str) -> list[str]:
    """Extract all {col} references from a template string."""
    return [m.group(1) for m in _PLACEHOLDER_RE.finditer(template)]


def validate_prompt(template: str, columns: list[str]) -> list[str]:
    """
    Validate a prompt template against available CSV columns.
    Returns a list of warning strings (empty = no issues).
    """
    warnings: list[str] = []
    referenced = get_prompt_columns(template)

    # label_options is a reserved placeholder – warn if it collides with a column
    if "label_options" in columns:
        warnings.append(
            "Column 'label_options' shadows the reserved {label_options} placeholder. "
            "Consider renaming the column."
        )

    # Warn about referenced placeholders that are neither columns nor label_options
    for col in referenced:
        if col == "label_options":
            continue
        if col not in columns:
            warnings.append(f"Placeholder {{{col}}} not found in CSV columns.")

    if not referenced:
        warnings.append("Prompt template has no {column} placeholders.")

    if "{label_options}" not in template:
        warnings.append(
            "Prompt does not contain {label_options} – the model won't see the category list."
        )

    return warnings


def build_prompt(
    template: str,
    row: dict,
    categories: list[str],
    multi_label: bool,
) -> str:
    """
    Build a prompt by substituting {col_name} placeholders and {label_options}.

    For multi_label=True, appends a note about using '|' as delimiter.
    """
    if multi_label:
        label_options_str = (
            "Pick one or more of the following categories (separate multiple with '|'):\n"
            + "\n".join(f"- {c}" for c in categories)
        )
    else:
        label_options_str = (
            "Pick exactly one of the following categories:\n"
            + "\n".join(f"- {c}" for c in categories)
        )

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key == "label_options":
            return label_options_str
        return str(row.get(key, f"{{{key}}}"))

    return _PLACEHOLDER_RE.sub(_replace, template)
