"""Web search-backed evidence retrieval using Serper API.

Drop-in replacement for wikipedia_service.get_wikipedia_evidence().
Returns the same dict structure so hallucination_detector.py needs
only a one-line import change.

Requires SERPER_API_KEY in .env.
Get a free key (2,500 queries) at https://serper.dev
"""

import logging
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/search"
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "in", "on", "for", "to",
    "and", "or", "by", "with", "as", "from", "at", "that", "this",
    "it", "was", "were", "be", "been", "being", "did", "not"
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"\b[a-zA-Z0-9.-]+\b", text)
    return [w for w in words if w not in STOPWORDS]


def build_search_query(claim: str) -> str:
    """Convert a claim into a tight keyword search query."""
    words = _tokenize(claim)
    words = [w for w in words if not re.fullmatch(r"\d{3,4}s?", w)]
    important = [w for w in words if len(w) > 2]
    return " ".join(important[:8])


def _score_candidate(claim: str, title: str, snippet: str) -> int:
    """Score a search result by word overlap with the claim."""
    claim_words = set(_tokenize(claim))
    if not claim_words:
        return 0
    title_words = set(_tokenize(title))
    snippet_words = set(_tokenize(snippet))
    return len(claim_words & title_words) * 3 + len(claim_words & snippet_words)


def _build_evidence_text(results: list[dict]) -> str:
    """Combine title + snippet into a readable evidence block."""
    parts = []
    for r in results:
        title = r.get("title", "").strip()
        snippet = r.get("snippet", "").strip()
        if title or snippet:
            parts.append(f"{title}: {snippet}" if title else snippet)
    return "\n\n".join(parts)


def _call_serper(query: str, k: int) -> dict:
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": k}
    response = requests.post(SERPER_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def get_web_evidence(query: str, k: int = 3) -> dict | None:
    """Retrieve and rank web evidence for a claim.

    Returns a dict with the same keys as wikipedia_service.get_wikipedia_evidence()
    plus `source_url` and `source` fields.

    Returns None if no results found or API key missing.
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not set — web search unavailable")
        return None

    search_query = build_search_query(query)

    try:
        data = _call_serper(search_query, k)
    except Exception as exc:
        logger.error("Serper API call failed: %s", exc)
        return None

    organic = data.get("organic", [])
    answer_box = data.get("answerBox", {})
    knowledge_graph = data.get("knowledgeGraph", {})

    if not organic and not answer_box and not knowledge_graph:
        return None

    # --- Build candidates from organic results ---
    candidates = []
    for result in organic[:k]:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        score = _score_candidate(query, title, snippet)
        candidates.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "score": score,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    # --- Build combined evidence text ---
    # Priority: answerBox > knowledgeGraph > top organic snippets
    evidence_parts = []

    if answer_box:
        box_text = answer_box.get("answer") or answer_box.get("snippet", "")
        box_title = answer_box.get("title", "Answer")
        if box_text:
            evidence_parts.append(f"{box_title}: {box_text}")

    if knowledge_graph:
        kg_desc = knowledge_graph.get("description", "")
        kg_title = knowledge_graph.get("title", "")
        if kg_desc:
            evidence_parts.append(f"{kg_title}: {kg_desc}" if kg_title else kg_desc)

    for c in candidates[:2]:
        evidence_parts.append(f"{c['title']}: {c['snippet']}")

    evidence_text = "\n\n".join(p for p in evidence_parts if p.strip())

    if not evidence_text:
        return None

    best = candidates[0] if candidates else {}

    return {
        "title": best.get("title", search_query),
        "evidence": evidence_text,
        "retrieval_score": best.get("score", 0),
        "search_query": search_query,
        "source": "web",
        "source_url": best.get("link", ""),
        "candidates": [
            {"title": c["title"], "score": c["score"], "link": c["link"]}
            for c in candidates
        ],
    }
