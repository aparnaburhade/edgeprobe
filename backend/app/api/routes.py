"""
routes.py
---------
FastAPI router for adversarial prompt generation.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from typing import Any

from app.db.database import SessionLocal
from app.services.edge_case_generator import (
    generate_edge_cases,
    SUPPORTED_DOMAINS,
    SUPPORTED_CATEGORIES,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    domain: str = Field(
        ...,
        description="Target domain. One of: general, healthcare, coding.",
        examples=["healthcare"],
    )
    categories: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "One or more adversarial categories: ambiguity, misleading_context, "
            "near_fact, insufficient_info, multi_hop."
        ),
        examples=[["ambiguity", "multi_hop"]],
    )
    count: int = Field(
        ...,
        gt=0,
        le=100,
        description="Number of prompts to generate (1 – 100).",
        examples=[5],
    )

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        normalised = value.strip().lower()
        if normalised not in SUPPORTED_DOMAINS:
            raise ValueError(
                f"'{value}' is not a supported domain. "
                f"Choose from: {sorted(SUPPORTED_DOMAINS)}"
            )
        return normalised

    @field_validator("categories", mode="before")
    @classmethod
    def validate_categories(cls, values: list[str]) -> list[str]:
        normalised = [v.strip().lower() for v in values]
        invalid = [v for v in normalised if v not in SUPPORTED_CATEGORIES]
        if invalid:
            raise ValueError(
                f"Unsupported categories: {invalid}. "
                f"Choose from: {sorted(SUPPORTED_CATEGORIES)}"
            )
        return normalised


class GenerateResponse(BaseModel):
    prompts: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate adversarial edge-case prompts",
    description=(
        "Randomly samples *count* adversarial prompts from the requested "
        "domain and categories and returns them as a JSON list."
    ),
)
def generate_prompts(request: GenerateRequest) -> GenerateResponse:
    """Generate and return adversarial edge-case prompts."""
    try:
        prompts = generate_edge_cases(
            domain=request.domain,
            categories=request.categories,
            count=request.count,
        )

        db = SessionLocal()
        try:
            for prompt in prompts:
                db.execute(
                    text(
                        """
                        INSERT INTO prompts (domain, category, prompt_text, reference_context)
                        VALUES (:domain, :category, :prompt_text, :reference_context)
                        """
                    ),
                    {
                        "domain": prompt["domain"],
                        "category": prompt["category"],
                        "prompt_text": prompt["prompt_text"],
                        "reference_context": prompt["reference_context"],
                    },
                )
            db.commit()
        finally:
            db.close()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return GenerateResponse(prompts=prompts)
