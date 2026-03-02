"""Tests for fuzzy matching."""

import pytest
from backend.fuzzy_match import fuzzy_match_label, fuzzy_match_multi_label, find_safe_delimiter


class TestFuzzyMatchLabel:
    def test_exact_match(self):
        assert fuzzy_match_label("Sports", ["Sports", "Politics", "Tech"]) == "Sports"

    def test_case_insensitive_exact(self):
        assert fuzzy_match_label("sports", ["Sports", "Politics", "Tech"]) == "Sports"

    def test_fuzzy_match(self):
        # "Sport" should match "Sports"
        result = fuzzy_match_label("Sport", ["Sports", "Politics", "Technology"])
        assert result == "Sports"

    def test_fuzzy_match_with_typo(self):
        result = fuzzy_match_label("Politcs", ["Sports", "Politics", "Technology"])
        assert result == "Politics"

    def test_no_match_below_threshold(self):
        result = fuzzy_match_label("xyz123", ["Sports", "Politics", "Tech"], threshold=80)
        assert result is None

    def test_empty_prediction(self):
        assert fuzzy_match_label("", ["A", "B"]) is None

    def test_empty_categories(self):
        assert fuzzy_match_label("test", []) is None

    def test_whitespace_handling(self):
        assert fuzzy_match_label("  Sports  ", ["Sports", "Tech"]) == "Sports"


class TestFuzzyMatchMultiLabel:
    def test_single_label(self):
        result = fuzzy_match_multi_label("Sports", ["Sports", "Politics"])
        assert result == ["Sports"]

    def test_multi_label_pipe(self):
        result = fuzzy_match_multi_label(
            "Sports|Politics", ["Sports", "Politics", "Tech"]
        )
        assert sorted(result) == ["Politics", "Sports"]

    def test_multi_label_with_spaces(self):
        result = fuzzy_match_multi_label(
            "Sports | Politics", ["Sports", "Politics", "Tech"]
        )
        assert sorted(result) == ["Politics", "Sports"]

    def test_fuzzy_multi_label(self):
        result = fuzzy_match_multi_label(
            "Sport|Politcs", ["Sports", "Politics", "Tech"]
        )
        assert sorted(result) == ["Politics", "Sports"]

    def test_custom_delimiter(self):
        result = fuzzy_match_multi_label(
            "Sports;;Politics", ["Sports", "Politics"], delimiter=";;"
        )
        assert sorted(result) == ["Politics", "Sports"]

    def test_deduplication(self):
        result = fuzzy_match_multi_label(
            "Sports|Sports", ["Sports", "Politics"]
        )
        assert result == ["Sports"]

    def test_empty_parts_ignored(self):
        result = fuzzy_match_multi_label(
            "Sports||Politics", ["Sports", "Politics"]
        )
        assert sorted(result) == ["Politics", "Sports"]


class TestFindSafeDelimiter:
    def test_pipe_safe(self):
        assert find_safe_delimiter(["Cat A", "Cat B"]) == "|"

    def test_pipe_in_category(self):
        result = find_safe_delimiter(["Cat|A", "Cat B"])
        assert result != "|"
        assert "|" not in result or result == "||"

    def test_all_delimiters_used(self):
        categories = ["a|b", "c||d", "e;;f", "g###h", "i^^^j"]
        result = find_safe_delimiter(categories)
        assert result == "|||"
