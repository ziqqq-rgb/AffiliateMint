"""
Deep research agent - the "credibility section" (FR-2.x extension).

Not every product has ingredients to research, but most products have
SOME differentiator worth digging into beyond price/rating/units_sold -
this could be active ingredients (skincare/supplements), material tech
(fabric, sole compound, aluminum grade), brand/model heritage (a shoe
model's design history), or certifications (safety/quality standards).
Whatever fits the product category.

Two-step process, both isolated so either can be tested/tuned alone:

1. extract_research_topics() - a cheap LLM call that decides IF this
   product has a genuine differentiator worth researching, and WHAT KIND
   (see TOPIC_EXTRACTION_PROMPT for the category examples). Returns []
   for a plain generic product with nothing distinctive to say.

2. build_deep_research() - for each topic, pulls real context via
   Firecrawl search (same tool/pattern as market_context.py), then asks
   the LLM to structure it into a short research section.

Health/ingredient claims carry real regulatory risk - the synthesis
prompt asks for hedged, sourced language ONLY for that kind of topic.
Material/heritage topics don't need medical hedging, so the prompt
tells the model to match tone to topic type.
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

Does this product have a genuine differentiator worth researching in
depth - something beyond its price, rating, or units sold that would
give a content creator a credible, specific detail to mention?

This can be ANY of these, whichever actually fits the product:
- Active ingredients/compounds (e.g. "retinol", "ashwagandha" - skincare, supplements)
- Material technology (e.g. "ripstop nylon", "aluminum alloy frame", a fabric's tech name)
- Brand or model heritage (e.g. a sneaker model's design history/year of origin)
- Certifications or standards (e.g. "IP68 water resistance", "OEKO-TEX certified")

Most generic/commodity products (plain phone cases, basic accessories,
unbranded homeware) have NOTHING here - only flag genuinely researchable
topics, don't force one.

Return a JSON list of up to {max_topics} topic strings, as specific as
possible (e.g. ["Onitsuka Tiger Mexico 66 heritage"], ["ripstop nylon fabric"],
["ashwagandha"]). Return an empty list [] if nothing is worth researching.
"""

SYNTHESIS_PROMPT = """\
You are writing a short, credible research section for a Malaysian
affiliate content creator, for topic: "{topic}".

Use ONLY the source material below - do not invent facts, studies, or
statistics not supported by it.

If this topic is a health/ingredient/supplement topic, use hedged
language ("may help", "is associated with") rather than definitive
medical claims - this is marketing research material, not medical advice.
If this topic is about material tech, brand/model heritage, or
certifications, write plainly and factually - no hedging needed since
there's no health claim involved.

Source material:
{context}

Return JSON with exactly these keys:
- what_it_is (string, 1-2 sentences)
- how_it_works (string, plain-language explanation of the mechanism/history/spec)
- who_benefits (string, who this matters to / who should care)
- things_to_know (string, caveats or limitations - empty string if the
  source material gives no such signal, do not invent one)
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
    nothing."""
    results = search(f"{topic} explained", limit=REQUEST_LIMIT_PER_TOPIC)

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
    """Returns a JSON-encoded list of topic dossiers, or "[]" if this
    product had nothing genuinely worth deep-researching (or every
    topic's search came back empty)."""
    topics = _extract_research_topics(product)

    results = [entry for topic in topics if (entry := _research_one_topic(topic)) is not None]
    return json.dumps(results)