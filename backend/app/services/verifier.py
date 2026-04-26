from dotenv import load_dotenv
import json
from openai import OpenAI

load_dotenv()
client = OpenAI()


def verify_claim(claim: str, evidence: str):
    if not evidence or len(evidence.strip()) == 0:
        return {
            "verdict": "unverifiable",
            "confidence": 0.0,
            "reason": "No evidence provided"
        }

    prompt = f"""
You are a strict fact-checking system.

Your job is to compare a claim against given evidence.

Rules:
- Only use the provided evidence.
- Do NOT use outside knowledge.
- If evidence clearly confirms the claim → supported
- If evidence clearly disproves the claim → contradicted
- If evidence is insufficient or unclear → unverifiable


Also assign a confidence score between 0 and 1:
- 0.9–1.0 → very strong evidence
- 0.7–0.9 → good evidence
- 0.4–0.7 → weak/partial evidence
- 0.0–0.4 → very weak or unclear

Claim:
{claim}

Evidence:
{evidence}

Respond ONLY in valid JSON:

{{
    "verdict": "supported | contradicted | unverifiable",
    "confidence": number,
    "reason": "short explanation"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,  # IMPORTANT: makes output consistent
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    # --- Safe JSON parsing ---
    try:
        return json.loads(content)
    except:
        return {
            "verdict": "error",
            "confidence": 0.0,
            "reason": f"Invalid JSON response: {content}"
        }