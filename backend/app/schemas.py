"""Pydantic response shapes that don't map 1:1 to a DB table.

Kept separate from app/models.py (SQLModel table=True definitions) so
it's obvious at a glance which classes are persisted tables and which
are just API response shapes built by joining/reshaping them.
"""
from datetime import datetime

from pydantic import BaseModel


class QueuedPostOut(BaseModel):
    post_id: int
    card_id: int
    product_id: int
    product_title: str
    product_image_url: str
    platform: str
    post_text: str
    scheduled_for: str  