"""Smoke test for the categoriser rule engine."""

from __future__ import annotations

from categoriser import categorise


SAMPLES = [
    ("Monthly salary from employer", "Salary credited to bank account", ("Income", "income")),
    ("gaji masuk", "Payment received RM 3,500.00", ("Income", "income")),
    ("Shopee Pay Later installment reminder", "Your payment is due", ("BNPL repayment", "expense")),
    ("SPayLater due notice", "Instalment due on 10/07/2026", ("BNPL repayment", "expense")),
    ("GrabFood order", "Paid to GrabFood at 7-Eleven", ("Food & drinks", "expense")),
    ("teALive receipt", "Tealive RM 12.50", ("Food & drinks", "expense")),
    ("myNEWS breakfast", "Purchase at MYNEWS.com", ("Food & drinks", "expense")),
    ("99 Speedmart essentials", "99 speedmart market purchase", ("Food & drinks", "expense")),
    ("GrabCar trip", "Payment of RM 18.00 to Grab", ("Transport", "expense")),
    ("Toll payment", "Touch 'n Go highway toll", ("Transport", "expense")),
    ("Shopee order confirmed", "Item shipped from seller", ("Shopping", "expense")),
    ("Lazada checkout", "Order confirmed by Lazada", ("Shopping", "expense")),
    ("Unifi bill", "Monthly broadband payment", ("Bills & utilities", "expense")),
    ("Netflix renewal", "Subscription charge on card", ("Subscriptions", "expense")),
    ("Top up wallet", "Touch n Go reload RM 50.00", ("E-wallet top-up", "expense")),
    ("Fixed deposit proceeds", "ASB investment credited", ("Savings", "income")),
    ("Random merchant", "Partial match: grabby is not a delivery brand", ("Uncategorised", "expense")),
]


def main() -> None:
    failures: list[str] = []
    for idx, (description, raw_text, expected) in enumerate(SAMPLES, 1):
        result = categorise(description, raw_text)
        if result != expected:
            failures.append(
                f"{idx}. expected {expected} but got {result} for description={description!r}, raw_text={raw_text!r}"
            )

    if failures:
        print("Phase 2 smoke test failed:")
        for failure in failures:
            print(failure)
        raise SystemExit(1)

    print(f"Phase 2 smoke test passed for {len(SAMPLES)} samples.")


if __name__ == "__main__":
    main()
