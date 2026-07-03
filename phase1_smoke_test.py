"""Simple Phase 1 smoke test for the database helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile

from db import (
    get_all_budgets,
    get_budget,
    get_category_spend,
    get_connection,
    get_monthly_summary,
    get_transactions,
    init_db,
    insert_transaction,
    upsert_budget,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "finance_tracker.db"
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            upsert_budget(conn, "Food & drinks", 500.0, 80)
            upsert_budget(conn, "Transport", 200.0, 90)

            assert insert_transaction(conn, "2026-07-01", "GrabFood", -25.5, "expense", "Food & drinks", "gmail", "raw")
            assert not insert_transaction(conn, "2026-07-01", "GrabFood", -25.5, "expense", "Food & drinks", "gmail", "raw")
            assert insert_transaction(conn, "2026-07-02", "Salary", 3500.0, "income", "Income", "gmail", "raw")

            summary = get_monthly_summary(conn, 7, 2026)
            assert summary["income"] == 3500.0
            assert summary["expense"] == -25.5
            assert summary["net"] == 3474.5
            assert summary["count"] == 2

            rows = get_transactions(conn, 7, 2026)
            assert len(rows) == 2
            assert get_budget(conn, "Food & drinks") == 500.0
            assert get_all_budgets(conn)["Transport"] == 200.0
            assert get_category_spend(conn, "Food & drinks", 7, 2026) == 25.5
        finally:
            conn.close()
        print("Phase 1 smoke test passed.")


if __name__ == "__main__":
    main()
