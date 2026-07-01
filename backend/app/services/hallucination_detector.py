"""Web search-backed hallucination detector.

Retrieves evidence for each claim using Serper web search (primary) with
Wikipedia as a fallback. Classifies claims via the verifier service.

The public signature of `evaluate_claims` is kept for compatibility with
existing route handlers.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.services.verifier import verify_claim
from app.services.web_search_service import get_web_evidence
from app.services.wikipedia_service import get_wikipedia_evidence

logger = logging.getLogger(__name__)

_ALLOWED_VERDICTS: frozenset[str] = frozenset(
    {"supported", "contradicted", "unverifiable"}
)


def _normalise_verdict(raw_verdict: Any) -> str:
    verdict = str(raw_verdict or "").strip().lower()
    if verdict == "unsupported":
        return "contradicted"
    if verdict in _ALLOWED_VERDICTS:
        return verdict
    return "unverifiable"


def _evaluate_single_claim(claim: dict[str, Any], api_key: str | None = None) -> dict[str, Any]:
    claim_text = str(claim.get("claim_text", "")).strip()
    if not claim_text:
        return {
            "claim_text": "",
            "verdict": "unverifiable",
            "evidence_text": "",
            "confidence": 0.0,
            "judge_reason": "Empty claim text.",
            "source_title": "",
        }

    try:
        # --- Primary: web search ---
        evidence_result = get_web_evidence(claim_text)
        source = "web"

        # --- Fallback: Wikipedia ---
        if not evidence_result:
            logger.debug("Web search returned nothing for claim, falling back to Wikipedia: %s", claim_text[:60])
            evidence_result = get_wikipedia_evidence(claim_text)
            source = "wikipedia"

        if not evidence_result:
            return {
                "claim_text": claim_text,
                "verdict": "unverifiable",
                "evidence_text": "",
                "confidence": 0.0,
                "judge_reason": "No evidence found via web search or Wikipedia.",
                "source_title": "",
                "source": "none",
                "source_url": "",
            }

        evidence_text = evidence_result.get("evidence", "")
        verifier_result = verify_claim(claim=claim_text, evidence=evidence_text, api_key=api_key)

        confidence_raw = verifier_result.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "claim_text": claim_text,
            "verdict": _normalise_verdict(verifier_result.get("verdict")),
            "evidence_text": evidence_text,
            "confidence": max(0.0, min(1.0, confidence)),
            "judge_reason": str(verifier_result.get("reason", "")).strip(),
            "source_title": str(evidence_result.get("title", "")),
            "source": source,
            "source_url": str(evidence_result.get("source_url", "")),
            "retrieval_score": evidence_result.get("retrieval_score", 0),
            "candidates": evidence_result.get("candidates", []),
        }
    except (EnvironmentError, PermissionError) as exc:
        # Auth/key errors should not be swallowed — let them surface as 500s
        raise
    except Exception as exc:
        logger.exception("Verification failed for claim: %s", claim_text)
        return {
            "claim_text": claim_text,
            "verdict": "unverifiable",
            "evidence_text": "",
            "confidence": 0.0,
            "judge_reason": f"Verification failed: {exc}",
            "source_title": "",
        }


def evaluate_claims(
    claims: list[dict[str, Any]],
    reference_context: str,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Evaluate claims via Wikipedia retrieval + verifier.

    `reference_context` is kept only for backward compatibility and is unused.
    """
    _ = reference_context

    if not isinstance(claims, list):
        raise ValueError("'claims' must be a list of dicts.")

    # Run all claims in parallel — each needs a web search + LLM call,
    # so parallelising cuts total time from (n × latency) to ~1× latency.
    results: list[dict[str, Any]] = [{}] * len(claims)
    with ThreadPoolExecutor(max_workers=min(len(claims), 6)) as executor:
        future_to_index = {
            executor.submit(_evaluate_single_claim, claim, api_key): i
            for i, claim in enumerate(claims)
        }
        for future in as_completed(future_to_index):
            i = future_to_index[future]
            evaluated = future.result()
            logger.debug(
                "claim=%r verdict=%s confidence=%.2f",
                evaluated.get("claim_text", "")[:60],
                evaluated.get("verdict"),
                evaluated.get("confidence", 0.0),
            )
            results[i] = evaluated

    return results
