"""Demo data seeding helpers for dashboard verification."""

from __future__ import annotations

from pathlib import Path

from db import get_connection, init_db, upsert_budget


def seed_demo_data(db_path: str | Path) -> None:
    """Insert realistic demo transactions and budgets if they are missing."""
    db_path = Path(db_path)
    init_db(db_path)
    with get_connection(db_path) as conn:
        demo_transactions = [
            ("2026-05-02", "Maybank salary", 6500.0, "income", "Income", "manual"),
            ("2026-05-03", "Tealive Mid Valley", -12.9, "expense", "Food & drinks", "manual"),
            ("2026-05-05", "GrabCar to office", -18.4, "expense", "Transport", "manual"),
            ("2026-05-07", "Unifi broadband bill", -129.0, "expense", "Bills & utilities", "manual"),
            ("2026-05-09", "Shopee headphones", -89.9, "expense", "Shopping", "manual"),
            ("2026-05-12", "Netflix subscription", -17.9, "expense", "Subscriptions", "manual"),
            ("2026-05-15", "Touch 'n Go top up", -50.0, "expense", "E-wallet top-up", "manual"),
            ("2026-05-18", "Shopee Pay Later instalment", -120.0, "expense", "BNPL repayment", "manual"),
            ("2026-05-25", "ASB dividend", 42.5, "income", "Savings", "manual"),
            ("2026-05-27", "myNEWS sandwich", -9.5, "expense", "Food & drinks", "manual"),
            ("2026-06-01", "June salary", 6500.0, "income", "Income", "manual"),
            ("2026-06-02", "99 Speedmart groceries", -34.7, "expense", "Food & drinks", "manual"),
            ("2026-06-04", "TNB electricity bill", -86.3, "expense", "Bills & utilities", "manual"),
            ("2026-06-06", "GrabFood lunch", -24.6, "expense", "Food & drinks", "manual"),
            ("2026-06-08", "Lazada office chair", -299.0, "expense", "Shopping", "manual"),
            ("2026-06-10", "Touch n Go highway toll", -7.8, "expense", "Transport", "manual"),
            ("2026-06-14", "Spotify premium", -15.9, "expense", "Subscriptions", "manual"),
            ("2026-06-20", "Fixed deposit interest", 18.2, "income", "Savings", "manual"),
            ("2026-06-22", "GrabPay wallet credit", -100.0, "expense", "E-wallet top-up", "manual"),
            ("2026-06-28", "Shopee order confirmation", -58.9, "expense", "Shopping", "manual"),
            ("2026-07-01", "July salary", 6500.0, "income", "Income", "manual"),
            ("2026-07-02", "McDonald's breakfast", -16.4, "expense", "Food & drinks", "manual"),
            ("2026-07-03", "Parking at office", -8.0, "expense", "Transport", "manual"),
            ("2026-07-04", "Air Selangor water bill", -24.5, "expense", "Bills & utilities", "manual"),
            ("2026-07-05", "Apple iCloud", -4.9, "expense", "Subscriptions", "manual"),
            ("2026-07-06", "Shopee laptop stand", -49.9, "expense", "Shopping", "manual"),
        ]
        for row in demo_transactions:
            date_value, description, amount, tx_type, category, source = row
            conn.execute(
                """
                INSERT OR IGNORE INTO transactions
                (date, description, amount, type, category, source, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (date_value, description, amount, tx_type, category, source, description),
            )

        demo_budgets = {
            "Food & drinks": 300.0,
            "Transport": 200.0,
            "Shopping": 400.0,
            "Bills & utilities": 250.0,
            "Subscriptions": 50.0,
            "E-wallet top-up": 150.0,
            "BNPL repayment": 200.0,
            "Savings": 1000.0,
        }
        for category, limit in demo_budgets.items():
            upsert_budget(conn, category, limit, 80)

