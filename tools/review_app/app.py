"""
Evidence Review App
===================
A lightweight local Flask app to review and approve evidence entries
in enriched_data.json.

Usage:
    pip install flask
    python tools/review_app/app.py

Then open http://localhost:5000 in your browser.

Phase 1 (/):         Card-by-card approval queue for unapproved evidence items.
Phase 2 (/statuses): Per-recommendation status review once items are approved.
"""

import json
import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Resolve paths relative to the repo root (two levels up from this file)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENRICHED_PATH = os.path.join(REPO_ROOT, "enriched_data.json")
DATA_PATH = os.path.join(REPO_ROOT, "data.json")


def load_enriched():
    with open(ENRICHED_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_enriched(data):
    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_recommendations():
    """Return flat dict: InquiryName__N -> recommendation text."""
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    recs = {}
    for dept in data:
        for inquiry in dept.get("Inquiries", []):
            name = inquiry["InquiryName"]
            for i, rec in enumerate(inquiry.get("Recommendations", []), 1):
                recs[f"{name}__{i}"] = rec["Recommendation"]
    return recs


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@app.route("/")
def index():
    enriched = load_enriched()
    recs = load_recommendations()
    inquiry_filter = request.args.get("inquiry", "")

    # Collect entries with at least one pending (approved:false) evidence item
    pending = []
    for key, entry in enriched.items():
        if key.startswith("_"):
            continue
        inquiry_name = key.rsplit("__", 1)[0]
        if inquiry_filter and inquiry_filter != inquiry_name:
            continue
        pending_items = [
            (i, item)
            for i, item in enumerate(entry.get("evidence", []))
            if not item.get("approved")
        ]
        if pending_items:
            pending.append({
                "key": key,
                "inquiry": inquiry_name,
                "rec_text": recs.get(key, "(recommendation text not found)"),
                "evidence_status": entry.get("evidence_status", ""),
                "notes": entry.get("notes", ""),
                "pending_items": pending_items,
                "total_items": len(entry.get("evidence", [])),
            })

    # Sort by inquiry name then key
    pending.sort(key=lambda x: (x["inquiry"], x["key"]))

    # Counts for the filter bar
    all_inquiries = sorted(
        {k.rsplit("__", 1)[0] for k in enriched if not k.startswith("_")}
    )
    total_pending = sum(
        1
        for entry in enriched.values()
        if isinstance(entry, dict)
        for item in entry.get("evidence", [])
        if not item.get("approved")
    )
    total_approved = sum(
        1
        for entry in enriched.values()
        if isinstance(entry, dict)
        for item in entry.get("evidence", [])
        if item.get("approved")
    )

    return render_template(
        "index.html",
        pending=pending,
        all_inquiries=all_inquiries,
        inquiry_filter=inquiry_filter,
        total_pending=total_pending,
        total_approved=total_approved,
    )


@app.route("/approve", methods=["POST"])
def approve():
    data = request.get_json()
    key = data.get("key")
    item_index = data.get("item_index")

    enriched = load_enriched()
    entry = enriched.get(key)
    if not entry or item_index is None:
        return jsonify({"ok": False, "error": "Not found"}), 404

    items = entry.get("evidence", [])
    if not isinstance(item_index, int) or item_index < 0 or item_index >= len(items):
        return jsonify({"ok": False, "error": "Index out of range"}), 400

    items[item_index]["approved"] = True
    items[item_index]["approved_at"] = utc_now()

    save_enriched(enriched)
    return jsonify({"ok": True})


@app.route("/unapprove", methods=["POST"])
def unapprove():
    """Send an approved item back to Phase 1 by setting approved: false."""
    data = request.get_json()
    key = data.get("key")
    item_index = data.get("item_index")

    enriched = load_enriched()
    entry = enriched.get(key)
    if not entry or item_index is None:
        return jsonify({"ok": False, "error": "Not found"}), 404

    items = entry.get("evidence", [])
    if not isinstance(item_index, int) or item_index < 0 or item_index >= len(items):
        return jsonify({"ok": False, "error": "Index out of range"}), 400

    items[item_index]["approved"] = False
    items[item_index]["approved_at"] = None

    save_enriched(enriched)
    return jsonify({"ok": True})


@app.route("/approve_all", methods=["POST"])
def approve_all():
    """Bulk-approve all unapproved items, optionally filtered to one inquiry."""
    data = request.get_json()
    inquiry_filter = (data.get("inquiry") or "").strip()

    enriched = load_enriched()
    stamped = utc_now()
    count = 0

    for key, entry in enriched.items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        inquiry_name = key.rsplit("__", 1)[0]
        if inquiry_filter and inquiry_filter != inquiry_name:
            continue
        for item in entry.get("evidence", []):
            if not item.get("approved"):
                item["approved"] = True
                item["approved_at"] = stamped
                count += 1

    save_enriched(enriched)
    return jsonify({"ok": True, "count": count})


@app.route("/reject", methods=["POST"])
def reject():
    """Remove a single evidence item from a key."""
    data = request.get_json()
    key = data.get("key")
    item_index = data.get("item_index")

    enriched = load_enriched()
    entry = enriched.get(key)
    if not entry or item_index is None:
        return jsonify({"ok": False, "error": "Not found"}), 404

    items = entry.get("evidence", [])
    if not isinstance(item_index, int) or item_index < 0 or item_index >= len(items):
        return jsonify({"ok": False, "error": "Index out of range"}), 400

    removed = items.pop(item_index)

    # If no evidence remains, remove the key entirely
    if not items:
        del enriched[key]

    save_enriched(enriched)
    return jsonify({"ok": True, "removed_title": removed.get("title", "")})


@app.route("/edit", methods=["POST"])
def edit():
    """Update fields on a single evidence item."""
    data = request.get_json()
    key = data.get("key")
    item_index = data.get("item_index")

    enriched = load_enriched()
    entry = enriched.get(key)
    if not entry or item_index is None:
        return jsonify({"ok": False, "error": "Not found"}), 404

    items = entry.get("evidence", [])
    if not isinstance(item_index, int) or item_index < 0 or item_index >= len(items):
        return jsonify({"ok": False, "error": "Index out of range"}), 400

    item = items[item_index]
    allowed_fields = {"title", "url", "date", "source_type", "description", "evidence_type"}
    for field in allowed_fields:
        if field in data:
            item[field] = data[field]

    save_enriched(enriched)
    return jsonify({"ok": True})


@app.route("/set_status", methods=["POST"])
def set_status():
    """Update evidence_status for a key."""
    data = request.get_json()
    key = data.get("key")
    status = data.get("status")
    valid = {"actioned", "partial", "no_evidence_found", "not_published"}
    if status not in valid:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    enriched = load_enriched()
    if key not in enriched:
        return jsonify({"ok": False, "error": "Key not found"}), 404

    enriched[key]["evidence_status"] = status
    save_enriched(enriched)
    return jsonify({"ok": True})


@app.route("/statuses")
def statuses():
    """Phase 2: per-recommendation status review."""
    enriched = load_enriched()
    recs = load_recommendations()
    inquiry_filter = request.args.get("inquiry", "")

    rec_cards = []
    for key, entry in enriched.items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        inquiry_name = key.rsplit("__", 1)[0]
        if inquiry_filter and inquiry_filter != inquiry_name:
            continue
        approved_items = [
            {"_idx": i, **ev}
            for i, ev in enumerate(entry.get("evidence", []))
            if ev.get("approved")
        ]
        if not approved_items:
            continue
        rec_cards.append({
            "key": key,
            "inquiry": inquiry_name,
            "rec_text": recs.get(key, "(recommendation text not found)"),
            "evidence_status": entry.get("evidence_status", ""),
            "notes": entry.get("notes", ""),
            "evidence_items": approved_items,
        })

    rec_cards.sort(key=lambda x: (x["inquiry"], x["key"]))

    all_inquiries = sorted(
        {k.rsplit("__", 1)[0] for k in enriched if not k.startswith("_")}
    )
    needs_status = sum(1 for c in rec_cards if not c["evidence_status"])

    return render_template(
        "status_review.html",
        rec_cards=rec_cards,
        all_inquiries=all_inquiries,
        inquiry_filter=inquiry_filter,
        needs_status=needs_status,
    )


if __name__ == "__main__":
    import os as _os
    print(f"Repo root: {REPO_ROOT}")
    print(f"enriched_data.json: {ENRICHED_PATH}")
    app.run(debug=_os.getenv("FLASK_DEBUG", "0") == "1", port=5000)
