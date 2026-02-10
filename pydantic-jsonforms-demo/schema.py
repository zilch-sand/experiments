from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator, model_validator
from datetime import date
from typing import Literal

# Data schema---------------------------------

class PortfolioMeta(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    owner_email: EmailStr
    created_on: date = Field(default_factory=date.today)
    visibility: Literal["private", "team", "public"] = "private"


class ProjectMeta(BaseModel):
    name: str = Field(..., min_length=3, max_length=60)
    status: Literal["planned", "active", "paused", "completed"]
    start_date: date
    end_date: date | None = None
    budget_usd: float = Field(..., ge=0, le=5_000_000)
    repo_url: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("tags")
    @classmethod
    def tags_unique_and_clean(cls, tags: list[str]) -> list[str]:
        cleaned = [tag.strip().lower() for tag in tags if tag.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("tags must be unique after normalization")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectMeta":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.status == "completed" and not self.end_date:
            raise ValueError("completed projects must include end_date")
        return self


class Project(BaseModel):
    meta: ProjectMeta
    summary: str = Field(..., min_length=10, max_length=400)
    contributors: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("contributors")
    @classmethod
    def contributors_non_empty(cls, contributors: list[str]) -> list[str]:
        cleaned = [name.strip() for name in contributors if name.strip()]
        if len(cleaned) < len(contributors):
            raise ValueError("contributors must not contain empty names")
        return cleaned


class Portfolio(BaseModel):
    meta: PortfolioMeta
    projects: list[Project] = Field(..., min_length=1, max_length=6)



# Visual schema---------------------------------

PORTFOLIO_UI_SCHEMA: dict = {
    "type": "VerticalLayout",
    "elements": [
        {
            "type": "Group",
            "label": "Portfolio",
            "elements": [
                {"type": "Control", "scope": "#/properties/meta/properties/title"},
                {"type": "Control", "scope": "#/properties/meta/properties/owner_email"},
                {"type": "Control", "scope": "#/properties/meta/properties/created_on"},
                {"type": "Control", "scope": "#/properties/meta/properties/visibility"},
            ],
        },
        {
            "type": "Group",
            "label": "Projects",
            "elements": [
                {
                    "type": "Control",
                    "scope": "#/properties/projects",
                    "options": {
                        "detail": {
                            "type": "VerticalLayout",
                            "elements": [
                                {
                                    "type": "Group",
                                    "label": "Project Meta",
                                    "elements": [
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/name",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/status",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/start_date",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/end_date",
                                            "rule": {
                                                "effect": "SHOW",
                                                "condition": {
                                                    "scope": "#/properties/meta/properties/status",
                                                    "schema": {"const": "completed"},
                                                },
                                            },
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/budget_usd",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/repo_url",
                                        },
                                        {
                                            "type": "Control",
                                            "scope": "#/properties/meta/properties/tags",
                                        },
                                    ],
                                },
                                {"type": "Control", "scope": "#/properties/summary"},
                                {"type": "Control", "scope": "#/properties/contributors"},
                            ],
                        }
                    },
                }
            ],
        },
    ],
}

