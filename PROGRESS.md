# Progress

## Phase 1
- Built: SQLite helper module (`db.py`) with table creation, insert/query helpers, budget helpers, and category spend helpers.
- Built: Gmail parser module (`gmail_parser.py`) with OAuth desktop auth, Gmail fetch logic, and email parsing helpers.
- Built: Smoke test script (`phase1_smoke_test.py`) to verify database behavior locally.
- Tested: `phase1_smoke_test.py` passed on Windows; verified table creation, duplicate protection, monthly summary, budget upsert/query, and category spend calculation.
- Tested: `py_compile` passed for `db.py`, `gmail_parser.py`, and `phase1_smoke_test.py`; parser sanity check passed for Gmail query building and generic parsing.
- Tested: Gmail OAuth completed successfully and token cached in `token.json`.
- Tested: Live Gmail fetch returned 0 matching messages in the last 6 hours, and the full Phase 1 orchestrator returned `{'fetched': 0, 'inserted': 0, 'skipped': 0}` cleanly.
- Next: Move to Phase 2 and build the categoriser rule engine.

## Phase 2
- Built: `categoriser.py` with the architecture document keyword mapping plus Malaysia-specific aliases and safer keyword matching.
- Built: `phase2_smoke_test.py` with 17 sample strings spanning income, BNPL, food, transport, shopping, bills, subscriptions, top-up, savings, uncategorised, mixed case, and partial-match edge cases.
- Tested: `phase2_smoke_test.py` passed on Windows for all 17 samples.
- Next: Move to Phase 3 and build the Streamlit dashboard.

## Phase 3
- Built: `dashboard.py` Streamlit app with month/year controls, editable budgets, top metric cards, category breakdown chart, 6-month trend chart, transaction table, and budget progress panel.
- Built: `demo_data.py` plus `seed_demo_data.py` to populate realistic Malaysian sample data for dashboard verification.
- Tested: Installed dashboard dependencies and seeded the database with 26 realistic transactions across 3 months and 8 budgeted categories.
- Tested: Streamlit server launched successfully and responded on `http://localhost:8501` with HTTP 200.
- Tested: Backing data verified for all dashboard panels, including monthly summaries for May, June, and July 2026, category coverage, and budget records.
- Next: Move to Phase 4 and build the Flask relay API for Railway deployment.

## Phase 4
- Built: `relay/` Flask API with `/health`, `/notify`, `/pending`, and `/processed` endpoints plus SQLite queue helpers.
- Built: `relay/Procfile` and `relay/requirements.txt` for Railway deployment.
- Built: `relay_smoke_test.py` covering auth, notification insert, pending fetch, processed updates, and error handling.
- Tested: `relay_smoke_test.py` passed locally; `py_compile` passed for `relay/app.py`, `relay/db.py`, and `relay_smoke_test.py`.
- Next: Deploy the relay as a separate Railway service and wire the laptop poller in Phase 5.
