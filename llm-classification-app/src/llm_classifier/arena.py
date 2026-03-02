"""
Arena: multi-model comparison with judge evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import ModelConfig, estimate_cost
from .vertex_client import call_model
from .config import THINKING_BUDGETS


@dataclass
class ContestantConfig:
    model_config: ModelConfig
    thinking_level: int = 0   # 0-3
    label: str = ""           # display label, defaults to model display_name


@dataclass
class ArenaConfig:
    contestants: list[ContestantConfig]
    judge_model: ModelConfig
    judge_prompt: str
    categories: list[str]
    multi_label: bool = False


_DEFAULT_JUDGE_PROMPT = """You are an independent evaluator. Below are responses from different AI assistants to the same classification task. 
Evaluate which response best follows the instructions (correct format, plausible reasoning, appropriate label).
Do NOT look up the correct answer. Just evaluate response quality and instruction-following.

Task prompt: {task_prompt}

Responses:
{responses}

Respond with just the label of the best response (e.g. "Model A") and a one-sentence reason."""


def run_arena_row(config: ArenaConfig, prompt: str, row_index: int) -> dict:
    """
    Run all contestants on a single prompt.

    Returns:
        {contestant_label: {"response": str, "matched_label": str, "input_tokens": int,
                            "output_tokens": int, "cost": float}}
    """
    from .classification import fuzzy_match_label

    results: dict[str, Any] = {}
    for c in config.contestants:
        label = c.label or c.model_config.display_name
        thinking_budget = THINKING_BUDGETS.get(c.thinking_level, None)
        try:
            resp = call_model(
                model_config=c.model_config,
                prompt=prompt,
                system_prompt=(
                    "You are an expert data classifier. "
                    "Respond with only the category label(s) — no explanation."
                ),
                thinking_level=thinking_budget,
                max_tokens=c.model_config.max_tokens_default,
            )
            raw = resp["text"].strip()
            matched = fuzzy_match_label(raw, config.categories, config.multi_label)
            cost = estimate_cost(
                c.model_config.id,
                resp["input_tokens"],
                resp["output_tokens"],
            )
            results[label] = {
                "response": raw,
                "matched_label": matched if isinstance(matched, str) else "|".join(matched),
                "input_tokens": resp["input_tokens"],
                "output_tokens": resp["output_tokens"],
                "cost": cost,
            }
        except Exception as exc:
            results[label] = {
                "response": f"ERROR: {exc}",
                "matched_label": "ERROR",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
            }
    return results


def judge_responses(
    config: ArenaConfig,
    prompt: str,
    responses: dict,
    row_data: dict,
) -> str:
    """
    Ask the judge model to evaluate contestant responses.

    Returns the judge's verdict string.
    """
    response_lines = "\n\n".join(
        f"{label}: {info['response']}" for label, info in responses.items()
    )

    judge_prompt_text = config.judge_prompt.replace("{task_prompt}", prompt).replace(
        "{responses}", response_lines
    )

    try:
        result = call_model(
            model_config=config.judge_model,
            prompt=judge_prompt_text,
            system_prompt="You are an impartial evaluator of AI classification quality.",
            thinking_level=None,
            max_tokens=512,
        )
        return result["text"].strip()
    except Exception as exc:
        return f"Judge error: {exc}"


DEFAULT_JUDGE_PROMPT = _DEFAULT_JUDGE_PROMPT
