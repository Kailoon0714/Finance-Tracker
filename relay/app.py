"""Flask relay API for MacroDroid notification ingestion."""

from __future__ import annotations

import json
import os
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request

from .db import DEFAULT_DB_PATH, init_db, insert_notification, get_pending, mark_processed


app = Flask(__name__)
RELAY_SECRET = os.getenv("RELAY_SECRET", "")
RELAY_DB_PATH = Path(os.getenv("RELAY_DB_PATH", str(DEFAULT_DB_PATH)))

init_db(RELAY_DB_PATH)


def require_secret(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not RELAY_SECRET:
            return jsonify({"error": "RELAY_SECRET not configured"}), 500
        if request.headers.get("X-Secret") != RELAY_SECRET:
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)

    return wrapper


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/notify")
@require_secret
def notify():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    if not text:
        return jsonify({"error": "missing text"}), 400
    record_id = insert_notification(json.dumps(payload, ensure_ascii=False), RELAY_DB_PATH)
    return jsonify({"id": record_id}), 201


@app.get("/pending")
@require_secret
def pending():
    limit = min(int(request.args.get("limit", 50)), 200)
    return jsonify({"items": get_pending(limit=limit, db_path=RELAY_DB_PATH)}), 200


@app.post("/processed")
@require_secret
def processed():
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    if not isinstance(ids, list):
        return jsonify({"error": "ids must be a list"}), 400
    processed_count = mark_processed([int(i) for i in ids], RELAY_DB_PATH)
    return jsonify({"updated": processed_count}), 200

