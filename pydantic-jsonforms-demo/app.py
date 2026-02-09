from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator, model_validator


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


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/validate")
async def validate_portfolio(payload: dict) -> dict:
    try:
        portfolio = Portfolio.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    return {"message": "Portfolio is valid", "portfolio": portfolio.model_dump()}


@app.get("/schema")
async def portfolio_schema() -> dict:
    return Portfolio.model_json_schema()
