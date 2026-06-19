"""Wikipedia-backed hallucination detector.

This module replaces the previous rule-based detector. It retrieves evidence
from Wikipedia for each claim and then classifies the claim via the verifier
service.

The public signature of `evaluate_claims` is kept for compatibility with
existing route handlers.
"""

import logging
from typing import Any

from app.services.verifier import verify_claim
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


def _evaluate_single_claim(claim: dict[str, Any]) -> dict[str, Any]:
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
        evidence_result = get_wikipedia_evidence(claim_text)
        if not evidence_result:
            return {
                "claim_text": claim_text,
                "verdict": "unverifiable",
                "evidence_text": "",
                "confidence": 0.0,
                "judge_reason": "No Wikipedia evidence found.",
                "source_title": "",
            }

        evidence_text = evidence_result.get("evidence", "")
        verifier_result = verify_claim(claim=claim_text, evidence=evidence_text)

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
            "retrieval_score": evidence_result.get("retrieval_score", 0),
            "candidates": evidence_result.get("candidates", []),
        }
    except Exception as exc:
        logger.exception("Wikipedia-backed verification failed for claim: %s", claim_text)
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
) -> list[dict[str, Any]]:
    """Evaluate claims via Wikipedia retrieval + verifier.

    `reference_context` is kept only for backward compatibility and is unused.
    """
    _ = reference_context

    if not isinstance(claims, list):
        raise ValueError("'claims' must be a list of dicts.")

    results: list[dict[str, Any]] = []
    for claim in claims:
        evaluated = _evaluate_single_claim(claim)
        logger.debug(
            "claim=%r verdict=%s confidence=%.2f",
            evaluated["claim_text"][:60],
            evaluated["verdict"],
            evaluated["confidence"],
        )
        results.append(evaluated)

    return results
