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

IMPORTANT: this whole module is best-effort. A failure here (Firecrawl
down, LLM returned bad JSON) must never break the main dossier - it
should just mean this product gets no deep-research section this run.
Every external call below is wrapped and logged so "no topics" (LLM's
genuine judgment) can be told apart from "topic dropped due to an
error" by reading the logs, instead of re-running and guessing.
"""
import json
import logging

from agents.market_context import clean_markdown
from agents.providers.firecrawl_client import search
from agents.providers.nvidia_client import run_task
from app.models import ScrapedProduct

logger = logging.getLogger(__name__)

MAX_TOPICS = 3
REQUEST_LIMIT_PER_TOPIC = 8
MAX_RESULTS_PER_TOPIC = 4
MAX_CHARS_PER_RESULT = 700

TOPIC_EXTRACTION_PROMPT = """\
Product title: {title}
Raw listing data: {raw_payload}

Identify up to {max_topics} SPECIFIC topics worth researching in depth -
things beyond price/rating/units sold that give a Malaysian affiliate
content creator a credible, nameable detail to mention in a video or post.

Match the research angle to what the product actually is:
- Skincare, supplements, food/health -> active ingredients or compounds
  (e.g. "niacinamide", "ashwagandha", "collagen peptides")
- Clothing, fashion, traditional/cultural wear -> the specific fabric or
  weave (e.g. "songket weave", "cotton pique"), the garment style or
  silhouette name (e.g. "peplum cut", "baju kurung", "kebaya"), or
  cultural/occasion significance (e.g. "Merdeka Day baju kurung
  traditions", "Raya baju melayu history")
- Electronics, gadgets, appliances -> technical specs or standards
  (e.g. "IP68 water resistance", "USB-C PD fast charging", battery chemistry)
- Footwear, bags, accessories -> material tech (e.g. "EVA midsole",
  "ripstop nylon") or brand/model heritage
- Home, furniture, kitchenware -> material or functional design
  (e.g. "food-grade silicone", "non-stick ceramic coating")
- Anything else -> whatever concrete, specific, nameable detail is
  actually present in the title/listing data - a named material, a
  named style, a named process, a named standard

Only return [] if the product is genuinely generic with no identifiable
detail at all (e.g. "assorted plastic clip", "random sticker pack").
Almost every real product - including plain clothing - has at least ONE
specific, nameable thing worth digging into (a fabric, a cut, a cultural
context, a use-case). Don't force three topics if only one genuinely
fits, but don't default to [] just because the product isn't a
supplement or a gadget.

Return a JSON list of up to {max_topics} topic strings, each as specific
as possible (e.g. ["peplum cut baju kurung Merdeka theme"], ["ripstop
nylon fabric"], ["ashwagandha"]).
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
    """Returns [] both when the LLM genuinely found nothing researchable
    AND when the call itself failed (bad JSON, API error) - the two
    cases are told apart in the logs, not by the return value, since
    callers should treat both identically (no deep research this run)."""
    prompt = TOPIC_EXTRACTION_PROMPT.format(
        title=product.title,
        raw_payload=product.raw_payload,
        max_topics=MAX_TOPICS,
    )
    try:
        topics = run_task(prompt, expects_json=True)
    except Exception as e:
        logger.warning(f"[deep_research] Topic extraction failed for product {product.id}: {e}")
        return []

    if not isinstance(topics, list):
        logger.warning(f"[deep_research] Topic extraction returned non-list for product {product.id}: {topics!r}")
        return []

    if not topics:
        logger.info(f"[deep_research] No researchable topics found for product {product.id} ({product.title!r})")
    else:
        logger.info(f"[deep_research] Topics for product {product.id}: {topics[:MAX_TOPICS]}")

    return topics[:MAX_TOPICS]


def _gather_topic_context(topic: str) -> tuple[str, list[str]]:
    """Returns (cleaned_context_text, source_urls) for one topic, or
    ("", []) if nothing useful came back - callers skip synthesis
    entirely in that case rather than asking the LLM to write about
    nothing. search() already logs its own failures/empty results."""
    results = search(f"{topic} explained", limit=REQUEST_LIMIT_PER_TOPIC)
    if not results:
        logger.warning(f"[deep_research] No search results for topic '{topic}' - dropping this topic")
        return "", []

    blocks, sources = [], []
    for r in results:
        cleaned = clean_markdown(r.get("markdown", ""))[:MAX_CHARS_PER_RESULT]
        if cleaned:
            blocks.append(f"Source: {r.get('title', 'Unknown')} ({r.get('url', '')})\n{cleaned}")
            sources.append(r.get("url", ""))
        if len(blocks) >= MAX_RESULTS_PER_TOPIC:
            break

    if not blocks:
        logger.warning(f"[deep_research] Search returned results but no usable content for topic '{topic}'")

    return "\n\n".join(blocks), sources


def _research_one_topic(topic: str) -> dict | None:
    context, sources = _gather_topic_context(topic)
    if not context:
        return None

    try:
        data = run_task(SYNTHESIS_PROMPT.format(topic=topic, context=context), expects_json=True)
    except Exception as e:
        logger.warning(f"[deep_research] Synthesis failed for topic '{topic}': {e}")
        return None

    return {**data, "topic": topic, "sources": sources}


def build_deep_research(product: ScrapedProduct) -> str:
    """Returns a JSON-encoded list of topic dossiers, or "[]" if this
    product had nothing genuinely worth deep-researching, every topic's
    search came back empty, or something failed along the way. This
    function itself never raises - a broken deep-research run must
    degrade to "[]" rather than blocking the rest of the dossier
    (see _build_dossier in app/services/pipeline.py, which has no
    try/except around this call and relies on that guarantee)."""
    try:
        topics = _extract_research_topics(product)
        results = [entry for topic in topics if (entry := _research_one_topic(topic)) is not None]
    except Exception as e:
        # Belt-and-suspenders: _extract_research_topics and
        # _research_one_topic already catch their own failures, but if
        # anything unexpected slips through, deep research must still
        # degrade gracefully rather than take down the whole dossier.
        logger.error(f"[deep_research] Unexpected failure for product {product.id}: {e}")
        return "[]"

    if topics and not results:
        logger.warning(
            f"[deep_research] Product {product.id}: {len(topics)} topic(s) identified "
            "but none produced usable research (see warnings above)"
        )

    return json.dumps(results)