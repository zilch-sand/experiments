"""
Vertex AI client supporting Gemini, Claude (via AnthropicVertex), and Llama models.

In demo/offline mode (DEMO_MODE=true or missing credentials) all functions
return realistic mock responses so the app can be explored without GCP access.
"""
from __future__ import annotations

import json
import random
import time
from typing import Any

from .config import (
    GCP_PROJECT,
    GCP_LOCATION,
    DEMO_MODE,
)
from .models import ModelConfig

# ---------------------------------------------------------------------------
# One-time Vertex AI initialisation
# ---------------------------------------------------------------------------

_vertexai_initialised = False


def _ensure_vertexai_init() -> None:
    """Initialise vertexai SDK once per process."""
    global _vertexai_initialised
    if _vertexai_initialised:
        return
    import vertexai
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    _vertexai_initialised = True


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------

_DEMO_LABELS = ["Positive", "Negative", "Neutral", "Spam", "Not Spam"]


def _demo_response(categories: list[str] | None = None) -> dict:
    labels = categories or _DEMO_LABELS
    return {
        "text": random.choice(labels),
        "input_tokens": random.randint(80, 400),
        "output_tokens": random.randint(1, 10),
    }


def _extract_categories_from_prompt(prompt: str) -> list[str] | None:
    """Try to extract category names from the rendered prompt for demo mode."""
    lines = prompt.splitlines()
    cats: list[str] = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") and (in_list or len(cats) == 0):
            cats.append(stripped[2:].strip())
            in_list = True
        elif in_list and stripped and not stripped.startswith("- "):
            break
    return cats if cats else None


