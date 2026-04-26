from dotenv import load_dotenv

load_dotenv()

import json
from app.services.llm_service import get_model_response

def decompose_claim_for_wikipedia(claim_text: str):
    """
    Converts a claim into atomic claims + wikipedia search queries.
    """

    prompt = f"""

You are helping verify factual claims using Wikipedia.

Break the claim below into 1 to 3 atomic factual claims. 
For each atomic claim, create a short Wikipedia search query.

Rules:
- Keep each atomic claim simple.
- Do not add new facts.
- If the claim is already simple, return only one item.
- Return only raw JSON.
- Do not include markdown.
- Do not include ```json.
- Do not include explanation.

Claim:
{claim_text}

Output format:
[
    {{
        "claim_text": "simple factual claim",
        "search_query": "short wikipedia search query"
    }}
]
"""
    
    decomposition_response = get_model_response(prompt)
    print("RAW DECOMPOSITION RESPONSE:", decomposition_response)

    try:
        cleaned_response = decomposition_response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace("```", "").strip()

        parsed = json.loads(cleaned_response)
        return parsed

    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return [
            {
                "claim_text": claim_text,
                "search_query": claim_text
            }
        ]