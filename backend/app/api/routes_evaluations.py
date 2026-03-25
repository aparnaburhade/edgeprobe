"""
routes_evaluations.py
---------------------
FastAPI router for end-to-end hallucination evaluation of an LLM run.

Pipeline
~~~~~~~~
  POST /run  { run_id: int }
      │
      ├─ 1. Fetch run record from stub store
      │       → { prompt_text, reference_context, response_text }
      │
      ├─ 2. Extract factual claims from response_text
      │       → List[{ claim_text }]
      │
      ├─ 3. Evaluate each claim against reference_context
      │       → List[{ claim_text, verdict, evidence_text, confidence }]
      │
      ├─ 4. Compute hallucination score
      │       → { hallucination_score, risk_level, failure_type, summary }
      │
      └─ 5. Return { claims, evaluation }
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.claim_extractor import extract_claims_from_text
from app.services.hallucination_detector import evaluate_claims
from app.services.scoring_service import compute_score

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Stubbed run store
# ---------------------------------------------------------------------------
# Each record contains the model's response alongside the ground-truth
# reference context used to verify claims.
# Replace `_get_run_from_db` with a real repository call when ready.

_RUN_STORE: dict[int, dict[str, str]] = {
    1: {
        "prompt_text": "Is diabetes reversible through diet alone?",
        "response_text": (
            "Type 2 diabetes can be put into remission through significant dietary changes. "
            "Weight loss is a key factor in managing blood sugar levels. "
            "Some studies show that a low-calorie diet can normalise blood glucose. "
            "However, Type 1 diabetes is not reversible as it is an autoimmune condition. "
            "Regular exercise also plays a critical role alongside diet."
        ),
        "reference_context": (
            "Type 2 diabetes remission is achievable in some patients through diet and weight loss. "
            "Type 1 diabetes is an autoimmune disease and cannot be reversed by diet. "
            "Low-calorie diets have been shown in clinical trials to normalise blood glucose in Type 2 patients. "
            "Exercise improves insulin sensitivity but does not cure diabetes."
        ),
    },
    2: {
        "prompt_text": "What are the main trade-offs between REST and GraphQL?",
        "response_text": (
            "REST APIs use fixed endpoints and return predefined data structures. "
            "GraphQL allows clients to request exactly the data they need. "
            "REST is universally supported and easier to cache. "
            "GraphQL was invented by Facebook in 2012 and open-sourced in 2015. "
            "GraphQL eliminates over-fetching and under-fetching of data. "
            "REST does not support real-time subscriptions natively."
        ),
        "reference_context": (
            "REST APIs expose fixed endpoints and return full resource representations. "
            "GraphQL was developed internally at Facebook in 2012 and released publicly in 2015. "
            "GraphQL enables clients to specify precise data requirements, reducing over-fetching. "
            "HTTP caching is straightforward with REST but more complex with GraphQL. "
            "GraphQL supports real-time data via subscriptions."
        ),
    },
    3: {
        "prompt_text": "What are second-order effects of electric vehicle adoption?",
        "response_text": (
            "Widespread EV adoption will significantly reduce urban air pollution. "
            "Electricity grids will face increased peak demand. "
            "Oil-dependent economies may experience severe economic disruption. "
            "Lithium mining for batteries has been proven to have zero environmental impact. "
            "Public charging infrastructure investment will create new jobs."
        ),
        "reference_context": (
            "Electric vehicles reduce tailpipe emissions and improve urban air quality. "
            "Increased EV adoption places higher demand on electricity grids. "
            "Countries reliant on oil exports face economic risks from declining demand. "
            "Lithium and cobalt mining for batteries raises environmental and ethical concerns. "
            "Expansion of charging networks is expected to generate employment in new sectors."
        ),
    },
}


def _get_run_from_db(run_id: int) -> dict[str, str] | None:
    """Return the run record for *run_id*, or ``None`` if not found.

    Stub — replace with an ORM / SQL query against a runs table.
    """
    return _RUN_STORE.get(run_id)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class EvaluationRequest(BaseModel):
    run_id: int = Field(
        ...,
        gt=0,
        description="ID of the completed LLM run to evaluate.",
        examples=[1],
    )


class EvaluationResponse(BaseModel):
    run_id: int
    prompt_text: str
    claims: list[dict[str, Any]]
    evaluation: dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/run",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run end-to-end hallucination evaluation for an LLM run",
    description=(
        "Fetches the stored run, extracts factual claims from the model response, "
        "evaluates each claim against the reference context, computes a hallucination "
        "score, and returns the full evaluation results."
    ),
)
def run_evaluation(request: EvaluationRequest) -> EvaluationResponse:
    """Execute the claim extraction → detection → scoring pipeline."""

    # 1. Fetch run record
    run = _get_run_from_db(request.run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No run found with id={request.run_id}.",
        )

    prompt_text = run["prompt_text"]
    response_text = run["response_text"]
    reference_context = run["reference_context"]

    logger.info("Starting evaluation pipeline for run_id=%d", request.run_id)

    # 2. Extract claims
    try:
        raw_claims = extract_claims_from_text(response_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Claim extraction failed: {exc}",
        ) from exc

    if not raw_claims:
        logger.warning("run_id=%d — no claims extracted from response.", request.run_id)

    # 3. Evaluate claims against reference context
    try:
        evaluated_claims = evaluate_claims(raw_claims, reference_context)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Hallucination detection failed: {exc}",
        ) from exc

    # 4. Compute score
    score_result = compute_score(evaluated_claims)

    logger.info(
        "Evaluation complete | run_id=%d  score=%d  risk=%s  failure=%s",
        request.run_id,
        score_result["hallucination_score"],
        score_result["risk_level"],
        score_result["failure_type"],
    )

    # 5. Return
    return EvaluationResponse(
        run_id=request.run_id,
        prompt_text=prompt_text,
        claims=evaluated_claims,
        evaluation=score_result,
    )
