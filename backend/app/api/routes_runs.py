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
from app.services.claim_extractor import extract_claims_from_text
from app.services.hallucination_detector import evaluate_claims
from app.services.scoring_service import compute_score

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
    claims: list[dict]
    score: dict


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
        # 1. Fetch prompt_text and reference_context from prompts table
        row = db.execute(
            text("SELECT prompt_text, reference_context FROM prompts WHERE id = :id"),
            {"id": request.prompt_id},
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No prompt found with id={request.prompt_id}.",
            )

        prompt_text, reference_context = row
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

        # 3. Extract factual claims from the response
        claims = extract_claims_from_text(response_text)

        # 4. Evaluate claims against reference_context
        evaluated_claims = evaluate_claims(claims, reference_context)

        # 5. Compute overall score from evaluated claims
        score = compute_score(evaluated_claims)

        # 4. Insert into model_runs and get the run_id
        run_row = db.execute(
            text(
                """
                INSERT INTO model_runs (prompt_id, model_name, response_text)
                VALUES (:prompt_id, :model_name, :response_text)
                RETURNING id
                """
            ),
            {
                "prompt_id": request.prompt_id,
                "model_name": MODEL_NAME,
                "response_text": response_text,
            },
        ).fetchone()
        run_id = run_row[0]

        # 5. Insert each claim into the claims table
        for claim in claims:
            db.execute(
                text(
                    """
                    INSERT INTO claims (run_id, claim_text)
                    VALUES (:run_id, :claim_text)
                    """
                ),
                {
                    "run_id": run_id,
                    "claim_text": claim["claim_text"],
                },
            )

        # 6. Update claims with evaluation results (verdict, evidence, confidence)
        for evaluated_claim in evaluated_claims:
            db.execute(
                text(
                    """
                    UPDATE claims
                    SET verdict = :verdict, evidence_text = :evidence_text, confidence = :confidence
                    WHERE run_id = :run_id AND claim_text = :claim_text
                    """
                ),
                {
                    "run_id": run_id,
                    "claim_text": evaluated_claim["claim_text"],
                    "verdict": evaluated_claim["verdict"],
                    "evidence_text": evaluated_claim["evidence_text"],
                    "confidence": evaluated_claim["confidence"],
                },
            )
        db.commit()

    finally:
        db.close()

    return ExecuteResponse(response_text=response_text, claims=evaluated_claims, score=score)
