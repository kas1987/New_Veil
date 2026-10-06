"""Database helpers with graceful fallbacks for optional dependencies."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "veil_db"),
    "user": os.getenv("DB_USER", "veil_user"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db_connection():  # pragma: no cover - exercised only when DB exists
    """Attempt to open a PostgreSQL connection.

    Returns ``None`` if psycopg2 is unavailable or the connection attempt fails.
    This keeps the higher-level mechanics usable in offline/test environments.
    """

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            cursor_factory=RealDictCursor,
        )
        return conn
    except ImportError:
        logger.info("psycopg2 not installed - database features disabled")
        return None
    except Exception as exc:  # noqa: BLE001 - we want to swallow all DB errors
        logger.warning("Database connection failed: %s", exc)
        return None


def execute_query(query: str, params: Optional[Iterable[Any]] = None):
    """Execute a SELECT-style query and return rows as dicts (or ``None``)."""

    conn = get_db_connection()
    if conn is None:
        return None

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.error("Query execution failed: %s", exc)
        return None


def execute_function(function_name: str, params: Optional[Iterable[Any]] = None):
    """Execute a stored function and return rows."""

    conn = get_db_connection()
    if conn is None:
        return None

    placeholders = ", ".join(["%s"] * len(params)) if params else ""
    query = (
        f"SELECT * FROM {function_name}({placeholders})"
        if placeholders
        else f"SELECT * FROM {function_name}()"
    )

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.error("Function execution failed: %s", exc)
        return None


def insert_log(table: str, data: Dict[str, Any]) -> bool:
    """Insert a log row if the database is reachable."""

    conn = get_db_connection()
    if conn is None:
        return False

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Log insertion failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Mock data helpers used by the Lyssandra mechanics
# ---------------------------------------------------------------------------

MOCK_PERSONAS = {
    (1, "czech"): {
        "persona_id": "lyssandra_lover_czech",
        "base_mask": "lover",
        "cultural_mask": "czech",
        "display_name": "The Ice Seductress",
        "voice_engine": "cs-CZ-VlastaNeural",
    },
    (1, "russian"): {
        "persona_id": "lyssandra_lover_russian",
        "base_mask": "lover",
        "cultural_mask": "russian",
        "display_name": "The Maternal Flame",
        "voice_engine": "ru-RU-SvetlanaNeural",
    },
    (1, "australian"): {
        "persona_id": "lyssandra_lover_australian",
        "base_mask": "lover",
        "cultural_mask": "australian",
        "display_name": "The Casual Charmer",
        "voice_engine": "en-AU-NatashaNeural",
    },
    (5, "czech"): {
        "persona_id": "lyssandra_sovereign_czech",
        "base_mask": "sovereign",
        "cultural_mask": "czech",
        "display_name": "The Crystal Throne",
        "voice_engine": "cs-CZ-VlastaNeural",
    },
    (5, "russian"): {
        "persona_id": "lyssandra_sovereign_russian",
        "base_mask": "sovereign",
        "cultural_mask": "russian",
        "display_name": "The Iron Mother",
        "voice_engine": "ru-RU-SvetlanaNeural",
    },
    (5, "australian"): {
        "persona_id": "lyssandra_sovereign_australian",
        "base_mask": "sovereign",
        "cultural_mask": "australian",
        "display_name": "The Desert Queen",
        "voice_engine": "en-AU-NatashaNeural",
    },
    (8, "czech"): {
        "persona_id": "lyssandra_huntress_czech",
        "base_mask": "huntress",
        "cultural_mask": "czech",
        "display_name": "The Calculated Predator",
        "voice_engine": "cs-CZ-VlastaNeural",
    },
    (8, "russian"): {
        "persona_id": "lyssandra_huntress_russian",
        "base_mask": "huntress",
        "cultural_mask": "russian",
        "display_name": "The Volcanic Possessor",
        "voice_engine": "ru-RU-SvetlanaNeural",
    },
    (8, "australian"): {
        "persona_id": "lyssandra_huntress_australian",
        "base_mask": "huntress",
        "cultural_mask": "australian",
        "display_name": "The Outback Predator",
        "voice_engine": "en-AU-NatashaNeural",
    },
}


def get_mock_persona(mirror_state: int, cultural_mask: str) -> Dict[str, Any]:
    """Fallback persona selection used when no database is available."""

    if 1 <= mirror_state <= 3:
        base_state = 1
    elif 4 <= mirror_state <= 6:
        base_state = 5
    else:
        base_state = 8

    return MOCK_PERSONAS.get(
        (base_state, cultural_mask),
        {
            "persona_id": f"lyssandra_unknown_{cultural_mask}",
            "base_mask": "unknown",
            "cultural_mask": cultural_mask,
            "display_name": "Unknown Persona",
            "voice_engine": "unknown",
        },
    )


__all__ = [
    "DB_CONFIG",
    "execute_function",
    "execute_query",
    "get_db_connection",
    "get_mock_persona",
    "insert_log",
]
