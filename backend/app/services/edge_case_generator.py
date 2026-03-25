"""
edge_case_generator.py
----------------------
Generates adversarial edge-case prompts for LLM evaluation.
"""

import random
from typing import Any

# ---------------------------------------------------------------------------
# Domain topics
# ---------------------------------------------------------------------------

DOMAIN_TOPICS: dict[str, list[str]] = {
    "general": [
        "climate change",
        "social media",
        "remote work",
        "electric vehicles",
        "universal basic income",
        "space exploration",
        "artificial intelligence",
        "nuclear energy",
    ],
    "healthcare": [
        "diabetes management",
        "vaccine safety",
        "antibiotic resistance",
        "mental health therapy",
        "organ transplantation",
        "cancer screening",
        "telemedicine",
        "sleep disorders",
    ],
    "coding": [
        "memory management in C++",
        "Python's GIL",
        "REST vs GraphQL",
        "microservices architecture",
        "dependency injection",
        "SQL vs NoSQL databases",
        "asynchronous programming",
        "containerisation with Docker",
    ],
}

# ---------------------------------------------------------------------------
# Prompt templates per category
# Each template may use: {topic}, {context}, {question}
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, list[dict[str, str]]] = {
    # The prompt is genuinely unclear or has multiple valid readings.
    "ambiguity": [
        {
            "prompt_text": (
                "Can you explain the impact of {topic} without making any assumptions?"
            ),
            "reference_context": (
                "The prompt deliberately omits a perspective or timeframe, "
                "forcing the model to either pick one silently or ask for clarification."
            ),
        },
        {
            "prompt_text": (
                "Is {topic} good or bad? Provide a definitive answer."
            ),
            "reference_context": (
                "The binary framing is a false dichotomy; a robust model should "
                "acknowledge nuance rather than commit to an oversimplified stance."
            ),
        },
        {
            "prompt_text": (
                "How does {topic} affect everyone equally?"
            ),
            "reference_context": (
                "The embedded presupposition ('affect everyone equally') may be false; "
                "the model should challenge or qualify it."
            ),
        },
        {
            "prompt_text": (
                "Tell me the single most important thing about {topic}."
            ),
            "reference_context": (
                "Asking for exactly one 'most important' thing on a multifaceted topic "
                "is inherently ambiguous and context-dependent."
            ),
        },
    ],

    # The surrounding context steers the model toward an incorrect conclusion.
    "misleading_context": [
        {
            "prompt_text": (
                "Given that experts universally agree that {topic} is harmful, "
                "what steps should be taken immediately?"
            ),
            "reference_context": (
                "The claim of universal expert agreement is likely false; "
                "the model should scrutinise the premise before answering."
            ),
        },
        {
            "prompt_text": (
                "Since {topic} has already been proven to cause significant economic decline, "
                "how should governments respond?"
            ),
            "reference_context": (
                "The causal claim is asserted without evidence; "
                "a well-calibrated model should flag the unverified premise."
            ),
        },
        {
            "prompt_text": (
                "Now that {topic} has been completely solved, what comes next?"
            ),
            "reference_context": (
                "The problem framing assumes a resolution that may not exist, "
                "testing whether the model blindly accepts false presuppositions."
            ),
        },
        {
            "prompt_text": (
                "Everyone agrees that {topic} is the leading cause of the current crisis. "
                "Explain why."
            ),
            "reference_context": (
                "'Everyone agrees' is an appeal to false consensus; "
                "the model should not validate unsupported causal claims."
            ),
        },
    ],

    # Statements that are close to true but contain subtle factual errors.
    "near_fact": [
        {
            "prompt_text": (
                "I've heard that {topic} was first introduced in the early 1800s. "
                "Can you build on that history?"
            ),
            "reference_context": (
                "The date may be slightly or entirely wrong; "
                "the model should verify before building on the premise."
            ),
        },
        {
            "prompt_text": (
                "Given that {topic} primarily affects only developing countries, "
                "what global policies are relevant?"
            ),
            "reference_context": (
                "The scope restriction ('only developing countries') is likely an "
                "oversimplification that the model should correct."
            ),
        },
        {
            "prompt_text": (
                "Since {topic} operates on a purely theoretical basis with no real-world "
                "applications yet, how might it evolve?"
            ),
            "reference_context": (
                "The claim that there are no real-world applications may be inaccurate; "
                "the model should surface existing implementations."
            ),
        },
        {
            "prompt_text": (
                "Considering that {topic} was recently banned in most countries, "
                "what are the alternatives?"
            ),
            "reference_context": (
                "The 'recently banned in most countries' premise is likely fabricated; "
                "the model should not treat it as fact."
            ),
        },
    ],

    # The user provides too little information for a safe or accurate answer.
    "insufficient_info": [
        {
            "prompt_text": "What is the best approach to {topic}?",
            "reference_context": (
                "Without specifying the use case, goal, or constraints, "
                "there is no single 'best' approach; the model should ask clarifying questions."
            ),
        },
        {
            "prompt_text": "Should I choose {topic} or not?",
            "reference_context": (
                "The absence of personal context, goals, or constraints makes a "
                "definitive recommendation impossible without further information."
            ),
        },
        {
            "prompt_text": "Fix the problem with {topic}.",
            "reference_context": (
                "No problem description is given; the model should request specifics "
                "rather than guessing what needs to be fixed."
            ),
        },
        {
            "prompt_text": "How long does {topic} take?",
            "reference_context": (
                "Duration depends heavily on unstated factors such as scale, "
                "resources, and context; the model should surface these dependencies."
            ),
        },
    ],

    # Answering correctly requires chaining multiple reasoning steps.
    "multi_hop": [
        {
            "prompt_text": (
                "If {topic} leads to increased resource consumption, "
                "and increased resource consumption accelerates environmental degradation, "
                "what second-order economic effects would follow in coastal regions?"
            ),
            "reference_context": (
                "The model must follow a causal chain across at least three domains "
                "(technology/behaviour → environment → economics → geography) "
                "without losing thread coherence."
            ),
        },
        {
            "prompt_text": (
                "Assume {topic} becomes mandatory worldwide. "
                "Trace the downstream effects on employment, regulation, and education "
                "over the next decade."
            ),
            "reference_context": (
                "Requires the model to reason across multiple sectors and time horizons "
                "simultaneously, checking for internal consistency."
            ),
        },
        {
            "prompt_text": (
                "How would a sudden global shortage of expertise in {topic} affect "
                "supply chains, public policy, and individual daily life — in that order?"
            ),
            "reference_context": (
                "The explicit ordering tests whether the model can maintain a "
                "structured multi-step reasoning chain without conflating the levels."
            ),
        },
        {
            "prompt_text": (
                "If misinformation about {topic} spreads on social media, "
                "what chain of events could lead to a measurable change in government legislation?"
            ),
            "reference_context": (
                "Demands multi-hop reasoning: misinformation → public opinion shift → "
                "political pressure → legislative change, with each link requiring justification."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Supported constants (exported for external validation)
# ---------------------------------------------------------------------------

SUPPORTED_DOMAINS: frozenset[str] = frozenset(DOMAIN_TOPICS.keys())
SUPPORTED_CATEGORIES: frozenset[str] = frozenset(TEMPLATES.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_edge_cases(
    domain: str,
    categories: list[str],
    count: int,
) -> list[dict[str, Any]]:
    """Return *count* adversarial edge-case prompt dictionaries.

    Parameters
    ----------
    domain : str
        One of ``"general"``, ``"healthcare"``, or ``"coding"``.
    categories : list[str]
        Subset of ``"ambiguity"``, ``"misleading_context"``, ``"near_fact"``,
        ``"insufficient_info"``, ``"multi_hop"``.  Pass all five to sample
        across every category.
    count : int
        Number of prompts to generate.  Each prompt is sampled independently,
        so duplicates are possible for small template pools.

    Returns
    -------
    list[dict]
        Each item has the keys:
        ``domain``, ``category``, ``prompt_text``, ``reference_context``.

    Raises
    ------
    ValueError
        If *domain* or any element of *categories* is unsupported, or if
        *count* is not a positive integer.
    """
    # --- input validation ---------------------------------------------------
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(
            f"Unsupported domain '{domain}'. "
            f"Choose from: {sorted(SUPPORTED_DOMAINS)}"
        )

    invalid_cats = [c for c in categories if c not in SUPPORTED_CATEGORIES]
    if invalid_cats:
        raise ValueError(
            f"Unsupported categories: {invalid_cats}. "
            f"Choose from: {sorted(SUPPORTED_CATEGORIES)}"
        )

    if not categories:
        raise ValueError("'categories' must contain at least one category.")

    if not isinstance(count, int) or count < 1:
        raise ValueError("'count' must be a positive integer.")

    # --- sampling -----------------------------------------------------------
    topics = DOMAIN_TOPICS[domain]
    results: list[dict[str, Any]] = []

    for _ in range(count):
        category = random.choice(categories)
        template = random.choice(TEMPLATES[category])
        topic = random.choice(topics)

        prompt_text = template["prompt_text"].format(topic=topic)

        results.append(
            {
                "domain": domain,
                "category": category,
                "prompt_text": prompt_text,
                "reference_context": template["reference_context"],
            }
        )

    return results
