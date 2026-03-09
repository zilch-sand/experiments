"""Tests for batch state persistence."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.batch import (
    save_batch_id,
    update_batch_status,
    load_tracked_batches,
    cleanup_batch,
    prepare_batch_requests,
    BATCH_STATE_DIR,
)
from backend.models import ModelConfig
from backend.pricing import ModelPrice
from backend.prompt import PromptTemplate

import pandas as pd


@pytest.fixture
def temp_batch_dir(tmp_path):
    """Use a temporary directory for batch state."""
    with patch("backend.batch.BATCH_STATE_DIR", tmp_path):
        yield tmp_path


class TestBatchPersistence:
    def test_save_and_load(self, temp_batch_dir):
        save_batch_id("test-batch-123", {"model": "test-model"})
        batches = load_tracked_batches()
        assert len(batches) == 1
        assert batches[0]["batch_id"] == "test-batch-123"
        assert batches[0]["status"] == "submitted"

    def test_update_status(self, temp_batch_dir):
        save_batch_id("test-batch-456")
        update_batch_status("test-batch-456", "completed")
        batches = load_tracked_batches()
        assert batches[0]["status"] == "completed"

    def test_cleanup(self, temp_batch_dir):
        save_batch_id("test-batch-789")
        cleanup_batch("test-batch-789")
        batches = load_tracked_batches()
        assert len(batches) == 0

    def test_multiple_batches(self, temp_batch_dir):
        save_batch_id("batch-1")
        save_batch_id("batch-2")
        save_batch_id("batch-3")
        batches = load_tracked_batches()
        assert len(batches) == 3


class TestPrepareRequests:
    def test_prepare_basic(self):
        df = pd.DataFrame({"text": ["Hello", "World"]})
        config = ModelConfig(
            model_id="gemini-2.0-flash",
            display_name="Gemini 2.0 Flash",
            vendor="Google",
        )
        template = PromptTemplate("Classify: {text}. Categories: {label_options}")
        requests = prepare_batch_requests(
            df, config, template, ["A", "B"], False, "|"
        )
        assert len(requests) == 2
        assert requests[0]["custom_id"] == "row-0"
        assert requests[1]["custom_id"] == "row-1"
        assert "Hello" in requests[0]["body"]["messages"][0]["content"]
