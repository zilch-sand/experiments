"""Model configuration and Vertex AI integration via litellm."""

import os
from dataclasses import dataclass, field
from backend.pricing import get_vertex_models, ModelPrice


@dataclass
class ModelConfig:
    """Configuration for a model run."""
    vertex_id: str
    display_name: str
    vendor: str
    price: ModelPrice | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    thinking_level: str | None = None  # "low", "medium", "high" for supported models
    extra_params: dict = field(default_factory=dict)

    def to_litellm_kwargs(self) -> dict:
        """Convert to kwargs for litellm.completion()."""
        kwargs = {
            "model": self.vertex_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        # Thinking / reasoning for models that support it.
        # "auto" = adaptive thinking (model chooses budget; Claude 4.5+ and Gemini 2.5+)
        # "low/medium/high" = extended thinking with explicit token budget
        if self.thinking_level:
            if "gemini" in self.vertex_id.lower():
                if self.thinking_level == "auto":
                    # Adaptive: let the model decide the budget
                    kwargs["thinking"] = {"type": "enabled"}
                else:
                    budget_map = {"low": 1024, "medium": 8192, "high": 32768}
                    kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": budget_map.get(self.thinking_level, 8192),
                    }
            elif "claude" in self.vertex_id.lower():
                if self.thinking_level == "auto":
                    # Adaptive thinking (Claude 4.5+): model manages its own budget
                    kwargs["thinking"] = {"type": "enabled"}
                else:
                    budget_map = {"low": 2048, "medium": 10000, "high": 32000}
                    kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": budget_map.get(self.thinking_level, 10000),
                    }
                # Claude on Vertex AI: use the region from VERTEX_REGION if set
                region = os.environ.get("VERTEX_REGION")
                if region:
                    kwargs["vertex_ai_location"] = region
        elif "claude" in self.vertex_id.lower():
            # Always pass region for Claude models, even when thinking is off
            region = os.environ.get("VERTEX_REGION")
            if region:
                kwargs["vertex_ai_location"] = region
        kwargs.update(self.extra_params)
        return kwargs


# Thinking level options per vendor.
# "auto" = adaptive thinking (model decides budget; Claude 4.5+ / Gemini 2.5+)
# "low/medium/high" = extended thinking with explicit token budgets
THINKING_LEVELS = {
    "Google": ["none", "auto", "low", "medium", "high"],
    "Anthropic": ["none", "auto", "low", "medium", "high"],
    "Meta": [],  # Llama doesn't support thinking
}


def get_available_models() -> list[dict]:
    """Get all available models with their configurations."""
    return get_vertex_models()


def get_model_display_options() -> list[str]:
    """Get display-friendly model names for UI selection."""
    models = get_available_models()
    return [f"{m['name']} ({m['vendor']})" for m in models]


def get_model_by_display_name(display_name: str) -> dict | None:
    """Find a model by its display name."""
    models = get_available_models()
    for m in models:
        if f"{m['name']} ({m['vendor']})" == display_name:
            return m
    return None


def create_model_config(
    model_info: dict,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    thinking_level: str | None = None,
) -> ModelConfig:
    """Create a ModelConfig from model info dict."""
    return ModelConfig(
        vertex_id="vertex_ai/" + model_info["vertex_id"],
        display_name=model_info["name"],
        vendor=model_info["vendor"],
        price=model_info.get("price"),
        temperature=temperature,
        max_tokens=max_tokens,
        thinking_level=thinking_level if thinking_level != "none" else None,
    )
