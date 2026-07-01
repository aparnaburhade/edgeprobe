"""
routes_runs.py
--------------
FastAPI router for executing LLM runs against stored prompts.
"""

import logging
import uuid 
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


class DirectExecuteRequest(BaseModel):
    prompt_text: str = Field(..., min_length=1, description="The question or prompt to evaluate.", examples=["What caused the 2008 financial crisis?"])
    api_key: str | None = Field(None, description="OpenAI API key. Used for this request only — never stored.")


class ExecuteResponse(BaseModel):
    prompt_text: str
    response_text: str
    claims: list[dict]
    score: dict


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/execute-direct",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question directly — no prompt ID needed",
)
def execute_run_direct(request: DirectExecuteRequest) -> ExecuteResponse:
    """Accept a free-form question, get the LLM response, and run full hallucination analysis."""
    prompt_text = request.prompt_text.strip()
    if not prompt_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="prompt_text must not be empty.",
        )

    try:
        user_api_key = request.api_key or None
        response_text = get_model_response(prompt_text, api_key=user_api_key)
        claims = extract_claims_from_text(response_text, use_llm=True, api_key=user_api_key)
        evaluated_claims = evaluate_claims(claims, "", api_key=user_api_key)
        score = compute_score(evaluated_claims)

        return ExecuteResponse(
            prompt_text=prompt_text,
            response_text=response_text,
            claims=evaluated_claims,
            score=score,
        )

    except Exception as exc:
        logger.exception("Direct execute failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc


@router.post(
    "/execute",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an LLM run against a stored prompt",
)
# def execute_run(request: ExecuteRequest) -> ExecuteResponse:
#     """Fetch prompt from DB → call LLM → save run → return response."""
#     db = SessionLocal()
#     try:
#         # 1. Fetch prompt_text and reference_context from prompts table
#         row = db.execute(
#             text("SELECT prompt_text, reference_context FROM prompts WHERE id = :id"),
#             {"id": request.prompt_id},
#         ).fetchone()

#         if row is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"No prompt found with id={request.prompt_id}.",
#             )

#         prompt_text, reference_context = row
#         logger.info("Executing run | prompt_id=%d  model=%s", request.prompt_id, MODEL_NAME)
#         request_id = str(uuid.uuid4())


#         run_row = db.execute(
#             text("""
#                 INSERT INTO model_runs (
#                     request_id,
#                     prompt_id,
#                     model_name,
#                     response_text,
#                     status
#                 )
#                 VALUES (
#                     :request_id,
#                     :prompt_id,
#                     :model_name,
#                     :response_text,
#                     :status
#                 )
#                 RETURNING id
#             """),
#             {
#                 "request_id": request_id,
#                 "prompt_id": request.prompt_id,
#                 "model_name": MODEL_NAME,
#                 "response_text": "",   # placeholder
#                 "status": "started",
#             }
#         ).fetchone()

#         run_id = run_row[0]

#         # 2. Call LLM
#         try:
#             response_text = get_model_response(prompt_text)

#             db.execute(
#                 text("""
#                     UPDATE model_runs
#                     SET response_text = :response_text
#                     WHERE id = :run_id
#                 """),
#                 {
#                     "response_text": response_text,
#                     "run_id": run_id,
#                 }
#             )
#             raise Exception("test failure")

#         # except EnvironmentError as exc:
#         #     raise HTTPException(
#         #         status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#         #         detail=str(exc),
#         #     ) from exc
#         # except RuntimeError as exc:
#         #     logger.error("LLM call failed: %s", exc)
#         #     raise HTTPException(
#         #         status_code=status.HTTP_502_BAD_GATEWAY,
#         #         detail=f"LLM service error: {exc}",
#         #     ) from exc
        
#         except RuntimeError as exc:
#             logger.error("LLM call failed: %s", exc)
#             raise HTTPException(...)

#         except Exception as exc:
#             db.execute(
#                 text("""
#                     UPDATE model_runs
#                     SET status = :status,
#                         error_message = :error_message,
#                         completed_at = CURRENT_TIMESTAMP
#                     WHERE id = :run_id
#                 """),
#                 {
#                     "status": "failed",
#                     "error_message": str(exc),
#                     "run_id": run_id,
#                 }
#             )
#             db.commit()
#             raise

#         # 3. Extract factual claims from the response
#         claims = extract_claims_from_text(response_text)

#         # 4. Evaluate claims against reference_context
#         evaluated_claims = evaluate_claims(claims, reference_context)

#         # 5. Compute overall score from evaluated claims
#         score = compute_score(evaluated_claims)

#         # 4. Insert into model_runs and get the run_id
#         # run_row = db.execute(
#         #     text(
#         #         """
#         #         INSERT INTO model_runs (request_id, prompt_id, model_name, response_text, status)
#         #         VALUES (:request_id, :prompt_id, :model_name, :response_text, :status)
#         #         RETURNING id
#         #         """
#         #     ),
#         #     {
#         #         "request_id": str(uuid.uuid4()),
#         #         "prompt_id": request.prompt_id,
#         #         "model_name": MODEL_NAME,
#         #         "response_text": response_text,
#         #         "status": "started",
#         #     },
#         # ).fetchone()
#         # run_id = run_row[0]

#         # 5. Insert each claim into the claims table
#         for claim in claims:
#             db.execute(
#                 text(
#                     """
#                     INSERT INTO claims (run_id, claim_text)
#                     VALUES (:run_id, :claim_text)
#                     """
#                 ),
#                 {
#                     "run_id": run_id,
#                     "claim_text": claim["claim_text"],
#                 },
#             )

#         # 6. Update claims with evaluation results (verdict, evidence, confidence)
#         for evaluated_claim in evaluated_claims:
#             db.execute(
#                 text(
#                     """
#                     UPDATE claims
#                     SET verdict = :verdict, evidence_text = :evidence_text, confidence = :confidence
#                     WHERE run_id = :run_id AND claim_text = :claim_text
#                     """
#                 ),
#                 {
#                     "run_id": run_id,
#                     "claim_text": evaluated_claim["claim_text"],
#                     "verdict": evaluated_claim["verdict"],
#                     "evidence_text": evaluated_claim["evidence_text"],
#                     "confidence": evaluated_claim["confidence"],
#                 },
#             )

#         db.execute(
#                 text("""
#                     UPDATE model_runs
#                     SET status = :status,
#                         completed_at = CURRENT_TIMESTAMP
#                     WHERE id = :run_id
#                 """),
#                 {
#                     "status": "completed",
#                     "run_id": run_id,
#                 }
#             )
#         db.commit()

#     finally:
#         db.close()

#     return ExecuteResponse(
#         prompt_text=prompt_text,
#         response_text=response_text,
#         claims=evaluated_claims,
#         score=score,
#     )


def execute_run(request: ExecuteRequest) -> ExecuteResponse:
    db = SessionLocal()
    run_id = None
    try:
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
        request_id = str(uuid.uuid4())

        run_row = db.execute(
            text("""
                INSERT INTO model_runs (
                    request_id,
                    prompt_id,
                    model_name,
                    response_text,
                    status
                )
                VALUES (
                    :request_id,
                    :prompt_id,
                    :model_name,
                    :response_text,
                    :status
                )
                RETURNING id
            """),
            {
                "request_id": request_id,
                "prompt_id": request.prompt_id,
                "model_name": MODEL_NAME,
                "response_text": "",
                "status": "started",
            },
        ).fetchone()

        run_id = run_row[0]

        response_text = get_model_response(prompt_text)

        db.execute(
            text("""
                UPDATE model_runs
                SET response_text = :response_text
                WHERE id = :run_id
            """),
            {
                "response_text": response_text,
                "run_id": run_id,
            },
        )

        claims = extract_claims_from_text(response_text, use_llm=True)
        evaluated_claims = evaluate_claims(claims, reference_context)
        score = compute_score(evaluated_claims)

        for claim in claims:
            db.execute(
                text("""
                    INSERT INTO claims (run_id, claim_text)
                    VALUES (:run_id, :claim_text)
                """),
                {
                    "run_id": run_id,
                    "claim_text": claim["claim_text"],
                },
            )

        for evaluated_claim in evaluated_claims:
            db.execute(
                text("""
                    UPDATE claims
                    SET verdict = :verdict,
                        evidence_text = :evidence_text,
                        confidence = :confidence
                    WHERE run_id = :run_id AND claim_text = :claim_text
                """),
                {
                    "run_id": run_id,
                    "claim_text": evaluated_claim["claim_text"],
                    "verdict": evaluated_claim["verdict"],
                    "evidence_text": evaluated_claim["evidence_text"],
                    "confidence": evaluated_claim["confidence"],
                },
            )

        db.execute(
            text("""
                UPDATE model_runs
                SET status = :status,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = :run_id
            """),
            {
                "status": "completed",
                "run_id": run_id,
            },
        )

        db.commit()

        return ExecuteResponse(
            prompt_text=prompt_text,
            response_text=response_text,
            claims=evaluated_claims,
            score=score,
        )

    except HTTPException:
        raise

    except Exception as exc:
        if run_id is not None:
            db.execute(
                text("""
                    UPDATE model_runs
                    SET status = :status,
                        error_message = :error_message,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = :run_id
                """),
                {
                    "status": "failed",
                    "error_message": str(exc),
                    "run_id": run_id,
                },
            )
            db.commit()
        raise

    finally:
        db.close()