"""
claim_extractor.py
------------------
Extracts structured factual claims from a block of text.

Strategy (two-tier):
  1. Primary  — rule-based sentence splitter with heuristic filters.
               Zero external dependencies; always available.
  2. Optional — LLM-backed extraction via `llm_service.extract_claims`.
               Activated by passing `use_llm=True` to the public function.

Both paths return the same list-of-dicts schema so callers are
insulated from the extraction method.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heuristic filter constants
# ---------------------------------------------------------------------------

# Sentence-opening phrases that strongly signal personal opinion.
# Keep this list short — only clear non-factual openers.
_OPINION_PREFIXES: tuple[str, ...] = (
    "i think",
    "i believe",
    "i feel",
    "in my opinion",
    "i would say",
    "personally,",
)

# Sentences shorter than this (in words) are too vague to be a claim.
_MIN_WORDS: int = 4

# Sentences longer than this are likely multi-clause run-ons.
_MAX_WORDS: int = 100


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split *text* into individual sentences."""
    # Temporarily protect common abbreviations that contain periods.
    abbreviations = re.compile(
        r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e|U\.S|U\.K|approx|est)\.",
        re.IGNORECASE,
    )
    protected = abbreviations.sub(lambda m: m.group(0).replace(".", "<DOT>"), text)

    # Split on . ! ? followed by whitespace (capital or not).
    raw_sentences = re.split(r"(?<=[.!?])\s+", protected)

    # Restore protected dots and strip whitespace.
    return [s.replace("<DOT>", ".").strip() for s in raw_sentences if s.strip()]


def _is_factual(sentence: str) -> bool:
    """Return *True* if *sentence* looks like a factual claim.

    Applies lightweight heuristic filters; does **not** use an LLM.
    """
    lowered = sentence.lower()

    # Too short or too long to be a useful claim.
    word_count = len(sentence.split())
    if word_count < _MIN_WORDS or word_count > _MAX_WORDS:
        return False

    # Starts with a known opinion / hedging phrase.
    if any(lowered.startswith(prefix) for prefix in _OPINION_PREFIXES):
        return False

    # Pure questions are not claims.
    if sentence.rstrip().endswith("?"):
        return False

    # Obvious imperative commands are not claims.
    imperative_starters = re.compile(
        r"^(ensure|remember|note that|please|feel free|click|visit|refer to|see also)\b",
        re.IGNORECASE,
    )
    if imperative_starters.match(sentence):
        return False

    return True


def _to_claim_dict(sentence: str) -> dict[str, Any]:
    """Wrap a sentence string in the standard claim schema."""
    return {"claim_text": sentence}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_claims_from_text(
    text: str,
    *,
    use_llm: bool = False,
) -> list[dict[str, Any]]:
    """Extract factual claims from *text* and return them as structured dicts.

    Parameters
    ----------
    text : str
        The model-generated (or any) text to analyse.
    use_llm : bool, optional
        When ``True``, delegates extraction to the LLM service
        (``llm_service.extract_claims``) for higher accuracy.
        Defaults to ``False`` (rule-based, no external calls).

    Returns
    -------
    list[dict]
        Each element has the key ``"claim_text"`` (str).
        Returns an empty list if no factual claims are found.

    Raises
    ------
    ValueError
        If *text* is empty or whitespace-only.
    RuntimeError
        If ``use_llm=True`` and the LLM API call fails.
    """
    if not text or not text.strip():
        raise ValueError("'text' must be a non-empty string.")

    if use_llm:
        return _extract_via_llm(text)

    return _extract_via_rules(text)


# ---------------------------------------------------------------------------
# Extraction strategies
# ---------------------------------------------------------------------------

def _extract_via_rules(text: str) -> list[dict[str, Any]]:
    """Rule-based extraction: split into sentences, filter, wrap."""
    sentences = _split_sentences(text)
    claims = [_to_claim_dict(s) for s in sentences if _is_factual(s)]
    logger.debug("Rule-based extraction: %d / %d sentences kept.", len(claims), len(sentences))
    return claims


def _extract_via_llm(text: str) -> list[dict[str, Any]]:
    """LLM-backed extraction using ``llm_service.extract_claims``."""
    try:
        # Import here to keep this module usable without OpenAI installed.
        from app.services.llm_service import extract_claims  # noqa: PLC0415

        raw_claims: list[str] = extract_claims(text)
        claims = [_to_claim_dict(c) for c in raw_claims if c.strip()]
        logger.debug("LLM-based extraction: %d claims returned.", len(claims))
        return claims
    except ImportError as exc:
        logger.error("llm_service is not available: %s", exc)
        raise RuntimeError(
            "LLM extraction requested but 'llm_service' could not be imported. "
            "Ensure the OpenAI package is installed and OPENAI_API_KEY is set."
        ) from exc
