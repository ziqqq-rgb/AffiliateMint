"""
Hermes' persistent memory ledger - a local SQLite FTS5 full-text index
of past scripts and their logged performance.

This is NOT a trained model (design doc, section 7 - "No true
learning"). It's a keyword search over history: "has something like
this worked before?" That's a deliberately honest scope, matching the
doc's own risk notes.
"""

import json
import re
import sqlite3
from pathlib import Path

DB_PATH = Path("./hermes_memory.db")

_CREATE_TABLE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS memory USING fts5(
    angle_type, hook_ms, product_title, commission_earned_rm, notes
);
"""
_CREATE_THREADS_TABLE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS threads_memory USING fts5(
    post_text, notes
);
"""


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE_SQL)
    conn.execute(_CREATE_THREADS_TABLE_SQL) 
    return conn


def _sanitize_fts_query(text: str) -> str:
    """FTS5's MATCH syntax treats &, %, (, ), -, etc. as query operators,
    not literal characters - a USP like "turmeric & lemon (70% off)"
    raises a syntax error otherwise. Strip down to plain words since this
    is a keyword lookup, not a query language the caller controls."""
    words = re.findall(r"\w+", text)
    return " ".join(words)


def _dossier_search_text(dossier) -> str:
    """dossier.usps is a JSON-encoded list of 3 strings - flatten to one
    string for the FTS query, same role `dossier.usp` played before the
    single-USP -> 3-USP change."""
    return " ".join(json.loads(dossier.usps))


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
    USPs. Returns a short plain-text summary the script prompt can drop
    in directly."""
    query = _sanitize_fts_query(_dossier_search_text(dossier))
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

def remember_edit(script) -> None:
    """Logs a manually-edited script into the same ledger remember_performance
    uses, tagged distinctly - lets a future prompt favor hooks the operator
    actually kept/rewrote, not just ones that earned commission (point 3)."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO memory (angle_type, hook_ms, product_title, commission_earned_rm, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (script.angle_type, script.hook_ms, "", "0", "manually edited by operator"),
    )
    conn.commit()
    conn.close()

def remember_threads_edit(post) -> None:
    """Threads analogue of remember_edit() above. Kept in its own FTS5
    table since a Threads post has no angle_type/hook_ms split - it's
    one block of text."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO threads_memory (post_text, notes) VALUES (?, ?)",
        (post.post_text, "manually edited by operator"),
    )
    conn.commit()
    conn.close()


def search_similar_threads_posts(dossier, limit: int = 3) -> str:
    """Full-text search over past kept/edited Threads posts related to
    this product's USPs - feeds threads_agent's prompt, same role as
    search_similar_performance() for the script prompt."""
    query = _sanitize_fts_query(_dossier_search_text(dossier))
    if not query:
        return ""

    conn = _get_connection()
    cursor = conn.execute(
        "SELECT post_text FROM threads_memory WHERE threads_memory MATCH ? ORDER BY rank LIMIT ?",
        (query, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""
    return "\n".join(f'- "{text}"' for (text,) in rows)