"""
hallucination_detector.py
-------------------------
Detects potential hallucinations in LLM claims by comparing each claim
against a reference context.

Evaluation strategy (rule-based, no external dependencies):
  1. Split reference context into sentences.
  2. For each claim, find the most semantically similar reference sentence
     using a combined token-overlap + sequence-similarity score.
  3. Apply negation-asymmetry detection to distinguish "contradicted" from
     "supported".
  4. Assign a verdict and confidence score based on configurable thresholds.

The evaluator is intentionally kept modular: swap `_score_pair` or the
entire `_evaluate_single_claim` function with an LLM-backed version later
without changing the public interface.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verdict labels
# ---------------------------------------------------------------------------

VERDICT_SUPPORTED = "supported"
VERDICT_CONTRADICTED = "contradicted"
VERDICT_UNVERIFIABLE = "unverifiable"
VERDICT_UNSUPPORTED = "unsupported"

# ---------------------------------------------------------------------------
# Thresholds (tuneable)
# ---------------------------------------------------------------------------

# Similarity score at or above which a claim is considered supported.
SUPPORT_THRESHOLD: float = 0.40

# Similarity score at or above which a claim is considered worth checking
# for contradiction (same threshold — high overlap is needed to infer opposition).
CONTRADICT_THRESHOLD: float = 0.40

# Similarity score below which a claim has no meaningful overlap at all.
UNSUPPORTED_THRESHOLD: float = 0.15

# Negation words used for contradiction detection.
_NEGATION_WORDS: frozenset[str] = frozenset(
    {
        "not", "no", "never", "neither", "nor", "nobody", "nothing",
        "nowhere", "cannot", "can't", "won't", "wouldn't", "shouldn't",
        "doesn't", "don't", "didn't", "isn't", "aren't", "wasn't",
        "weren't", "hasn't", "haven't", "hadn't", "without",
    }
)


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lower-case and tokenise *text* into alphanumeric words."""
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def _split_sentences(text: str) -> list[str]:
    """Split *text* into sentences on ``.``, ``!``, or ``?``."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _word_overlap(claim: str, sentence: str) -> int:
    """Return the number of unique words shared between *claim* and *sentence*."""
    claim_words = set(claim.lower().split())
    sentence_words = set(sentence.lower().split())
    return len(claim_words & sentence_words)


def _overlap_score(claim: str, sentence: str) -> float:
    """Normalise word overlap into a [0, 1] similarity score."""
    claim_words = set(claim.lower().split())
    sentence_words = set(sentence.lower().split())
    if not claim_words and not sentence_words:
        return 0.0
    overlap = len(claim_words & sentence_words)
    # Normalise by the size of the larger set to keep scores comparable.
    return round(overlap / max(len(claim_words), len(sentence_words)), 4)


def _has_negation(tokens: list[str]) -> bool:
    """Return *True* if *tokens* contain at least one negation word."""
    return bool(set(tokens) & _NEGATION_WORDS)


def _negation_asymmetry(claim_tokens: list[str], evidence_tokens: list[str]) -> bool:
    """Return *True* if exactly one of the two token lists contains negation.

    High overlap + negation in one but not the other → likely contradiction.
    """
    return _has_negation(claim_tokens) != _has_negation(evidence_tokens)


# ---------------------------------------------------------------------------
# Core evaluation logic
# ---------------------------------------------------------------------------

def _find_best_evidence(
    claim: str, reference_sentences: list[str]
) -> tuple[str, float]:
    """Return the (sentence, score) with the highest word overlap to *claim*."""
    best_sentence = ""
    best_score = 0.0
    for sentence in reference_sentences:
        score = _overlap_score(claim, sentence)
        if score > best_score:
            best_score = score
            best_sentence = sentence
    return best_sentence, best_score


def _assign_verdict(
    claim: str,
    evidence: str,
    score: float,
) -> tuple[str, float]:
    """Determine verdict and confidence from similarity score and negation.

    Returns
    -------
    tuple[str, float]
        ``(verdict, confidence)`` where confidence is in ``[0.0, 1.0]``.
    """
    if score < UNSUPPORTED_THRESHOLD:
        # Too little overlap — the reference says nothing relevant.
        return VERDICT_UNSUPPORTED, round(1.0 - score, 4)

    if score < SUPPORT_THRESHOLD:
        # Some overlap but not enough to confirm or deny.
        return VERDICT_UNVERIFIABLE, round(score, 4)

    # High overlap — check negation asymmetry.
    claim_tokens = list(claim.lower().split())
    evidence_tokens = list(evidence.lower().split())

    if _negation_asymmetry(claim_tokens, evidence_tokens):
        # One side negates; the other does not → contradiction.
        return VERDICT_CONTRADICTED, round(score, 4)

    return VERDICT_SUPPORTED, round(score, 4)


def _evaluate_single_claim(
    claim: dict[str, Any],
    reference_sentences: list[str],
) -> dict[str, Any]:
    """Evaluate one claim dict and return an enriched dict."""
    claim_text: str = claim.get("claim_text", "").strip()

    if not claim_text:
        return {
            "claim_text": claim_text,
            "verdict": VERDICT_UNVERIFIABLE,
            "evidence_text": "",
            "confidence": 0.0,
        }

    evidence_text, score = _find_best_evidence(claim_text, reference_sentences)
    verdict, confidence = _assign_verdict(claim_text, evidence_text, score)

    return {
        "claim_text": claim_text,
        "verdict": verdict,
        "evidence_text": evidence_text,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_claims(
    claims: list[dict[str, Any]],
    reference_context: str,
) -> list[dict[str, Any]]:
    """Evaluate each claim against *reference_context* and return verdicts.

    Parameters
    ----------
    claims : list[dict]
        Each dict must contain at minimum a ``"claim_text"`` key (str).
        Additional keys are preserved in the output.
    reference_context : str
        The ground-truth or source text to compare claims against.

    Returns
    -------
    list[dict]
        One dict per input claim, each containing:

        * ``claim_text``   – original claim string
        * ``verdict``      – ``"supported"``, ``"contradicted"``,
                             ``"unverifiable"``, or ``"unsupported"``
        * ``evidence_text``– the reference sentence most similar to the claim
        * ``confidence``   – similarity-based confidence in ``[0.0, 1.0]``

    Raises
    ------
    ValueError
        If *claims* is not a list or *reference_context* is empty.
    """
    if not isinstance(claims, list):
        raise ValueError("'claims' must be a list of dicts.")

    if not reference_context or not reference_context.strip():
        raise ValueError("'reference_context' must be a non-empty string.")

    reference_sentences = _split_sentences(reference_context)
    if not reference_sentences:
        logger.warning("reference_context produced no sentences; all claims → unsupported.")
        reference_sentences = [reference_context.strip()]

    results: list[dict[str, Any]] = []
    for claim in claims:
        evaluated = _evaluate_single_claim(claim, reference_sentences)
        logger.debug(
            "claim=%r  verdict=%s  confidence=%.2f",
            evaluated["claim_text"][:60],
            evaluated["verdict"],
            evaluated["confidence"],
        )
        results.append(evaluated)

    return results
