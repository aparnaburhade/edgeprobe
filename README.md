# EdgeProbe

EdgeProbe is a claim-level hallucination detection system for evaluating LLM responses.

Instead of treating an AI response as a single block of text, EdgeProbe breaks it down into individual claims and verifies each claim against external evidence.

---

## Why I built this

While building AI-powered applications, I noticed that most systems focus on generation, but not enough on evaluation.

**How do we know if an LLM response is actually reliable?**

EdgeProbe explores this by treating LLM outputs as something to be *tested*, not just consumed.

---

## Key Idea
LLM Output → Claims → Evidence Retrieval → Verification → Risk Score


This pipeline allows fine-grained inspection of where hallucinations occur.

---

## Features

- **Adversarial Prompt Generation**  
  Creates edge-case prompts such as ambiguity, misleading context, near-fact scenarios, and multi-hop reasoning

- **Claim Extraction**  
  Breaks LLM responses into atomic factual claims

- **Wikipedia-based Evidence Retrieval**  
  - Retrieves top-k relevant Wikipedia pages  
  - Ranks them using lexical overlap between:
    - claim/query  
    - page title  
    - summary evidence  
  - Selects the most relevant source instead of blindly using the first search result  

- **Claim Verification**  
  - Uses an LLM to classify each claim as:
    - `supported`  
    - `contradicted`  
    - `unverifiable`  
  - Uses **temperature = 0** for consistent and deterministic outputs  

- **Risk Scoring**  
  Aggregates claim-level verdicts into an overall hallucination risk score  

- **Frontend Dashboard**  
  Allows users to inspect:
  - original prompt  
  - AI-generated response  
  - extracted claims  
  - retrieved evidence  
  - verification results  

---

## Recent Improvements

### Retrieval Fix (Key Improvement)

**Previously:**
- Used only the top-1 Wikipedia search result  
- This often returned incorrect or loosely related pages  

**Now:**
- Retrieve top-k results (k = 3)  
- Score each candidate using:
  - word overlap with query/claim  
  - title importance weighting  
- Select the best-matching page  

**Impact:**
- More accurate evidence retrieval  
- Reduced false positives in verification  

---

## How it works

1. A prompt is generated and stored  
2. The prompt is sent to an LLM  
3. The response is stored  
4. The response is decomposed into claims  
5. Each claim is converted into search queries  
6. Evidence is retrieved from Wikipedia  
7. Claims are verified against evidence  
8. A risk score is computed  

---

## Tech Stack

### Backend
- FastAPI  
- Python  
- PostgreSQL  
- SQLAlchemy  
- OpenAI API  

### Frontend
- React  
- Vite  

---

## Example

**Claim:**  
The capital of Australia is Sydney  

**Retrieved Evidence:**  
Canberra is the capital city of Australia  

**Verdict:**  
Contradicted  

---

## Future Improvements

- Confidence scoring for verification  
- Multi-source retrieval beyond Wikipedia  
- Better query decomposition  
- Evaluation metrics for retrieval quality  
- Caching and performance optimization  

---

## Why this project matters

EdgeProbe focuses on a critical problem in AI systems:

> Not just generating answers — but verifying them.

It reflects real-world challenges in building reliable AI systems, especially in domains where correctness matters.