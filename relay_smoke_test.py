"""Smoke test for the Flask relay API."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["RELAY_SECRET"] = "test-secret"

from relay.app import app  # noqa: E402
from relay.db import init_db, get_pending, mark_processed, insert_notification  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "relay.db"
        init_db(db_path)
        insert_notification('{"app":"PublicBank","text":"Payment of RM 25.00 to Grab"}', db_path)

        client = app.test_client()
        app.config["TESTING"] = True
        headers = {"X-Secret": "test-secret"}

        assert client.get("/health").status_code == 200
        assert client.post("/notify", json={"app": "PublicBank", "text": "Payment of RM 25.00 to Grab"}, headers=headers).status_code == 201
        assert client.post("/notify", json={"app": "PublicBank"}, headers=headers).status_code == 400
        assert client.get("/pending", headers=headers).status_code == 200
        pending_resp = client.get("/pending", headers=headers)
        assert pending_resp.status_code == 200
        items = pending_resp.get_json()["items"]
        assert len(items) >= 1
        first_id = items[0]["id"]
        assert client.post("/processed", json={"ids": [first_id]}, headers=headers).status_code == 200
        assert client.post("/processed", json={"ids": "bad"}, headers=headers).status_code == 400

        with app.app_context():
            pass

        print("Relay smoke test passed.")


if __name__ == "__main__":
    main()
