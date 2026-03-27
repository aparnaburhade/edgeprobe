# EdgeProbe

EdgeProbe is an AI evaluation tool that analyzes LLM-generated responses at a claim level to detect possible hallucinations.

Instead of treating an AI response as one block of text, EdgeProbe:
- sends a stored prompt to an LLM
- extracts individual claims from the response
- compares those claims against reference context
- labels them as supported, unsupported, contradicted, or unverifiable
- computes an overall risk score

## Why I built this

While building AI-powered applications, I became curious about a different problem:

**How do we know if AI-generated responses are actually reliable?**

EdgeProbe was built to explore the evaluation side of AI systems, not just generation. The goal is to make AI outputs easier to inspect, question, and trust.

## Features

- **Adversarial prompt generation**
  - Generates edge-case prompts across categories like:
    - ambiguity
    - misleading context
    - near-fact
    - insufficient information
    - multi-hop reasoning

- **LLM response execution**
  - Sends stored prompts to an LLM and captures the generated response

- **Claim extraction**
  - Breaks a response into smaller factual or logical claims

- **Hallucination detection**
  - Compares claims against reference context
  - Assigns verdicts:
    - `supported`
    - `unsupported`
    - `contradicted`
    - `unverifiable`

- **Risk scoring**
  - Aggregates claim-level verdicts into an overall response risk score

- **Frontend dashboard**
  - Lets users enter a prompt ID and inspect:
    - the original prompt
    - the AI-generated response
    - extracted claims
    - verdicts, evidence, and confidence
    - overall score

## How it works

1. A prompt is generated and stored in the database
2. The prompt is sent to the LLM
3. The response is stored
4. The response is split into claims
5. Each claim is checked against trusted reference context
6. Verdicts and confidence are assigned
7. A final score is computed and displayed

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

### Database
- PostgreSQL
- pgAdmin (for local database inspection)

## Project Structure

```text
edgeprobe/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   └── services/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   └── package.json
└── README.md