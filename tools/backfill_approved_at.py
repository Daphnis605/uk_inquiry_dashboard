"""
Backfill approved_at timestamps
================================
Sets approved_at on all evidence items where approved:true but approved_at is null.

Usage:
    python tools/backfill_approved_at.py           # write changes
    python tools/backfill_approved_at.py --dry-run # preview only, no writes
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ENRICHED_PATH = REPO_ROOT / "enriched_data.json"


def main():
    dry_run = "--dry-run" in sys.argv

    with open(ENRICHED_PATH, encoding="utf-8") as f:
        data = json.load(f)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    found = []

    for key, entry in data.items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        for i, item in enumerate(entry.get("evidence", [])):
            if item.get("approved") and not item.get("approved_at"):
                found.append((key, i, item.get("title", "(no title)")[:60]))
                if not dry_run:
                    item["approved_at"] = stamp

    if not found:
        print("Nothing to backfill — all approved items already have approved_at.")
        return

    for key, idx, title in found:
        print(f"  {'[dry-run] ' if dry_run else ''}backfill: {key}  item {idx}: {title}")

    if dry_run:
        print(f"\n{len(found)} item(s) would be updated (dry run — no changes written).")
    else:
        with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n{len(found)} item(s) updated with approved_at: {stamp}")


if __name__ == "__main__":
    main()
