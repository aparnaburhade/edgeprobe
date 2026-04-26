"""
hallucination_detector.py
-------------------------
Detects potential hallucinations in LLM claims by comparing each claim
against a reference context.

Evaluation strategy (rule-based, no external dependencies):
  1. Split reference context into sentences.
  2. Score each claim with content-word sets (stopwords removed), combining
     Sørensen–Dice, per-sentence reference recall, and whole-context claim
     recall so paraphrases and longer answers are not unfairly penalised.
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
# Calibrated for Dice / recall-style scores (typically higher than raw
# overlap/max for long claims).
SUPPORT_THRESHOLD: float = 0.36

# Same bar used before running negation-asymmetry (contradiction) logic.
CONTRADICT_THRESHOLD: float = 0.36

# Below this, the claim is treated as unrelated to the reference material.
UNSUPPORTED_THRESHOLD: float = 0.09

# English stopwords removed so scores reflect content words (temperature,
# warming, IPCC) rather than glue words (the, is, approximately).
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "as", "at", "by", "for",
        "from", "in", "into", "of", "on", "to", "with", "about", "against",
        "between", "through", "during", "before", "after", "above", "below",
        "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should", "may",
        "might", "must", "can", "this", "that", "these", "those", "it", "its",
        "they", "them", "their", "there", "here", "which", "who", "whom",
        "what", "when", "where", "why", "how", "all", "each", "every", "both",
        "few", "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just", "also",
        "any", "up", "out", "off", "over", "again", "further", "then", "once",
    }
)

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


def _content_tokens(text: str) -> set[str]:
    """Alphanumeric tokens minus common stopwords."""
    return set(_tokenise(text)) - _STOPWORDS


def _pair_grounding_score(claim: str, reference_sentence: str) -> float:
    """How well *claim* is grounded in one reference sentence.

    Combines Sørensen–Dice (symmetric, fair for uneven lengths) with
    reference recall (claim covers the sentence's content words). Either
    signal can carry a correct paraphrase that adds extra words to the claim.
    """
    c = _content_tokens(claim)
    s = _content_tokens(reference_sentence)
    if not c or not s:
        c = set(_tokenise(claim))
        s = set(_tokenise(reference_sentence))
    if not c or not s:
        return 0.0
    inter = len(c & s)
    dice = 2.0 * inter / (len(c) + len(s))
    ref_recall = inter / len(s)
    return round(max(dice, ref_recall), 4)


def _document_grounding_score(claim: str, full_reference: str) -> float:
    """Share of the claim's content vocabulary that appears anywhere in *full_reference*.

    Helps when the model blends ideas from several sentences or paraphrases
    the whole blurb: no single sentence may reach a high pair score, but the
    claim still uses only on-topic words from the reference.
    """
    c = _content_tokens(claim)
    r = _content_tokens(full_reference)
    if not c or not r:
        c = set(_tokenise(claim))
        r = set(_tokenise(full_reference))
    if not c or not r:
        return 0.0
    inter = len(c & r)
    claim_recall = inter / len(c)
    dice_doc = 2.0 * inter / (len(c) + len(r))
    return round(max(claim_recall, dice_doc), 4)


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
    claim: str,
    reference_sentences: list[str],
    full_reference: str,
) -> tuple[str, float]:
    """Return the best-matching reference sentence and a combined grounding score."""
    best_sentence = ""
    best_sentence_score = 0.0
    for sentence in reference_sentences:
        score = _pair_grounding_score(claim, sentence)
        if score > best_sentence_score:
            best_sentence_score = score
            best_sentence = sentence

    doc_score = _document_grounding_score(claim, full_reference)
    combined = max(best_sentence_score, doc_score)
    return best_sentence, round(combined, 4)


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
    full_reference: str,
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

    evidence_text, score = _find_best_evidence(
        claim_text, reference_sentences, full_reference
    )
    verdict, confidence = _assign_verdict(claim_text, evidence_text, score)

    return {
        "claim_text": claim_text,
        "verdict": verdict,
        "evidence_text": evidence_text,
        "confidence": confidence,
        "judge_reason": "some explanation"
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
        evaluated = _evaluate_single_claim(claim, reference_sentences, reference_context)
        logger.debug(
            "claim=%r  verdict=%s  confidence=%.2f",
            evaluated["claim_text"][:60],
            evaluated["verdict"],
            evaluated["confidence"],
        )
        results.append(evaluated)

    return results
