"""
Deep research agent - the "ingredient science" section (FR-2.x extension,
your idea from chat: skincare actives, supplements like ashwagandha -
who needs it, what the science says).

Two-step process, both isolated so either can be tested/tuned alone:

1. extract_research_topics() - a cheap LLM call that decides IF this
   product even has ingredient/compound-style topics worth researching.
   Returns [] for e.g. a phone case - deep research is additive, not
   forced onto every product.

2. build_deep_research() - for each topic, pulls real evidence-based
   context via Firecrawl search (same tool/pattern as market_context.py),
   then asks the LLM to structure it into a science section.

Health/supplement claims carry real regulatory risk in affiliate
marketing - the prompt below deliberately asks for hedged, sourced
language ("may support...") rather than medical claims, and this is
marketing copy raw material, not medical advice. Review before publishing.
"""
import json

from agents.market_context import clean_markdown
from agents.providers.firecrawl_client import search
from agents.providers.nvidia_client import run_task
from app.models import ScrapedProduct

MAX_TOPICS = 3
REQUEST_LIMIT_PER_TOPIC = 8
MAX_RESULTS_PER_TOPIC = 4
MAX_CHARS_PER_RESULT = 700

TOPIC_EXTRACTION_PROMPT = """\
Product title: {title}
Raw listing data: {raw_payload}

Does this product have specific active ingredients, compounds, or
materials worth researching in depth (e.g. a supplement's herbs, a
skincare serum's actives, a fabric's material tech)? Most products
(electronics, accessories, homeware, generic apparel) do NOT - only
flag genuine ingredient/compound-driven products.

Return a JSON list of up to {max_topics} ingredient/compound names as
plain strings (e.g. ["ashwagandha", "vitamin D3"]). Return an empty
list [] if this product has nothing worth deep-researching.
"""

SYNTHESIS_PROMPT = """\
You are writing a science-backed research section for a Malaysian
affiliate content creator, for topic: "{topic}".

Use ONLY the source material below - do not invent studies, statistics,
or claims not supported by it. Use hedged language ("may help", "is
associated with", "some evidence suggests") rather than definitive
medical claims - this is marketing research material, not medical advice.

Source material:
{context}

Return JSON with exactly these keys:
- what_it_is (string, 1-2 sentences)
- how_it_works (string, plain-language summary of the mechanism/science)
- who_benefits (string, who this is typically relevant for)
- things_to_know (string, caveats/who should be cautious - empty string
  if the source material gives no such signal, do not invent one)
"""


def _extract_research_topics(product: ScrapedProduct) -> list[str]:
    prompt = TOPIC_EXTRACTION_PROMPT.format(
        title=product.title,
        raw_payload=product.raw_payload,
        max_topics=MAX_TOPICS,
    )
    topics = run_task(prompt, expects_json=True)
    return topics[:MAX_TOPICS] if isinstance(topics, list) else []


def _gather_topic_context(topic: str) -> tuple[str, list[str]]:
    """Returns (cleaned_context_text, source_urls) for one topic, or
    ("", []) if nothing useful came back - callers skip synthesis
    entirely in that case rather than asking the LLM to write about
    nothing.

    Requests more than MAX_RESULTS_PER_TOPIC for the same reason as
    market_context.py: self-hosted Firecrawl drops some result pages
    silently, so over-requesting absorbs that attrition."""
    results = search(f"{topic} benefits scientific evidence research", limit=REQUEST_LIMIT_PER_TOPIC)

    blocks, sources = [], []
    for r in results:
        cleaned = clean_markdown(r.get("markdown", ""))[:MAX_CHARS_PER_RESULT]
        if cleaned:
            blocks.append(f"Source: {r.get('title', 'Unknown')} ({r.get('url', '')})\n{cleaned}")
            sources.append(r.get("url", ""))
        if len(blocks) >= MAX_RESULTS_PER_TOPIC:
            break

    return "\n\n".join(blocks), sources


def _research_one_topic(topic: str) -> dict | None:
    context, sources = _gather_topic_context(topic)
    if not context:
        return None

    data = run_task(SYNTHESIS_PROMPT.format(topic=topic, context=context), expects_json=True)
    return {**data, "topic": topic, "sources": sources}


def build_deep_research(product: ScrapedProduct) -> str:
    topics = _extract_research_topics(product)
    print(f"[DEEP RESEARCH] topics for '{product.title}': {topics}")   # ADD THIS

    results = [entry for topic in topics if (entry := _research_one_topic(topic)) is not None]
    print(f"[DEEP RESEARCH] synthesized {len(results)}/{len(topics)} topics")   # ADD THIS

    return json.dumps(results)