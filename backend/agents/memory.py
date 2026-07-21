"""
Hermes' persistent memory ledger - a local SQLite FTS5 full-text index
of past scripts and their logged performance.

This is NOT a trained model (design doc, section 7 - "No true
learning"). It's a keyword search over history: "has something like
this worked before?" That's a deliberately honest scope, matching the
doc's own risk notes.
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path("./hermes_memory.db")

_CREATE_TABLE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS memory USING fts5(
    angle_type, hook_ms, product_title, commission_earned_rm, notes
);
"""


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE_SQL)
    return conn


def _sanitize_fts_query(text: str) -> str:
    """FTS5's MATCH syntax treats &, %, (, ), -, etc. as query operators,
    not literal characters - a USP like "turmeric & lemon (70% off)"
    raises a syntax error otherwise. Strip down to plain words since this
    is a keyword lookup, not a query language the caller controls."""
    words = re.findall(r"\w+", text)
    return " ".join(words)


def remember_performance(script, earnings) -> None:
    """Called from app/services/feedback.py once earnings are logged
    (FR-3.4 feedback loop)."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO memory (angle_type, hook_ms, product_title, commission_earned_rm, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            script.angle_type,
            script.hook_ms,
            "",  # TODO: join in product title once ScriptVariation carries a denormalized copy
            str(earnings.commission_earned_rm),
            earnings.notes or "",
        ),
    )
    conn.commit()
    conn.close()


def search_similar_performance(dossier, limit: int = 3) -> str:
    """Full-text search for past hooks/angles related to this product's
    USP. Returns a short plain-text summary the script prompt can drop
    in directly."""
    query = _sanitize_fts_query(dossier.usp)
    if not query:
        return ""

    conn = _get_connection()
    cursor = conn.execute(
        "SELECT angle_type, hook_ms, commission_earned_rm FROM memory "
        "WHERE memory MATCH ? ORDER BY rank LIMIT ?",
        (query, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""
    lines = [f'- {angle}: "{hook}" earned RM{rm}' for angle, hook, rm in rows]
    return "\n".join(lines)