"""
llm_service.py
--------------
Service layer for OpenAI API interactions.
Provides model response generation and factual claim extraction.
"""

import os
import json
import logging
from typing import Any

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    """Instantiate an OpenAI client using the key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Export it as an environment variable before starting the server."
        )
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE: float = 0.2   # low temperature → more deterministic answers
MAX_TOKENS_RESPONSE: int = 1024
MAX_TOKENS_CLAIMS: int = 512


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _chat(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = MAX_TOKENS_RESPONSE,
) -> str:
    """Send a chat completion request and return the assistant message text."""
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as exc:
        logger.error("OpenAI API error: %s", exc)
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_model_response(prompt: str) -> str:
    """Send *prompt* to the model and return its answer as plain text.

    Parameters
    ----------
    prompt : str
        The user-facing prompt to evaluate.

    Returns
    -------
    str
        The model's raw text response.

    Raises
    ------
    ValueError
        If *prompt* is empty or whitespace-only.
    RuntimeError
        If the OpenAI API call fails.
    """
    if not prompt or not prompt.strip():
        raise ValueError("'prompt' must be a non-empty string.")

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful, accurate assistant. "
                "Answer the user's question as clearly and concisely as possible. "
                "Do not add disclaimers or meta-commentary."
            ),
        },
        {
            "role": "user",
            "content": prompt.strip(),
        },
    ]

    return _chat(messages, max_tokens=MAX_TOKENS_RESPONSE)


def extract_claims(text: str) -> list[str]:
    """Extract discrete factual claims from *text*.

    The model is instructed to return a JSON array of short, self-contained
    factual claims.  Non-factual or purely opinion sentences are excluded.

    Parameters
    ----------
    text : str
        The model-generated text to analyse.

    Returns
    -------
    list[str]
        A list of factual claim strings.  Returns an empty list if none are
        found or if the model response cannot be parsed.

    Raises
    ------
    ValueError
        If *text* is empty or whitespace-only.
    RuntimeError
        If the OpenAI API call fails.
    """
    if not text or not text.strip():
        raise ValueError("'text' must be a non-empty string.")

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a precise fact-extraction assistant. "
                "Given a passage of text, identify every discrete factual claim it contains. "
                "Return ONLY a JSON array of short, self-contained strings — one claim per element. "
                "Exclude opinions, hedges, and non-factual statements. "
                "Example output: [\"The Earth orbits the Sun.\", \"Water boils at 100 °C at sea level.\"] "
                "If there are no factual claims, return an empty array: []"
            ),
        },
        {
            "role": "user",
            "content": text.strip(),
        },
    ]

    raw = _chat(messages, temperature=0.0, max_tokens=MAX_TOKENS_CLAIMS)
    return _parse_claims(raw)


# ---------------------------------------------------------------------------
# Internal parsing
# ---------------------------------------------------------------------------

def _parse_claims(raw: str) -> list[str]:
    """Parse a JSON array of claims from the model's raw output.

    Handles common cases where the model wraps the array in a markdown
    code fence (``` or ```json).
    """
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # Drop opening fence (e.g. ```json) and closing fence
        inner_lines = [
            line for line in lines[1:]
            if line.strip() != "```"
        ]
        cleaned = "\n".join(inner_lines).strip()

    try:
        parsed: Any = json.loads(cleaned)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
        logger.warning("Claim extraction returned non-list JSON: %s", parsed)
        return []
    except json.JSONDecodeError:
        logger.warning(
            "Could not parse claim extraction response as JSON. Raw: %s", raw
        )
        return []
