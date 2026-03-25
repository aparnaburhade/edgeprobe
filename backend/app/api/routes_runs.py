"""
routes_runs.py
--------------
FastAPI router for executing LLM runs against stored prompts.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db.database import SessionLocal
from app.services.llm_service import get_model_response

logger = logging.getLogger(__name__)
router = APIRouter()

MODEL_NAME = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ExecuteRequest(BaseModel):
    prompt_id: int = Field(..., gt=0, description="ID of the stored prompt to run.", examples=[1])


class ExecuteResponse(BaseModel):
    response_text: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/execute",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an LLM run against a stored prompt",
)
def execute_run(request: ExecuteRequest) -> ExecuteResponse:
    """Fetch prompt from DB → call LLM → save run → return response."""
    db = SessionLocal()
    try:
        # 1. Fetch prompt_text from prompts table
        row = db.execute(
            text("SELECT prompt_text FROM prompts WHERE id = :id"),
            {"id": request.prompt_id},
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No prompt found with id={request.prompt_id}.",
            )

        prompt_text = row[0]
        logger.info("Executing run | prompt_id=%d  model=%s", request.prompt_id, MODEL_NAME)

        # 2. Call LLM
        try:
            response_text = get_model_response(prompt_text)
        except EnvironmentError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            logger.error("LLM call failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM service error: {exc}",
            ) from exc

        # 3. Insert into model_runs
        db.execute(
            text(
                """
                INSERT INTO model_runs (prompt_id, model_name, response_text)
                VALUES (:prompt_id, :model_name, :response_text)
                """
            ),
            {
                "prompt_id": request.prompt_id,
                "model_name": MODEL_NAME,
                "response_text": response_text,
            },
        )
        db.commit()

    finally:
        db.close()

    return ExecuteResponse(response_text=response_text)
