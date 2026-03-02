"""Tests for prompt template handling."""

import pytest
from backend.prompt import PromptTemplate, DEFAULT_CLASSIFICATION_PROMPT


def test_extract_columns():
    template = PromptTemplate("Classify: {title} - {description}. Categories: {label_options}")
    assert sorted(template.columns_used) == ["description", "title"]


def test_extract_columns_excludes_label_options():
    template = PromptTemplate("{text} {label_options}")
    assert template.columns_used == ["text"]


def test_validate_missing_column():
    template = PromptTemplate("{missing_col} {label_options}")
    errors = template.validate(["text", "title"])
    assert any("missing_col" in e for e in errors)


def test_validate_missing_label_options():
    template = PromptTemplate("{text}")
    errors = template.validate(["text"])
    assert any("label_options" in e for e in errors)


def test_validate_success():
    template = PromptTemplate("{text} {label_options}")
    errors = template.validate(["text", "other"])
    assert errors == []


def test_warning_label_options_column():
    template = PromptTemplate("{text} {label_options}")
    warnings = template.check_warnings(["text", "label_options"])
    assert len(warnings) == 1
    assert "label_options" in warnings[0]


def test_no_warning_without_label_options_column():
    template = PromptTemplate("{text} {label_options}")
    warnings = template.check_warnings(["text", "title"])
    assert warnings == []


def test_render():
    template = PromptTemplate("Text: {title}. Categories: {label_options}")
    row = {"title": "Hello World", "other": "ignored"}
    result = template.render(row, ["A", "B", "C"])
    assert "Hello World" in result
    assert "A, B, C" in result


def test_render_missing_column():
    template = PromptTemplate("Text: {missing}. Categories: {label_options}")
    row = {"title": "Hello"}
    result = template.render(row, ["A"])
    assert "[missing:missing]" in result


def test_preview_uses_first_row():
    template = PromptTemplate("{name}: {label_options}")
    row = {"name": "Test Item"}
    preview = template.preview(row, ["Cat1", "Cat2"])
    assert "Test Item" in preview
    assert "Cat1, Cat2" in preview


def test_default_prompt_has_label_options():
    template = PromptTemplate(DEFAULT_CLASSIFICATION_PROMPT)
    assert "{label_options}" in DEFAULT_CLASSIFICATION_PROMPT
    # The default uses {text} column
    assert "text" in template.columns_used
