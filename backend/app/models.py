"""
Database models for the TikTok Shop Affiliate AI Engine.

All five entities live in one file on purpose: each model is small,
they share one lifecycle (product -> dossier -> script -> card ->
earnings), and splitting them into five near-empty files would add
navigation cost without adding clarity. Split this file only if a
single model grows past ~80 lines or gains its own validation logic.

Field names and FR references match section 6 of the design doc.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class ResearchStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CardStatus(str, Enum):
    """Kanban columns - FR-4.1."""

    SCRAPED = "scraped"
    RESEARCHED_PENDING = "researched_pending"
    RESEARCH_APPROVED = "research_approved"
    SCRIPTED_PENDING = "scripted_pending"
    SCRIPT_APPROVED = "script_approved"
    FILMING = "filming"
    READY_TO_POST = "ready_to_post"
    POSTED = "posted"
    EARNINGS_LOGGED = "earnings_logged"


class ScrapedProduct(SQLModel, table=True):
    """One product pulled from TikTok Shop's public website. FR-1.1 - FR-1.4.

    No commission data here on purpose: that field only exists behind
    TikTok's Seller/Affiliate Center login, which this scraper doesn't
    use (see scraper/README or backend/README "How the scraper works").
    Shortlisting instead ranks on rating + units sold.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    tiktok_product_id: str  # TikTok's own ID - lets repeat scrapes de-dupe later
    title: str
    price_rm: float
    original_price_rm: float = 0.0  # pre-discount price, 0 if not on sale
    review_score: float
    review_count: int = 0
    units_sold: int
    shop_name: str = ""
    image_url: str = ""
    product_url: str
    raw_payload: str  # FR-1.4: keep the raw response so a parsing bug doesn't lose data
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchDossier(SQLModel, table=True):
    """Deep research written by the Hermes research agent. FR-2.1 - FR-2.4."""

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="scrapedproduct.id")
    what_it_does: str
    key_benefits: str  # JSON-encoded list - SQLite has no native array type
    usp: str
    review_summary_positive: str
    review_summary_negative: str
    status: ResearchStatus = ResearchStatus.PENDING
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScriptVariation(SQLModel, table=True):
    """One of 3 script angles written by the Hermes script agent. FR-3.1 - FR-3.6."""

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="scrapedproduct.id")
    angle_type: str  # e.g. "problem_hook", "tech_spec", "aesthetic_lifestyle"
    hook_ms: str
    body_ms: str
    cta_ms: str
    caption_ms: str
    hashtags: str  # JSON-encoded list
    visual_notes: str
    is_selected: bool = False


class ContentCard(SQLModel, table=True):
    """The Kanban card tracking one product through the whole pipeline. FR-4.1."""

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="scrapedproduct.id")
    selected_script_id: Optional[int] = Field(default=None, foreign_key="scriptvariation.id")
    status: CardStatus = CardStatus.SCRAPED
    filmed_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    tiktok_video_url: Optional[str] = None  # entered manually - posting itself stays out of scope


class EarningsEntry(SQLModel, table=True):
    """Manually typed-in performance numbers for one posted card. FR-4.4."""

    id: Optional[int] = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="contentcard.id")
    date_checked: datetime = Field(default_factory=datetime.utcnow)
    views: int = 0
    likes: int = 0
    units_sold: int = 0
    commission_earned_rm: float = 0.0
    notes: Optional[str] = None

class ContentCard(SQLModel, table=True):
    """The Kanban card tracking one product through the whole pipeline. FR-4.1."""

    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="scrapedproduct.id")
    selected_script_id: Optional[int] = Field(default=None, foreign_key="scriptvariation.id")
    status: CardStatus = CardStatus.SCRAPED
    filmed_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    tiktok_video_url: Optional[str] = None  # entered manually - posting itself stays out of scope

    is_generating: bool = Field(default=False)
    used_auto_pipeline: bool = Field(default=False)