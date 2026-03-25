"""
scoring_service.py
------------------
Computes a hallucination risk score from evaluated claims.

Score model
~~~~~~~~~~~
Each verdict carries a weight that contributes to the raw penalty:

  supported     →  0   (no penalty)
  unverifiable  →  1   (mild — absence of evidence is not evidence of absence)
  unsupported   →  2   (moderate — claim has no grounding)
  contradicted  →  4   (severe — claim actively conflicts with context)

  raw_penalty  = Σ weight_i
  max_penalty  = 4 × n_claims   (worst case: every claim contradicted)
  penalty_rate = raw_penalty / max_penalty          ∈ [0, 1]

  hallucination_score = round(penalty_rate × 100)   ∈ [0, 100]

Risk thresholds
~~~~~~~~~~~~~~~
  0 – 24   → low
  25 – 59  → medium
  60 – 100 → high

Special override: *any* contradicted claim forces risk_level to at least "high".

Failure type
~~~~~~~~~~~~
Describes the dominant failure mode:
  "contradiction"          — at least one claim directly conflicts with context
  "high_unsupported"       — > 50 % of claims are unsupported
  "high_unverifiable"      — > 50 % of claims cannot be verified
  "mixed_hallucination"    — a mix of unsupported / unverifiable failures
  "none"                   — no failures detected
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VERDICT_WEIGHTS: dict[str, int] = {
    "supported": 0,
    "unverifiable": 1,
    "unsupported": 2,
    "contradicted": 4,
}

_RISK_LOW = "low"
_RISK_MEDIUM = "medium"
_RISK_HIGH = "high"

# hallucination_score thresholds (inclusive lower bound)
_THRESHOLDS: list[tuple[int, str]] = [
    (60, _RISK_HIGH),
    (25, _RISK_MEDIUM),
    (0, _RISK_LOW),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_verdicts(claims: list[dict[str, Any]]) -> dict[str, int]:
    """Return a frequency map of verdict labels across all claims."""
    counts: dict[str, int] = {v: 0 for v in _VERDICT_WEIGHTS}
    for claim in claims:
        verdict = claim.get("verdict", "unverifiable")
        if verdict in counts:
            counts[verdict] += 1
        else:
            logger.warning("Unknown verdict '%s' treated as 'unverifiable'.", verdict)
            counts["unverifiable"] += 1
    return counts


def _compute_penalty_rate(counts: dict[str, int], n_claims: int) -> float:
    """Return the normalised penalty in ``[0.0, 1.0]``."""
    if n_claims == 0:
        return 0.0
    raw = sum(_VERDICT_WEIGHTS[v] * cnt for v, cnt in counts.items())
    max_penalty = _VERDICT_WEIGHTS["contradicted"] * n_claims  # worst case
    return raw / max_penalty


def _risk_level(score: int, has_contradiction: bool) -> str:
    """Map *score* to a risk label, with contradiction override."""
    if has_contradiction:
        return _RISK_HIGH
    for threshold, level in _THRESHOLDS:
        if score >= threshold:
            return level
    return _RISK_LOW


def _failure_type(counts: dict[str, int], n_claims: int) -> str:
    """Return a human-readable failure-mode label."""
    if counts["contradicted"] > 0:
        return "contradiction"

    if n_claims == 0:
        return "none"

    unsupported_rate = counts["unsupported"] / n_claims
    unverifiable_rate = counts["unverifiable"] / n_claims

    if counts["supported"] == n_claims:
        return "none"

    if unsupported_rate > 0.50:
        return "high_unsupported"

    if unverifiable_rate > 0.50:
        return "high_unverifiable"

    if counts["unsupported"] > 0 or counts["unverifiable"] > 0:
        return "mixed_hallucination"

    return "none"


def _build_summary(
    score: int,
    risk: str,
    failure: str,
    counts: dict[str, int],
    n_claims: int,
) -> str:
    """Compose a concise human-readable summary string."""
    if n_claims == 0:
        return "No claims were provided for evaluation."

    pct_supported = round(counts["supported"] / n_claims * 100)
    parts: list[str] = [
        f"Hallucination score: {score}/100 ({risk} risk).",
        f"{pct_supported}% of claims ({counts['supported']}/{n_claims}) are supported.",
    ]

    if counts["contradicted"]:
        parts.append(
            f"{counts['contradicted']} claim(s) directly contradict the reference context."
        )
    if counts["unsupported"]:
        parts.append(
            f"{counts['unsupported']} claim(s) have no grounding in the reference context."
        )
    if counts["unverifiable"]:
        parts.append(
            f"{counts['unverifiable']} claim(s) could not be verified."
        )
    if failure == "none":
        parts.append("No hallucination signals detected.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_score(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute a hallucination risk score from a list of evaluated claims.

    Parameters
    ----------
    claims : list[dict]
        Each dict should contain at minimum a ``"verdict"`` key with one of
        ``"supported"``, ``"unsupported"``, ``"contradicted"``,
        ``"unverifiable"``.  Produced by ``hallucination_detector.evaluate_claims``.

    Returns
    -------
    dict with keys:

    * ``hallucination_score`` – int in ``[0, 100]`` (higher = more hallucinated)
    * ``risk_level``          – ``"low"``, ``"medium"``, or ``"high"``
    * ``failure_type``        – dominant failure mode string
    * ``summary``             – human-readable explanation

    Raises
    ------
    ValueError
        If *claims* is not a list.
    """
    if not isinstance(claims, list):
        raise ValueError("'claims' must be a list of dicts.")

    n_claims = len(claims)

    if n_claims == 0:
        logger.warning("compute_score called with an empty claims list.")
        return {
            "hallucination_score": 0,
            "risk_level": _RISK_LOW,
            "failure_type": "none",
            "summary": "No claims were provided for evaluation.",
        }

    counts = _count_verdicts(claims)
    penalty_rate = _compute_penalty_rate(counts, n_claims)
    score = round(penalty_rate * 100)
    has_contradiction = counts["contradicted"] > 0
    risk = _risk_level(score, has_contradiction)
    failure = _failure_type(counts, n_claims)
    summary = _build_summary(score, risk, failure, counts, n_claims)

    logger.debug(
        "Scoring complete | score=%d  risk=%s  failure=%s  counts=%s",
        score, risk, failure, counts,
    )

    return {
        "hallucination_score": score,
        "risk_level": risk,
        "failure_type": failure,
        "summary": summary,
    }
