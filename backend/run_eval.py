import json
from app.services.wikipedia_service import get_wikipedia_evidence
from app.services.verifier import verify_claim

def run_evaluation():
    with open("eval_cases.json", "r") as file:
        cases = json.load(file)

    correct = 0
    total = len(cases)


    for case in cases:
        claim = case["claim"]
        query = case["query"]
        expected = case["expected"]

        print("\n==================================")
        print("CLAIM:", claim)
        print("EXPECTED:", expected)

        evidence_result = get_wikipedia_evidence(query)

        if not evidence_result:
            predicted = "unverifiable"
            print("No evidence found")
        else:
            print("WIKIPEDIA TITLE:", evidence_result["title"])

            verifier_result = verify_claim(
                claim=claim,
                evidence=evidence_result["evidence"]
            )

            predicted = verifier_result["verdict"]
            print("PREDICTED:", predicted)
            print("CONFIDENCE:", verifier_result.get("confidence"))
            print("REASON:", verifier_result.get("reason"))
                  
        if predicted == expected:
            correct += 1
            print("RESULT: CORRECT")
        else:
            print("RESULT: WRONG")

    accuracy = correct / total

    print("\n==============================")
    print(f"TOTAL CASES: {total}")
    print(f"CORRECT: {correct}")
    print(f"ACCURACY: {accuracy:.2%}")


if __name__ == "__main__":
    run_evaluation()