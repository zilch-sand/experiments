from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from schema import PORTFOLIO_UI_SCHEMA, Portfolio


def flatten_nullable_anyof(schema: dict) -> dict:
    """
    Recursively flatten anyOf schemas that represent nullable types.
    JSONForms vanilla renderers don't handle anyOf well, so we convert:
      {"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}
    to:
      {"type": "string", "format": "date"}
    making the field simply optional rather than explicitly nullable.
    """
    if isinstance(schema, dict):
        if "anyOf" in schema:
            any_of = schema["anyOf"]
            # Check if it's a simple nullable pattern (one type + null)
            if len(any_of) == 2:
                non_null_schema = None
                has_null = False
                
                for item in any_of:
                    if isinstance(item, dict):
                        if item.get("type") == "null":
                            has_null = True
                        else:
                            non_null_schema = item
                
                # If we found a nullable pattern, flatten it
                if has_null and non_null_schema:
                    schema.pop("anyOf")
                    schema.update(non_null_schema)
        
        # Recursively process all nested objects
        for key, value in list(schema.items()):
            if isinstance(value, dict):
                flatten_nullable_anyof(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        flatten_nullable_anyof(item)
    
    return schema


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/validate")
async def validate_portfolio(payload: dict) -> dict:
    try:
        portfolio = Portfolio.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=jsonable_encoder(exc.errors()))
    return {"message": "Portfolio is valid", "portfolio": portfolio.model_dump()}


@app.get("/schema")
async def portfolio_schema() -> dict:
    schema = Portfolio.model_json_schema()
    return flatten_nullable_anyof(schema)


@app.get("/ui-schema")
async def portfolio_ui_schema() -> dict:
    return PORTFOLIO_UI_SCHEMA
