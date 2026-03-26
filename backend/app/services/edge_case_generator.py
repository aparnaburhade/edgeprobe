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
# Factual reference context per topic (used to verify LLM claims)
# ---------------------------------------------------------------------------

TOPIC_CONTEXT: dict[str, str] = {
    # general
    "climate change": (
        "Global average temperatures have risen by approximately 1.1°C since the pre-industrial period. "
        "Human activities, primarily burning fossil fuels, are the dominant cause of observed warming since the mid-20th century. "
        "The IPCC projects further warming of 1.5–4.5°C by 2100 depending on emissions scenarios."
    ),
    "social media": (
        "Social media platforms are used by over 5 billion people worldwide. "
        "Studies link heavy use to both positive community building and negative mental health outcomes in adolescents. "
        "Misinformation spreads faster on social media than factual content, according to MIT research."
    ),
    "remote work": (
        "Remote work adoption accelerated significantly during the COVID-19 pandemic. "
        "Research shows remote workers can be as productive as office workers, though outcomes vary by role. "
        "Hybrid work models combining office and remote days are now common in knowledge industries."
    ),
    "electric vehicles": (
        "Electric vehicles produce zero direct tailpipe emissions. "
        "Lithium-ion batteries power most EVs, and their production involves mining lithium, cobalt, and nickel. "
        "EV sales surpassed 10 million units globally in 2022."
    ),
    "universal basic income": (
        "Universal basic income (UBI) is a policy where all citizens receive a regular unconditional cash payment. "
        "Pilot programs in Finland, Kenya, and several US cities have shown reductions in stress and improvements in wellbeing. "
        "Critics raise concerns about funding costs and potential inflation."
    ),
    "space exploration": (
        "NASA's Artemis program aims to return humans to the Moon. "
        "The International Space Station has been continuously inhabited since November 2000. "
        "Private companies like SpaceX have reduced launch costs significantly through reusable rockets."
    ),
    "artificial intelligence": (
        "Artificial intelligence refers to machine systems that perform tasks typically requiring human intelligence. "
        "Large language models are trained on vast text datasets using transformer architectures. "
        "AI systems have achieved human-level performance on specific tasks such as image classification and game playing."
    ),
    "nuclear energy": (
        "Nuclear power plants generate electricity through fission of uranium-235. "
        "Nuclear energy produces very low greenhouse gas emissions per kilowatt-hour compared to fossil fuels. "
        "Radioactive waste from nuclear plants requires secure storage for thousands of years."
    ),
    # healthcare
    "diabetes management": (
        "Type 2 diabetes can be managed through diet, exercise, and medication. "
        "Weight loss and reduced carbohydrate intake help control blood glucose levels. "
        "Type 1 diabetes is an autoimmune condition requiring lifelong insulin therapy."
    ),
    "vaccine safety": (
        "Vaccines undergo rigorous clinical trials before regulatory approval. "
        "Serious adverse effects from approved vaccines are rare; benefits outweigh risks for most people. "
        "The MMR vaccine does not cause autism — this claim was based on a retracted fraudulent study."
    ),
    "antibiotic resistance": (
        "Antibiotic resistance occurs when bacteria evolve to survive antibiotic exposure. "
        "Overuse and misuse of antibiotics in humans and livestock accelerates resistance. "
        "The WHO lists antimicrobial resistance as one of the greatest threats to global health."
    ),
    "mental health therapy": (
        "Cognitive behavioural therapy (CBT) is one of the most evidence-based treatments for depression and anxiety. "
        "Therapy outcomes improve when combined with appropriate medication for moderate to severe conditions. "
        "Access to mental health services remains limited in low- and middle-income countries."
    ),
    "organ transplantation": (
        "Organ transplantation requires matching donor and recipient blood type and tissue compatibility. "
        "Immunosuppressant drugs are required lifelong after transplantation to prevent rejection. "
        "There is a global shortage of donor organs; thousands of patients die each year while on waiting lists."
    ),
    "cancer screening": (
        "Early cancer detection through screening significantly improves survival rates. "
        "Common screening tests include mammography for breast cancer and colonoscopy for colorectal cancer. "
        "Not all cancers benefit from routine screening; some screenings carry risks of over-diagnosis."
    ),
    "telemedicine": (
        "Telemedicine allows patients to consult healthcare providers remotely via video or phone. "
        "It has expanded access to care in rural and underserved areas. "
        "Telemedicine is not suitable for all conditions; physical examinations cannot be performed remotely."
    ),
    "sleep disorders": (
        "Insomnia affects approximately 10–30% of adults worldwide. "
        "Sleep apnoea is a disorder where breathing repeatedly stops during sleep and is treated with CPAP therapy. "
        "Chronic sleep deprivation is associated with increased risk of obesity, diabetes, and cardiovascular disease."
    ),
    # coding
    "memory management in C++": (
        "C++ requires manual memory management using new and delete operators. "
        "Memory leaks occur when allocated memory is never freed. "
        "Smart pointers such as std::unique_ptr and std::shared_ptr automate memory cleanup and are preferred in modern C++."
    ),
    "Python's GIL": (
        "Python's Global Interpreter Lock (GIL) prevents multiple native threads from executing Python bytecode simultaneously. "
        "The GIL simplifies CPython's memory management but limits multi-threaded CPU-bound performance. "
        "The multiprocessing module bypasses the GIL by using separate processes instead of threads."
    ),
    "REST vs GraphQL": (
        "REST APIs use fixed endpoints that return predefined data structures. "
        "GraphQL allows clients to request exactly the fields they need, reducing over-fetching and under-fetching. "
        "GraphQL was developed at Facebook in 2012 and open-sourced in 2015."
    ),
    "microservices architecture": (
        "Microservices architecture structures an application as a collection of small, independently deployable services. "
        "Each service typically owns its own database and communicates via APIs or message queues. "
        "Microservices improve scalability and team autonomy but increase operational complexity."
    ),
    "dependency injection": (
        "Dependency injection is a design pattern where a component receives its dependencies from the outside rather than creating them. "
        "It improves testability by allowing dependencies to be replaced with mocks during testing. "
        "Frameworks like Spring (Java) and FastAPI (Python) support dependency injection natively."
    ),
    "SQL vs NoSQL databases": (
        "SQL databases use structured schemas and support ACID transactions. "
        "NoSQL databases offer flexible schemas and horizontal scaling, suited to unstructured or rapidly changing data. "
        "Common NoSQL types include document stores (MongoDB), key-value stores (Redis), and column-family stores (Cassandra)."
    ),
    "asynchronous programming": (
        "Asynchronous programming allows code to perform non-blocking I/O operations, improving throughput. "
        "Python's asyncio library and JavaScript's async/await syntax are common implementations. "
        "Async programming is most beneficial for I/O-bound tasks, not CPU-bound computation."
    ),
    "containerisation with Docker": (
        "Docker packages applications and their dependencies into containers that run consistently across environments. "
        "Containers share the host OS kernel, making them lighter than virtual machines. "
        "Docker images are built from Dockerfiles and distributed via container registries such as Docker Hub."
    ),
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
        },
        {
            "prompt_text": (
                "Is {topic} good or bad? Provide a definitive answer."
            ),
        },
        {
            "prompt_text": (
                "How does {topic} affect everyone equally?"
            ),
        },
        {
            "prompt_text": (
                "Tell me the single most important thing about {topic}."
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
        },
        {
            "prompt_text": (
                "Since {topic} has already been proven to cause significant economic decline, "
                "how should governments respond?"
            ),
        },
        {
            "prompt_text": (
                "Now that {topic} has been completely solved, what comes next?"
            ),
        },
        {
            "prompt_text": (
                "Everyone agrees that {topic} is the leading cause of the current crisis. "
                "Explain why."
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
        },
        {
            "prompt_text": (
                "Given that {topic} primarily affects only developing countries, "
                "what global policies are relevant?"
            ),
        },
        {
            "prompt_text": (
                "Since {topic} operates on a purely theoretical basis with no real-world "
                "applications yet, how might it evolve?"
            ),
        },
        {
            "prompt_text": (
                "Considering that {topic} was recently banned in most countries, "
                "what are the alternatives?"
            ),
        },
    ],

    # The user provides too little information for a safe or accurate answer.
    "insufficient_info": [
        {
            "prompt_text": "What is the best approach to {topic}?",
        },
        {
            "prompt_text": "Should I choose {topic} or not?",
        },
        {
            "prompt_text": "Fix the problem with {topic}.",
        },
        {
            "prompt_text": "How long does {topic} take?",
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
        },
        {
            "prompt_text": (
                "Assume {topic} becomes mandatory worldwide. "
                "Trace the downstream effects on employment, regulation, and education "
                "over the next decade."
            ),
        },
        {
            "prompt_text": (
                "How would a sudden global shortage of expertise in {topic} affect "
                "supply chains, public policy, and individual daily life — in that order?"
            ),
        },
        {
            "prompt_text": (
                "If misinformation about {topic} spreads on social media, "
                "what chain of events could lead to a measurable change in government legislation?"
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
        reference_context = TOPIC_CONTEXT.get(topic, "")

        results.append(
            {
                "domain": domain,
                "category": category,
                "prompt_text": prompt_text,
                "reference_context": reference_context,
            }
        )

    return results