_DEMO_FEEDBACK = (
    "**1. Clarity** – The task is clear and unambiguous. The instruction to respond "
    "with only the category name is explicit.\n\n"
    "**2. Category overlap** – The categories appear mutually exclusive. However, "
    "consider whether a text could be both Positive and Neutral (e.g. a polite "
    "but indifferent review). Adding an 'Other' category may help.\n\n"
    "**3. Missing category** – Consider adding an 'Other' or 'Mixed' category "
    "for texts that don't clearly fit any label.\n\n"
    "**4. Length** – The prompt is concise. No RAG approach is needed.\n\n"
    "**5. Formatting** – The output format instruction is explicit ('Respond with "
    "only the category name'). This is good for reliable parsing."
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def call_model(
    model_config: ModelConfig,
    prompt: str,
    system_prompt: str = "",
    thinking_level: int | None = None,
    max_tokens: int = 8192,
) -> dict:
    """
    Call a model on Vertex AI and return {"text": str, "input_tokens": int, "output_tokens": int}.

    thinking_level: token budget for extended thinking (None = off).
    """
    if DEMO_MODE or not GCP_PROJECT:
        time.sleep(0.2)  # simulate latency
        # Detect feedback/evaluation requests by system prompt keyword
        is_feedback_request = "prompt engineer" in system_prompt.lower() or "evaluator" in system_prompt.lower()
        if is_feedback_request:
            return {
                "text": _DEMO_FEEDBACK,
                "input_tokens": random.randint(200, 600),
                "output_tokens": random.randint(80, 160),
            }
        cats = _extract_categories_from_prompt(prompt)
        return _demo_response(cats)

    provider = model_config.provider

    if provider == "google":
        return _call_gemini(model_config, prompt, system_prompt, thinking_level, max_tokens)
    elif provider == "anthropic":
        return _call_claude(model_config, prompt, system_prompt, thinking_level, max_tokens)
    elif provider == "meta":
        return _call_llama(model_config, prompt, system_prompt, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def count_tokens(model_config: ModelConfig, prompt: str) -> int:
    """Estimate token count for a prompt. Falls back to rough word-based estimate."""
    if DEMO_MODE or not GCP_PROJECT:
        # ~1.3 tokens per word as rough estimate
        return max(1, int(len(prompt.split()) * 1.3))

    if model_config.provider == "google":
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
            model = GenerativeModel(model_config.vertex_model_id)
            response = model.count_tokens(prompt)
            return response.total_tokens
        except Exception:
            pass

    # Fallback to tiktoken cl100k estimate
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(prompt))
    except Exception:
        return max(1, int(len(prompt.split()) * 1.3))


def create_batch_job(
    model_config: ModelConfig,
    prompts: list[dict],
    output_bq_table: str,
    gcs_output_uri: str,
) -> str:
    """
    Submit a batch prediction job.

    For Gemini: writes JSONL to GCS and submits BatchPredictionJob.
    For Claude: uses BigQuery input format.

    Returns the job ID/resource name.
    """
    if DEMO_MODE or not GCP_PROJECT:
        return f"demo-batch-{int(time.time())}"

    if model_config.provider == "google":
        return _create_gemini_batch(model_config, prompts, gcs_output_uri)
    elif model_config.provider == "anthropic":
        return _create_claude_batch(model_config, prompts, output_bq_table, gcs_output_uri)
    else:
        raise NotImplementedError(f"Batch jobs not supported for provider: {model_config.provider}")


def get_batch_status(model_config: ModelConfig, job_id: str) -> dict:
    """
    Return {"state": str, "completed": bool, "output_uri": str | None}.
    """
    if DEMO_MODE or not GCP_PROJECT:
        return {"state": "JOB_STATE_SUCCEEDED", "completed": True, "output_uri": None}

    if model_config.provider == "google":
        return _get_gemini_batch_status(job_id)
    elif model_config.provider == "anthropic":
        return _get_claude_batch_status(job_id)
    return {"state": "UNKNOWN", "completed": False, "output_uri": None}


def cancel_batch_job(model_config: ModelConfig, job_id: str) -> None:
    """Cancel a running batch job."""
    if DEMO_MODE or not GCP_PROJECT:
        return

    if model_config.provider == "google":
        try:
            from google.cloud import aiplatform
            aiplatform.init(project=GCP_PROJECT, location=GCP_LOCATION)
            job = aiplatform.BatchPredictionJob(job_id)
            job.cancel()
        except Exception as exc:
            raise RuntimeError(f"Failed to cancel Gemini batch job: {exc}") from exc


def get_batch_results(model_config: ModelConfig, job_id: str) -> list[dict]:
    """
    Retrieve results from a completed batch job.

    Returns a list of dicts with keys: row_index, raw_response, input_tokens, output_tokens.
    """
    if DEMO_MODE or not GCP_PROJECT:
        return [
            {"row_index": i, "raw_response": random.choice(_DEMO_LABELS),
             "input_tokens": random.randint(80, 400), "output_tokens": random.randint(1, 10)}
            for i in range(5)
        ]

    if model_config.provider == "google":
        return _get_gemini_batch_results(job_id)
    elif model_config.provider == "anthropic":
        return _get_claude_batch_results(job_id)
    return []


# ---------------------------------------------------------------------------
# Gemini implementation
# ---------------------------------------------------------------------------

def _call_gemini(
    model_config: ModelConfig,
    prompt: str,
    system_prompt: str,
    thinking_budget: int | None,
    max_tokens: int,
) -> dict:
    """Call a Gemini model via vertexai SDK."""
    from vertexai.generative_models import GenerativeModel, GenerationConfig

    _ensure_vertexai_init()

    gen_config_kwargs: dict[str, Any] = {"max_output_tokens": max_tokens}

    # Gemini 2.5 extended thinking
    if thinking_budget and model_config.supports_thinking:
        gen_config_kwargs["thinking_config"] = {"thinking_budget": thinking_budget}

    gen_config = GenerationConfig(**gen_config_kwargs)

    model = GenerativeModel(
        model_config.vertex_model_id,
        system_instruction=system_prompt or None,
    )
    response = model.generate_content(prompt, generation_config=gen_config)

    usage = response.usage_metadata
    return {
        "text": response.text,
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
    }


def _create_gemini_batch(model_config: ModelConfig, prompts: list[dict], gcs_output_uri: str) -> str:
    """
    Write prompts as JSONL to GCS and create a Gemini BatchPredictionJob.
    The input JSONL is written alongside the output URI (same GCS path prefix).
    """
    from google.cloud import aiplatform, storage
    import io

    _ensure_vertexai_init()

    gcs_input_uri = gcs_output_uri.rstrip("/") + "/input.jsonl"
    bucket_name, *path_parts = gcs_input_uri.replace("gs://", "").split("/")
    blob_name = "/".join(path_parts)

    lines = []
    for i, p in enumerate(prompts):
        lines.append(json.dumps({"request": {"contents": [{"parts": [{"text": p["prompt"]}], "role": "user"}]}}))
    jsonl_bytes = "\n".join(lines).encode()

    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(bucket_name)
    bucket.blob(blob_name).upload_from_file(io.BytesIO(jsonl_bytes), content_type="application/jsonl")

    aiplatform.init(project=GCP_PROJECT, location=GCP_LOCATION)
    job = aiplatform.BatchPredictionJob.create(
        job_display_name=f"llm-classifier-{int(time.time())}",
        model_name=model_config.vertex_model_id,
        instances_format="jsonl",
        gcs_source=gcs_input_uri,
        predictions_format="jsonl",
        gcs_destination_prefix=gcs_output_uri,
    )
    return job.resource_name


def _get_gemini_batch_status(job_id: str) -> dict:
    from google.cloud import aiplatform
    aiplatform.init(project=GCP_PROJECT, location=GCP_LOCATION)
    job = aiplatform.BatchPredictionJob(job_id)
    state = job.state.name
    completed = state in ("JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED")
    output_uri = None
    if completed and state == "JOB_STATE_SUCCEEDED":
        output_uri = job.output_info.gcs_output_directory
    return {"state": state, "completed": completed, "output_uri": output_uri}


def _get_gemini_batch_results(job_id: str) -> list[dict]:
    from google.cloud import aiplatform, storage
    aiplatform.init(project=GCP_PROJECT, location=GCP_LOCATION)
    job = aiplatform.BatchPredictionJob(job_id)
    output_uri = job.output_info.gcs_output_directory
    bucket_name, prefix = output_uri.replace("gs://", "").split("/", 1)

    client = storage.Client(project=GCP_PROJECT)
    results = []
    for blob in client.list_blobs(bucket_name, prefix=prefix):
        if blob.name.endswith(".jsonl"):
            for i, line in enumerate(blob.download_as_text().splitlines()):
                data = json.loads(line)
                text = data.get("response", {}).get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                results.append({
                    "row_index": i,
                    "raw_response": text,
                    "input_tokens": data.get("response", {}).get("usageMetadata", {}).get("promptTokenCount", 0),
                    "output_tokens": data.get("response", {}).get("usageMetadata", {}).get("candidatesTokenCount", 0),
                })
    return results


# ---------------------------------------------------------------------------
# Claude (AnthropicVertex) implementation
# ---------------------------------------------------------------------------

def _call_claude(
    model_config: ModelConfig,
    prompt: str,
    system_prompt: str,
    thinking_budget: int | None,
    max_tokens: int,
) -> dict:
    """Call Claude via AnthropicVertex."""
    from anthropic import AnthropicVertex

    client = AnthropicVertex(region=GCP_LOCATION, project_id=GCP_PROJECT)

    kwargs: dict[str, Any] = {
        "model": model_config.vertex_model_id,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    # Claude extended thinking
    if thinking_budget and model_config.supports_thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

    response = client.messages.create(**kwargs)
    text = "".join(
        block.text for block in response.content if hasattr(block, "text")
    )
    return {
        "text": text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def _create_claude_batch(
    model_config: ModelConfig,
    prompts: list[dict],
    output_bq_table: str,
    gcs_output_uri: str,
) -> str:
    """
    Create a Claude batch job via AnthropicVertex.
    Uses the Anthropic Messages Batches API proxied through Vertex AI.
    """
    from anthropic import AnthropicVertex

    client = AnthropicVertex(region=GCP_LOCATION, project_id=GCP_PROJECT)
    requests = [
        {
            "custom_id": str(p.get("row_index", i)),
            "params": {
                "model": model_config.vertex_model_id,
                "max_tokens": model_config.max_tokens_default,
                "messages": [{"role": "user", "content": p["prompt"]}],
            },
        }
        for i, p in enumerate(prompts)
    ]
    batch = client.messages.batches.create(requests=requests)
    return batch.id


def _get_claude_batch_status(job_id: str) -> dict:
    from anthropic import AnthropicVertex
    client = AnthropicVertex(region=GCP_LOCATION, project_id=GCP_PROJECT)
    batch = client.messages.batches.retrieve(job_id)
    completed = batch.processing_status == "ended"
    return {"state": batch.processing_status, "completed": completed, "output_uri": None}


def _get_claude_batch_results(job_id: str) -> list[dict]:
    from anthropic import AnthropicVertex
    client = AnthropicVertex(region=GCP_LOCATION, project_id=GCP_PROJECT)
    results = []
    for i, result in enumerate(client.messages.batches.results(job_id)):
        if result.result.type == "succeeded":
            text = "".join(
                b.text for b in result.result.message.content if hasattr(b, "text")
            )
            usage = result.result.message.usage
            results.append({
                "row_index": int(result.custom_id),
                "raw_response": text,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            })
    return results


# ---------------------------------------------------------------------------
# Llama (Model Garden, OpenAI-compatible) implementation
# ---------------------------------------------------------------------------

def _call_llama(
    model_config: ModelConfig,
    prompt: str,
    system_prompt: str,
    max_tokens: int,
) -> dict:
    """
    Call a Llama model via Vertex AI Model Garden using the OpenAI-compatible endpoint.
    Uses GCP_PROJECT as the project identifier in the endpoint URL.
    """
    import httpx

    # Vertex AI Model Garden OpenAI-compatible endpoint
    endpoint = (
        f"https://{GCP_LOCATION}-aiplatform.googleapis.com/v1beta1/projects/"
        f"{GCP_PROJECT}/locations/{GCP_LOCATION}/endpoints/openapi/chat/completions"
    )

    import google.auth
    import google.auth.transport.requests
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    token = creds.token

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_config.vertex_model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    resp = httpx.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {
        "text": text,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }
