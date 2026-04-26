from dotenv import load_dotenv

load_dotenv()

from app.services.wikipedia_service import get_wikipedia_evidence
from app.services.verifier import verify_claim


claims = [
    "The capital of Australia is Sydney",
    "Canberra is the capital of Australia",
    "The Amazon rainforest is the largest tropical rainforest in the world.",
]


for claim in claims:
    print("\n==============================")
    print("CLAIM:", claim)

    wiki_data = get_wikipedia_evidence(claim)

    if wiki_data is None:
        print("No Wikipedia evidence found.")
        continue

    print("WIKIPEDIA TITLE:", wiki_data["title"])
    print("EVIDENCE:", wiki_data["evidence"][:500])

    result = verify_claim(claim, wiki_data["evidence"])

    print("VERIFIER RESULT:")
    print(result)