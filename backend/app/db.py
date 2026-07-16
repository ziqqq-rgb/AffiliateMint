"""
Database engine and session management.

Kept deliberately thin: this file only knows how to open connections.
It has no knowledge of what a ScrapedProduct or ContentCard is - that
separation is what lets SQLite be swapped for Postgres later
(NFR 5.5 / design doc 3.1) without touching this file's callers.
"""

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(settings.database_url, echo=settings.sql_echo)


def init_db() -> None:
    """Create all tables if they don't exist yet. Called once on startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: yields one DB session per request."""
    with Session(engine) as session:
        yield session
