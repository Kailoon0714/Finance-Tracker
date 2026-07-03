"""Streamlit dashboard for the personal finance tracker."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from contextlib import closing

import pandas as pd
import plotly.express as px
import streamlit as st

from db import get_connection, get_all_budgets, get_category_spend, get_monthly_summary, get_transactions
from demo_data import seed_demo_data


DB_PATH = Path("finance_tracker.db")
CATEGORIES = [
    "Food & drinks",
    "Transport",
    "Shopping",
    "Bills & utilities",
    "E-wallet top-up",
    "Subscriptions",
    "BNPL repayment",
    "Income",
    "Savings",
    "Uncategorised",
]


st.set_page_config(page_title="Personal Finance Tracker", layout="wide")
st.title("Personal Finance Tracker")


def format_rm(value: float) -> str:
    return f"RM {value:,.2f}"


def month_options() -> list[tuple[int, int, str]]:
    today = date.today()
    options = []
    for offset in range(5, -1, -1):
        month = today.month - offset
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        label = datetime(year, month, 1).strftime("%B %Y")
        options.append((year, month, label))
    return options


@st.cache_data(show_spinner=False)
def load_month_summary(db_path: str, month: int, year: int):
    with get_connection(db_path) as conn:
        return get_monthly_summary(conn, month, year)


@st.cache_data(show_spinner=False)
def load_transactions(db_path: str, month: int, year: int):
    with get_connection(db_path) as conn:
        rows = get_transactions(conn, month, year)
        return [dict(row) for row in rows]


@st.cache_data(show_spinner=False)
def load_budgets(db_path: str):
    with get_connection(db_path) as conn:
        return get_all_budgets(conn)


@st.cache_data(show_spinner=False)
def load_spend_by_category(db_path: str, month: int, year: int):
    with get_connection(db_path) as conn:
        rows = []
        budgets = get_all_budgets(conn)
        cur = conn.execute(
            """
            SELECT category, COALESCE(SUM(amount), 0) AS spend
            FROM transactions
            WHERE date LIKE ?
              AND amount < 0
            GROUP BY category
            ORDER BY ABS(SUM(amount)) DESC
            """,
            (f"{year:04d}-{month:02d}-%",),
        )
        for row in cur.fetchall():
            category = row["category"]
            spend = abs(float(row["spend"]))
            budget = budgets.get(category)
            rows.append({"category": category, "spend": spend, "budget": budget, "over_budget": budget is not None and spend > budget})
        return rows


@st.cache_data(show_spinner=False)
def load_trend_data(db_path: str):
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT substr(date, 1, 7) AS month_key,
                   COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS income,
                   COALESCE(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END), 0) AS expense
            FROM transactions
            GROUP BY substr(date, 1, 7)
            ORDER BY month_key DESC
            LIMIT 6
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        rows.reverse()
        return rows


def clear_cache() -> None:
    st.cache_data.clear()
    st.rerun()


if "seeded" not in st.session_state:
    seed_demo_data(DB_PATH)
    st.session_state["seeded"] = True

with st.sidebar:
    st.header("Controls")
    month_year = month_options()
    labels = [label for _, _, label in month_year]
    selected_label = st.selectbox("Month / Year", labels, index=len(labels) - 1)
    selected_year, selected_month = next((y, m) for y, m, label in month_year if label == selected_label)

    if st.button("Refresh"):
        clear_cache()

    st.subheader("Budgets")
    with get_connection(DB_PATH) as conn:
        for category in CATEGORIES:
            current = get_all_budgets(conn).get(category, 0.0)
            budget_value = st.number_input(category, min_value=0.0, step=10.0, value=float(current), format="%.2f", key=f"budget_{category}")
            if st.button(f"Save {category}", key=f"save_{category}"):
                upsert_budget(conn, category, budget_value, 80)
                st.cache_data.clear()
                st.success(f"Saved {category}")

summary = load_month_summary(str(DB_PATH), selected_month, selected_year)
transactions = load_transactions(str(DB_PATH), selected_month, selected_year)
budgets = load_budgets(str(DB_PATH))
spend_rows = load_spend_by_category(str(DB_PATH), selected_month, selected_year)
trend_rows = load_trend_data(str(DB_PATH))

metric_cols = st.columns(4)
metric_cols[0].metric("Total income", format_rm(summary["income"]))
metric_cols[1].metric("Total expenses", format_rm(abs(summary["expense"])))
metric_cols[2].metric("Net savings", format_rm(summary["net"]))
metric_cols[3].metric("Transaction count", f"{summary['count']}")

left, right = st.columns([1.2, 1])

with left:
    st.subheader("Category Breakdown")
    if spend_rows:
        df_spend = pd.DataFrame(spend_rows)
        df_spend["display"] = df_spend["spend"].map(format_rm)
        df_spend["color"] = df_spend["over_budget"].map({True: "Over budget", False: "Within budget"})
        fig = px.bar(
            df_spend,
            x="spend",
            y="category",
            orientation="h",
            color="color",
            color_discrete_map={"Over budget": "#d62728", "Within budget": "#1f77b4"},
            text="display",
        )
        fig.update_layout(showlegend=False, xaxis_title="RM", yaxis_title="")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No expense data for the selected month.")

with right:
    st.subheader("Trend Chart")
    if trend_rows:
        df_trend = pd.DataFrame(trend_rows)
        fig = px.line(df_trend, x="month_key", y=["income", "expense"], markers=True)
        fig.update_layout(xaxis_title="Month", yaxis_title="RM")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No trend data available yet.")

st.subheader("Transaction Table")
df = pd.DataFrame(transactions)
if not df.empty:
    category_filter = st.multiselect("Filter by category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))
    type_filter = st.multiselect("Filter by type", sorted(df["type"].unique()), default=sorted(df["type"].unique()))
    df = df[df["category"].isin(category_filter) & df["type"].isin(type_filter)]
    sort_col = st.selectbox("Sort by", ["date", "amount"], index=0)
    ascending = st.checkbox("Ascending", value=False)
    df = df.sort_values(by=sort_col, ascending=ascending)
    df_display = df[["date", "description", "category", "type", "amount"]].copy()
    df_display["amount"] = df_display["amount"].map(format_rm)
    st.dataframe(df_display, width="stretch", hide_index=True)
else:
    st.info("No transactions found for the selected month.")

    st.subheader("Budget Progress")
    if budgets:
        with closing(get_connection(DB_PATH)) as conn:
            for category, budget in budgets.items():
                spend = get_category_spend(conn, category, selected_month, selected_year)
                pct = 0 if budget == 0 else spend / budget * 100
                st.write(f"**{category}** - {format_rm(spend)} spent of {format_rm(budget)} budget ({pct:.0f}%)")
                st.progress(min(pct / 100, 1.0), text=f"{category}: {pct:.0f}%")
    else:
        st.info("No budgets have been set yet.")
