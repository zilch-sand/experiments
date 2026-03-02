"""Batch processing with Vertex AI and batch ID persistence."""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import litellm
import pandas as pd

from backend.models import ModelConfig
from backend.prompt import PromptTemplate
from backend.fuzzy_match import fuzzy_match_label, fuzzy_match_multi_label


BATCH_STATE_DIR = Path(__file__).parent.parent / "batch_state"


def _ensure_batch_dir():
    BATCH_STATE_DIR.mkdir(parents=True, exist_ok=True)


def save_batch_id(batch_id: str, metadata: dict | None = None):
    """Persist a batch ID to file for recovery."""
    _ensure_batch_dir()
    record = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(),
        "status": "submitted",
        **(metadata or {}),
    }
    filepath = BATCH_STATE_DIR / f"{batch_id}.json"
    filepath.write_text(json.dumps(record, indent=2))


def update_batch_status(batch_id: str, status: str, extra: dict | None = None):
    """Update the status of a tracked batch."""
    filepath = BATCH_STATE_DIR / f"{batch_id}.json"
    if filepath.exists():
        record = json.loads(filepath.read_text())
    else:
        record = {"batch_id": batch_id}
    record["status"] = status
    record["updated_at"] = datetime.now().isoformat()
    if extra:
        record.update(extra)
    filepath.write_text(json.dumps(record, indent=2))


def load_tracked_batches() -> list[dict]:
    """Load all tracked batch records."""
    _ensure_batch_dir()
    batches = []
    for f in BATCH_STATE_DIR.glob("*.json"):
        try:
            batches.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(batches, key=lambda b: b.get("created_at", ""), reverse=True)


def cleanup_batch(batch_id: str):
    """Remove batch tracking file after completion."""
    filepath = BATCH_STATE_DIR / f"{batch_id}.json"
    if filepath.exists():
        filepath.unlink()


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
    try:
        batch = litellm.retrieve_batch(batch_id=batch_id)
        status = batch.status
        update_batch_status(batch_id, status)
        return {
            "batch_id": batch_id,
            "status": status,
            "completed": batch.request_counts.completed if batch.request_counts else 0,
            "total": batch.request_counts.total if batch.request_counts else 0,
            "failed": batch.request_counts.failed if batch.request_counts else 0,
        }
    except Exception as e:
        return {"batch_id": batch_id, "status": "error", "error": str(e)}


def retrieve_batch_results(
    batch_id: str,
    categories: list[str],
    multi_label: bool = False,
    delimiter: str = "|",
) -> list[dict]:
    """Retrieve and parse results from a completed batch."""
    try:
        results = litellm.retrieve_batch(batch_id=batch_id)
        if results.status != "completed":
            return []

        output_file_id = results.output_file_id
        content = litellm.file_content(file_id=output_file_id)

        parsed = []
        for line in content.text.strip().split("\n"):
            record = json.loads(line)
            custom_id = record.get("custom_id", "")
            row_idx = int(custom_id.split("-")[1]) if "-" in custom_id else 0

            response_body = record.get("response", {}).get("body", {})
            choices = response_body.get("choices", [])
            raw = choices[0]["message"]["content"].strip() if choices else ""

            usage = response_body.get("usage", {})

            if multi_label:
                matched = fuzzy_match_multi_label(raw, categories, delimiter)
            else:
                matched = fuzzy_match_label(raw, categories) or raw

            parsed.append({
                "row_index": row_idx,
                "raw_response": raw,
                "matched_label": matched,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            })

        # Cleanup after successful retrieval
        update_batch_status(batch_id, "completed_and_retrieved")

        return sorted(parsed, key=lambda x: x["row_index"])

    except Exception as e:
        return [{"error": str(e)}]
