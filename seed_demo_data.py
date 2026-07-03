"""Seed realistic demo transactions and budgets for dashboard testing."""

from __future__ import annotations

from dashboard import seed_demo_data, DB_PATH


def main() -> None:
    seed_demo_data(DB_PATH)
    print("Demo data seeded.")


if __name__ == "__main__":
    main()

