"""Rule-based categoriser for personal finance transactions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryRule:
    category: str
    transaction_type: str
    keywords: tuple[str, ...]


RULES: tuple[CategoryRule, ...] = (
    CategoryRule(
        category="Income",
        transaction_type="income",
        keywords=(
            "salary",
            "gaji",
            "payment received",
            "credited",
            "bank in",
            "transfer in",
        ),
    ),
    CategoryRule(
        category="BNPL repayment",
        transaction_type="expense",
        keywords=(
            "shopee pay later",
            "instalment",
            "installment",
            "spaylater",
            "bnpl",
            "repayment due",
            "due payment",
        ),
    ),
    CategoryRule(
        category="Food & drinks",
        transaction_type="expense",
        keywords=(
            "grabfood",
            "foodpanda",
            "mcdonalds",
            "mcdonald's",
            "kfc",
            "pizza",
            "tealive",
            "starbucks",
            "restaurant",
            "mamak",
            "mynews",
            "99 speedmart",
        ),
    ),
    CategoryRule(
        category="Transport",
        transaction_type="expense",
        keywords=(
            "grabcar",
            "grabbike",
            "grab",
            "toll",
            "parking",
            "touch n go highway",
            "commuter",
            "mrt",
            "lrt",
            "touch 'n go",
            "tng",
        ),
    ),
    CategoryRule(
        category="Shopping",
        transaction_type="expense",
        keywords=(
            "shopee",
            "lazada",
            "order confirmed",
            "item shipped",
            "99 speedmart",
            "mynews",
        ),
    ),
    CategoryRule(
        category="Bills & utilities",
        transaction_type="expense",
        keywords=(
            "unifi",
            "tnb",
            "tenaga",
            "air selangor",
            "telekom",
            "maxis",
            "celcom",
            "digi",
            "yes 4g",
            "utility",
            "broadband",
            "water bill",
        ),
    ),
    CategoryRule(
        category="Subscriptions",
        transaction_type="expense",
        keywords=(
            "netflix",
            "spotify",
            "youtube premium",
            "apple",
            "google play",
            "adobe",
            "subscription",
            "renewal",
        ),
    ),
    CategoryRule(
        category="E-wallet top-up",
        transaction_type="expense",
        keywords=(
            "reload",
            "top-up",
            "top up",
            "wallet credit",
            "ewallet credit",
            "e-wallet credit",
            "touch n go reload",
            "grabpay top up",
        ),
    ),
    CategoryRule(
        category="Savings",
        transaction_type="income",
        keywords=(
            "savings",
            "fixed deposit",
            "fd ",
            "asb",
            "amanah saham",
            "tabung haji",
            "investment",
            "invest",
        ),
    ),
)


def categorise(description: str, raw_text: str) -> tuple[str, str]:
    """Return (category, transaction_type) using first-match-wins rules."""
    haystack = f"{description} {raw_text}".lower()
    if _matches_any(haystack, ("savings", "fixed deposit", "fd ", "asb", "amanah saham", "tabung haji", "investment", "invest")):
        return "Savings", "income"
    for rule in RULES:
        if _matches_any(haystack, rule.keywords):
            return rule.category, rule.transaction_type
    return "Uncategorised", "expense"


def _matches_any(haystack: str, keywords: tuple[str, ...]) -> bool:
    return any(_matches_keyword(haystack, keyword) for keyword in keywords)


def _matches_keyword(haystack: str, keyword: str) -> bool:
    needle = keyword.lower().strip()
    if not needle:
        return False
    if any(ch.isalnum() for ch in needle):
        if " " in needle:
            return needle in haystack
        import re

        pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
        return re.search(pattern, haystack) is not None
    return needle in haystack
