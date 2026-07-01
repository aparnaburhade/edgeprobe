import re
import time
import logging
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

USER_AGENT = "EdgeProbe/1.0"
SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "in", "on", "for", "to",
    "and", "or", "by", "with", "as", "from", "at", "that", "this",
    "it", "was", "were", "be", "been", "being", "did", "not"
}


def tokenize(text: str):
    text = text.lower()
    words = re.findall(r"\b[a-zA-Z0-9.-]+\b", text)
    return [word for word in words if word not in STOPWORDS]


def build_search_query(claim: str) -> str:
    words = tokenize(claim)

    # Remove years like 1800s, 1970s, 2000s, 1970
    words = [w for w in words if not re.fullmatch(r"\d{3,4}s?", w)]

    # Keep useful keywords only
    important_words = [w for w in words if len(w) > 2]

    return " ".join(important_words[:8])


def get_top_k_titles(query: str, k: int = 3):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": k,
    }

    for attempt in range(3):
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )

        if response.status_code == 429:
            wait = 2 ** attempt  # 1s, 2s, 4s
            logger.warning("Wikipedia rate-limited (429). Retrying in %ds (attempt %d/3).", wait, attempt + 1)
            time.sleep(wait)
            continue

        response.raise_for_status()
        data = response.json()
        results = data.get("query", {}).get("search", [])
        return [result["title"] for result in results]

    logger.warning("Wikipedia rate-limit persisted after 3 retries. Skipping.")
    return []


def fetch_summary(title: str):
    encoded_title = quote(title)
    summary_url = f"{SUMMARY_URL}/{encoded_title}"

    response = requests.get(
        summary_url,
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if "extract" not in data:
        return None

    return {
        "title": title,
        "evidence": data.get("extract", ""),
    }


def score_candidate(original_claim: str, candidate: dict):
    title = candidate["title"]
    evidence = candidate["evidence"]

    claim_words = set(tokenize(original_claim))
    title_words = set(tokenize(title))
    evidence_words = set(tokenize(evidence))

    if not claim_words:
        return 0

    title_overlap = len(claim_words & title_words)
    evidence_overlap = len(claim_words & evidence_words)

    score = 0
    score += title_overlap * 3
    score += evidence_overlap

    return score


def get_wikipedia_evidence(query: str, k: int = 3):
    search_query = build_search_query(query)

    titles = get_top_k_titles(search_query, k)

    if not titles:
        return None

    candidates = []

    for title in titles:
        summary = fetch_summary(title)
        if summary:
            candidates.append(summary)

    if not candidates:
        return None

    scored_candidates = []

    for candidate in candidates:
        score = score_candidate(query, candidate)
        scored_candidates.append((score, candidate))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    best_score, best_candidate = scored_candidates[0]

    return {
        "title": best_candidate["title"],
        "evidence": best_candidate["evidence"],
        "retrieval_score": best_score,
        "search_query": search_query,
        "candidates": [
            {
                "title": candidate["title"],
                "score": score,
            }
            for score, candidate in scored_candidates
        ],
    }