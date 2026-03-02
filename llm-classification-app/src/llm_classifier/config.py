"""
App configuration loaded from environment variables.
"""
import os
from pathlib import Path

# GCP settings
GCP_PROJECT = os.environ.get("GCP_PROJECT", "")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

# GCS / BQ defaults
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")
BQ_DATASET = os.environ.get("BQ_DATASET", "")

# Demo mode: if True, use mock responses instead of real API calls
DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() in ("1", "true", "yes")

# Path to llm-prices data directory
LLM_PRICES_DATA_DIR = Path(__file__).parent.parent.parent / "llm-prices" / "data"

# Batch jobs persistence file
BATCH_JOBS_FILE = Path(os.environ.get("BATCH_JOBS_FILE", "batch_jobs.json"))

# Fuzzy match threshold (0-100)
FUZZY_THRESHOLD = int(os.environ.get("FUZZY_THRESHOLD", "70"))

# Thinking budget tokens by level
THINKING_BUDGETS = {
    0: None,    # off
    1: 1024,    # low
    2: 8192,    # medium
    3: 32768,   # high
}
