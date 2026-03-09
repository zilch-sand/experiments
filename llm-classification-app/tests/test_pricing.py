"""Tests for pricing module."""

import pytest
from backend.pricing import ModelPrice, load_all_prices, estimate_dataset_cost, format_cost


class TestModelPrice:
    def test_per_token_rates(self):
        price = ModelPrice(
            model_id="test",
            name="Test",
            vendor="test",
            input_per_mtok=1.0,
            output_per_mtok=2.0,
        )
        assert price.input_per_token == 1.0 / 1_000_000
        assert price.output_per_token == 2.0 / 1_000_000

    def test_estimate_cost_basic(self):
        price = ModelPrice(
            model_id="test",
            name="Test",
            vendor="test",
            input_per_mtok=1.0,  # $1/million
            output_per_mtok=2.0,  # $2/million
        )
        cost = price.estimate_cost(1_000_000, 500_000)
        assert abs(cost - 2.0) < 0.001  # $1 input + $1 output

    def test_estimate_cost_with_caching(self):
        price = ModelPrice(
            model_id="test",
            name="Test",
            vendor="test",
            input_per_mtok=1.0,
            output_per_mtok=2.0,
            input_cached_per_mtok=0.1,
        )
        # 1M tokens, 500K cached
        cost = price.estimate_cost(1_000_000, 0, cached_input_tokens=500_000)
        # Non-cached: 500K * (1/1M) = 0.5
        # Cached: 500K * (0.1/1M) = 0.05
        assert abs(cost - 0.55) < 0.001


class TestLoadPrices:
    def test_loads_prices(self):
        prices = load_all_prices()
        assert len(prices) > 0

    def test_google_models_present(self):
        prices = load_all_prices()
        google_models = [p for p in prices.values() if p.vendor == "google"]
        assert len(google_models) > 0

    def test_anthropic_models_present(self):
        prices = load_all_prices()
        anthropic_models = [p for p in prices.values() if p.vendor == "anthropic"]
        assert len(anthropic_models) > 0

    def test_price_values_reasonable(self):
        prices = load_all_prices()
        for mid, price in prices.items():
            assert price.input_per_mtok >= 0, f"{mid} has negative input price"
            assert price.output_per_mtok >= 0, f"{mid} has negative output price"


class TestEstimateDatasetCost:
    def test_basic_estimate(self):
        price = ModelPrice(
            model_id="test", name="Test", vendor="test",
            input_per_mtok=1.0, output_per_mtok=2.0,
        )
        cost = estimate_dataset_cost(price, avg_input_tokens=100, avg_output_tokens=50, num_rows=1000)
        expected = 1000 * price.estimate_cost(100, 50)
        assert abs(cost - expected) < 0.001


class TestFormatCost:
    def test_small_cost(self):
        assert "$0.0012" == format_cost(0.0012)

    def test_normal_cost(self):
        assert "$1.50" == format_cost(1.50)

    def test_zero_cost(self):
        assert "$0.0000" == format_cost(0)
