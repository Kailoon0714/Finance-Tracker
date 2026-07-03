"""SQLite helpers for the Railway notification relay."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("relay.db")


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with closing(get_connection(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                received_at TEXT DEFAULT (datetime('now')),
                processed INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def insert_notification(payload: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    with closing(get_connection(db_path)) as conn:
        cur = conn.execute("INSERT INTO notification_queue (payload) VALUES (?)", (payload,))
        conn.commit()
        return int(cur.lastrowid)


def get_pending(limit: int = 50, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with closing(get_connection(db_path)) as conn:
        cur = conn.execute(
            """
            SELECT id, payload, received_at, processed
            FROM notification_queue
            WHERE processed = 0
            ORDER BY id ASC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def mark_processed(ids: list[int], db_path: str | Path = DEFAULT_DB_PATH) -> int:
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    with closing(get_connection(db_path)) as conn:
        cur = conn.execute(
            f"UPDATE notification_queue SET processed = 1 WHERE id IN ({placeholders})",
            ids,
        )
        conn.commit()
        return int(cur.rowcount)
