"""
routes.py
---------
FastAPI router for adversarial prompt generation and prompt listing.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
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


class PromptSummary(BaseModel):
    id: int
    domain: str
    category: str
    prompt_preview: str
    created_at: datetime | None = None


class PromptListResponse(BaseModel):
    prompts: list[PromptSummary]


def _preview(text: str, max_len: int = 120) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=PromptListResponse,
    summary="List stored prompts (newest first)",
)
def list_prompts(
    limit: int = Query(100, ge=1, le=500, description="Max rows to return."),
) -> PromptListResponse:
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT id, domain, category, prompt_text, created_at
                FROM prompts
                ORDER BY id DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).fetchall()
    finally:
        db.close()

    summaries = [
        PromptSummary(
            id=r[0],
            domain=r[1],
            category=r[2],
            prompt_preview=_preview(r[3] or ""),
            created_at=r[4],
        )
        for r in rows
    ]
    return PromptListResponse(prompts=summaries)


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
                row = db.execute(
                    text(
                        """
                        INSERT INTO prompts (domain, category, prompt_text, reference_context)
                        VALUES (:domain, :category, :prompt_text, :reference_context)
                        RETURNING id
                        """
                    ),
                    {
                        "domain": prompt["domain"],
                        "category": prompt["category"],
                        "prompt_text": prompt["prompt_text"],
                        "reference_context": prompt["reference_context"],
                    },
                ).fetchone()
                prompt["id"] = int(row[0])
            db.commit()
        finally:
            db.close()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return GenerateResponse(prompts=prompts)
