
# import requests

# def get_wikipedia_evidence(query: str):
#     search_url = "https://en.wikipedia.org/w/api.php"
#     params = {
#         "action": "query",
#         "list": "search",
#         "srsearch": query,
#         "format": "json"
#     }

#     response = requests.get(
#         search_url,
#         params=params,
#         headers={"User-Agent": "EdgeProbe/1.0"}
#     )

#     data = response.json()

#     if not data["query"]["search"]:
#         return None

#     title = data["query"]["search"][0]["title"]

#     # # Now fetch summary
#     # summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
#     # summary_res = requests.get(summary_url).json()

#     from urllib.parse import quote

#     encoded_title = quote(title)
#     summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

#     summary_response = requests.get(
#         summary_url,
#         headers={"User-Agent": "EdgeProbe/1.0"}
#     )

#     print("SUMMARY URL:", summary_url)
#     print("SUMMARY STATUS:", summary_response.status_code)
#     print("SUMMARY TEXT:", summary_response.text[:300])

#     summary_res = summary_response.json()
#     #return summary_res.get("extract", "")

#     if "extract" not in summary_res:
#         return None

#     return {
#         "title": title,
#         "evidence": summary_res.get("extract", "")
# }



import re
import requests
from urllib.parse import quote


USER_AGENT = "EdgeProbe/1.0"
SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"


STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "in", "on", "for", "to",
    "and", "or", "by", "with", "as", "from", "at", "that", "this",
    "it", "was", "were", "be", "been", "being"
}


def tokenize(text: str):
    text = text.lower()
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    return [word for word in words if word not in STOPWORDS]


def get_top_k_titles(query: str, k: int = 3):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": k
    }

    response = requests.get(
        SEARCH_URL,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    results = data.get("query", {}).get("search", [])

    return [result["title"] for result in results]


def fetch_summary(title: str):
    encoded_title = quote(title)
    summary_url = f"{SUMMARY_URL}/{encoded_title}"

    response = requests.get(
        summary_url,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if "extract" not in data:
        return None

    return {
        "title": title,
        "evidence": data.get("extract", "")
    }


def score_candidate(query: str, candidate: dict):
    title = candidate["title"]
    evidence = candidate["evidence"]

    query_words = set(tokenize(query))
    title_words = set(tokenize(title))
    evidence_words = set(tokenize(evidence))

    if not query_words:
        return 0

    title_overlap = len(query_words & title_words)
    evidence_overlap = len(query_words & evidence_words)

    score = 0
    score += title_overlap * 3
    score += evidence_overlap

    return score


def get_wikipedia_evidence(query: str, k: int = 3):
    titles = get_top_k_titles(query, k)

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
        "candidates": [
            {
                "title": candidate["title"],
                "score": score
            }
            for score, candidate in scored_candidates
        ]
    }