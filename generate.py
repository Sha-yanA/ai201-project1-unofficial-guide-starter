"""
Grounded generation pipeline.

Retrieves chunks from ChromaDB, filters by relevance, then calls Groq
llama-3.3-70b-versatile with a strict grounding prompt.

Grounding is enforced in two layers:
  1. Pre-LLM: chunks with cosine distance > MAX_DISTANCE are dropped; if none
     pass, the LLM is never called and a "not enough information" reply is
     returned directly.
  2. System prompt: model is told explicitly to refuse any question the context
     cannot answer, and to never draw on training knowledge.

Source attribution is programmatic: built from chunk metadata after generation,
not extracted from the LLM response.

Exposes:
    ask(query, k=5)  →  {"answer": str, "sources": list[dict], "chunks": list[dict]}

Run directly for an end-to-end smoke test:
    python generate.py
"""

import os

from dotenv import load_dotenv
from groq import Groq

from embed import retrieve

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5
# Cosine distance ceiling: chunks above this score are too dissimilar to use.
# Range is [0, 2]; typical relevant hits fall under 0.6, noise tends to exceed 0.75.
MAX_DISTANCE = 0.70

_SYSTEM_PROMPT = """\
You are a factual assistant that answers questions about UF (University of Florida) \
campus dining — dining halls, meal plans, late-night food, and dietary options.

=== GROUNDING RULES (non-negotiable) ===
1. Answer ONLY using the numbered context passages provided by the user.
2. Do NOT draw on your training knowledge about UF dining, Gainesville \
restaurants, or meal plan pricing. Treat everything you know from training \
as if it does not exist.
3. If the context passages do not contain enough information to answer the \
question, respond with this exact sentence and nothing else:
   "I don't have enough information in my sources to answer that."
4. Do NOT guess, estimate, or fill in details absent from the context.
5. Do NOT reference passage numbers, passage positions, or source names. \
Do NOT say things like "one reviewer", "the individual", "another perspective", \
or "passage [X]". Attribution is handled separately. \
Write a direct answer in plain prose. When opinions differ across the context, \
use natural phrases like "opinions are mixed", "most students say", or \
"some prefer X while others prefer Y" — never point back to the structure \
of the context you were given.
6. Write in clear, direct prose. Be concise — aim for 3–6 sentences unless \
a list is genuinely clearer.
"""


def _format_context(chunks: list[dict]) -> str:
    return "\n\n".join(c["text"] for c in chunks)


def ask(query: str, k: int = TOP_K) -> dict:
    """
    Full RAG pipeline: retrieve → distance-filter → generate → attribute sources.

    Returns a dict with:
        answer   — grounded LLM response (or a "not enough information" string)
        sources  — deduplicated list of source dicts built from chunk metadata
        chunks   — the filtered chunks that were actually sent to the LLM
    """
    all_chunks = retrieve(query, k=k)

    # Layer 1 grounding: drop anything too dissimilar before touching the LLM
    relevant = [c for c in all_chunks if c["distance"] <= MAX_DISTANCE]

    if not relevant:
        return {
            "answer": "I don't have enough information in my sources to answer that.",
            "sources": [],
            "chunks": all_chunks,
        }

    context = _format_context(relevant)
    user_message = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {query}"
    )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=600,
    )
    answer = response.choices[0].message.content.strip()

    # Programmatic attribution: built from metadata, never parsed from LLM text
    seen: set[tuple] = set()
    sources: list[dict] = []
    for chunk in relevant:
        key = (chunk["source"], chunk["url"])
        if key not in seen:
            seen.add(key)
            sources.append(
                {
                    "source": chunk["source"],
                    "location": chunk["location"],
                    "url": chunk["url"],
                    "doc_type": chunk["doc_type"],
                    "filename": chunk["filename"],
                }
            )

    return {"answer": answer, "sources": sources, "chunks": relevant}


if __name__ == "__main__":
    test_queries = [
        "What do students say about food quality at Gator Corner compared to Broward?",
        "Are there vegan options at UF dining halls?",
        "How much does a UF meal plan cost and is it worth buying?",
        "What food options are available at the Reitz Union?",
        "Where can UF students find food after midnight?",
        # Grounding test — should get "not enough information"
        "What is the best Italian restaurant in Gainesville?",
    ]

    print("=== End-to-end RAG smoke test ===\n")
    for query in test_queries:
        print(f"Q: {query}")
        result = ask(query)
        print(f"A: {result['answer']}\n")
        if result["sources"]:
            print("Sources:")
            for s in result["sources"]:
                print(f"  [{s['source']}] {s['location']}")
                print(f"  {s['url']}")
        else:
            print("Sources: none (no relevant chunks found)")
        print("-" * 70)
