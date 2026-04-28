"""
Evidence Review App
===================
A lightweight local Flask app to review and approve evidence entries
in enriched_data.json.

Usage:
    pip install flask
    python tools/review_app/app.py

Then open http://localhost:5000 in your browser.

Entries with approved:false are shown for review. Approving an entry
sets approved:true and saves immediately to enriched_data.json.
"""

import json
import os
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


@app.route("/")
def index():
    enriched = load_enriched()
    recs = load_recommendations()
    inquiry_filter = request.args.get("inquiry", "")

    # Build flat list of cards — one card per unapproved evidence item
    cards = []
    for key, entry in enriched.items():
        if key.startswith("_"):
            continue
        inquiry_name = key.rsplit("__", 1)[0]
        if inquiry_filter and inquiry_filter != inquiry_name:
            continue
        for i, item in enumerate(entry.get("evidence", [])):
            if not item.get("approved"):
                cards.append({
                    "key": key,
                    "inquiry": inquiry_name,
                    "rec_text": recs.get(key, "(recommendation text not found)"),
                    "evidence_status": entry.get("evidence_status", ""),
                    "notes": entry.get("notes", ""),
                    "item_index": i,
                    "item": item,
                })

    cards.sort(key=lambda x: (x["inquiry"], x["key"]))

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
        cards=cards,
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

    # If all items are now approved, update evidence_status if still partial
    if all(i.get("approved") for i in items):
        if entry.get("evidence_status") == "partial":
            pass  # leave as partial — status reflects implementation, not review

    save_enriched(enriched)
    return jsonify({"ok": True})


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


if __name__ == "__main__":
    import os as _os
    print(f"Repo root: {REPO_ROOT}")
    print(f"enriched_data.json: {ENRICHED_PATH}")
    app.run(debug=_os.getenv("FLASK_DEBUG", "0") == "1", port=5000)
