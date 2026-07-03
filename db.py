"""SQLite helpers for the personal finance tracker."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Return a SQLite connection with row access by column name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path) -> None:
    """Create the core tables if they do not already exist."""
    with closing(get_connection(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                raw_text TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(date, amount, description)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                monthly_limit REAL NOT NULL,
                alert_pct REAL DEFAULT 80
            );
            """
        )
        conn.commit()


def insert_transaction(
    conn: sqlite3.Connection,
    date: str,
    description: str,
    amount: float,
    type: str,
    category: str,
    source: str,
    raw_text: str | None,
) -> bool:
    """Insert a transaction if it is not already present.

    Returns True when inserted, False when skipped as a duplicate.
    """
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO transactions
        (date, description, amount, type, category, source, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (date, description, amount, type, category, source, raw_text),
    )
    conn.commit()
    return cur.rowcount == 1


def get_transactions(conn: sqlite3.Connection, month: int, year: int) -> list[sqlite3.Row]:
    """Return all transactions for the selected month and year."""
    month_prefix = f"{year:04d}-{month:02d}-%"
    cur = conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE date LIKE ?
        ORDER BY date DESC, id DESC
        """,
        (month_prefix,),
    )
    return cur.fetchall()


def get_monthly_summary(conn: sqlite3.Connection, month: int, year: int) -> dict[str, float | int]:
    """Return monthly totals for income, expense, net and count."""
    month_prefix = f"{year:04d}-{month:02d}-%"
    cur = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END), 0) AS expense,
            COALESCE(SUM(amount), 0) AS net,
            COUNT(*) AS count
        FROM transactions
        WHERE date LIKE ?
        """,
        (month_prefix,),
    )
    row = cur.fetchone()
    return {
        "income": float(row["income"]),
        "expense": float(row["expense"]),
        "net": float(row["net"]),
        "count": int(row["count"]),
    }


def upsert_budget(conn: sqlite3.Connection, category: str, monthly_limit: float, alert_pct: float = 80) -> None:
    """Create or update a category budget."""
    conn.execute(
        """
        INSERT INTO budgets (category, monthly_limit, alert_pct)
        VALUES (?, ?, ?)
        ON CONFLICT(category) DO UPDATE SET
            monthly_limit = excluded.monthly_limit,
            alert_pct = excluded.alert_pct
        """,
        (category, monthly_limit, alert_pct),
    )
    conn.commit()


def get_budget(conn: sqlite3.Connection, category: str) -> float | None:
    """Return a category budget limit if one exists."""
    cur = conn.execute("SELECT monthly_limit FROM budgets WHERE category = ?", (category,))
    row = cur.fetchone()
    return None if row is None else float(row["monthly_limit"])


def get_all_budgets(conn: sqlite3.Connection) -> dict[str, float]:
    """Return all category budgets as a mapping."""
    cur = conn.execute("SELECT category, monthly_limit FROM budgets ORDER BY category")
    return {row["category"]: float(row["monthly_limit"]) for row in cur.fetchall()}


def get_category_spend(conn: sqlite3.Connection, category: str, month: int, year: int) -> float:
    """Return total spend for a category in a given month."""
    month_prefix = f"{year:04d}-{month:02d}-%"
    cur = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS spend
        FROM transactions
        WHERE date LIKE ?
          AND category = ?
          AND amount < 0
        """,
        (month_prefix, category),
    )
    row = cur.fetchone()
    return abs(float(row["spend"]))

