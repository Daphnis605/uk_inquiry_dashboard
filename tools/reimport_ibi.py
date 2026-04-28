"""
Reimport IBI evidence from infected_blood_inquiry_raw_data.csv
==============================================================
Replaces existing Infected Blood Inquiry entries in enriched_data.json
with structured evidence items — one item per data column where content exists:

  1. Government Response  — formal acceptance position (always present)
  2. Actions Taken        — concrete steps taken (present in ~40% of recs)
  3. May 2025 Update      — government's progress narrative (always present)

Run from the repo root:
    python tools/reimport_ibi.py
"""

import csv
import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENRICHED_PATH = os.path.join(REPO_ROOT, "enriched_data.json")
CSV_PATH = os.path.join(REPO_ROOT, "infected_blood_inquiry_raw_data.csv")
DATA_PATH = os.path.join(REPO_ROOT, "data.json")
TRACKER_URL = "https://ibinquiry.dac.grid.civilservice.gov.uk/"

# CSV row index (0-based) → enriched_data.json rec index (1-based key suffix)
# Most map sequentially; rows 50-52 are sub-recs that collapse into rec 50.
def csv_row_to_rec_index(csv_idx):
    """Return 1-based rec index for a 0-based CSV row index."""
    if csv_idx <= 49:
        return csv_idx + 1          # rows 0-49  → recs 1-50
    elif csv_idx <= 52:
        return 50                   # rows 50-52 → rec 50 (11b/11c/11d)
    else:
        return csv_idx - 2          # rows 53-57 → recs 51-55


def make_evidence_items(row, sub_label):
    """Build evidence items from one CSV row."""
    gov_response = row["Government Response"].strip()
    actions = row["Actions"].strip()
    may_update = row["May 2025 Update"].strip()
    items = []

    # Item 1 — Government position (always)
    if gov_response:
        items.append({
            "title": f"Government position: {gov_response} — IBI Tracker",
            "url": TRACKER_URL,
            "source_type": "official_report",
            "date": "2025-05",
            "description": gov_response,
            "approved": False,
            "approved_at": None,
            "submitted_by": None,
        })

    # Item 2 — Actions taken (only if the field is populated)
    if actions:
        items.append({
            "title": f"Actions taken — IBI Tracker (May 2025)",
            "url": TRACKER_URL,
            "source_type": "official_report",
            "date": "2025-05",
            "description": actions,
            "approved": False,
            "approved_at": None,
            "submitted_by": None,
        })

    # Item 3 — May 2025 progress update (always)
    if may_update:
        items.append({
            "title": f"May 2025 progress update — IBI Tracker",
            "url": TRACKER_URL,
            "source_type": "official_report",
            "date": "2025-05",
            "description": may_update,
            "approved": False,
            "approved_at": None,
            "submitted_by": None,
        })

    return items


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(ENRICHED_PATH, encoding="utf-8") as f:
        enriched = json.load(f)

    # Remove existing IBI entries
    ibi_keys = [k for k in enriched if k.startswith("Infected Blood Inquiry")]
    for k in ibi_keys:
        del enriched[k]
    print(f"Removed {len(ibi_keys)} existing IBI entries")

    # Group CSV rows by target rec index
    rec_groups = {}  # rec_index -> list of (row, sub_label)
    for i, row in enumerate(rows):
        rec_idx = csv_row_to_rec_index(i)
        sub_label = row["Sub-recommendation"].strip()
        rec_groups.setdefault(rec_idx, []).append((row, sub_label))

    # Build new enriched entries
    added = 0
    for rec_idx in sorted(rec_groups.keys()):
        key = f"Infected Blood Inquiry__{rec_idx}"
        group = rec_groups[rec_idx]

        # Aggregate evidence items from all CSV rows for this rec
        all_items = []
        sub_labels = [sub for _, sub in group]
        for row, sub_label in group:
            # If multiple rows collapse into one rec, prefix titles with sub-rec label
            prefix = f"[{sub_label}] " if len(group) > 1 else ""
            items = make_evidence_items(row, sub_label)
            if len(group) > 1:
                for item in items:
                    item["title"] = prefix + item["title"]
            all_items.extend(items)

        # Determine evidence_status: partial if actions exist, else partial by default
        has_actions = any(row["Actions"].strip() for row, _ in group)
        gov_response = group[0][0]["Government Response"].strip()

        enriched[key] = {
            "evidence_status": "partial",  # reviewer will confirm or change
            "evidence": all_items,
            "notes": (
                f"Source: IBI implementation tracker (May 2025). "
                f"Government position: {gov_response}. "
                + (f"Sub-recs: {', '.join(sub_labels)}." if len(group) > 1 else "")
            ).strip(),
        }
        added += 1

    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    total_items = sum(len(v["evidence"]) for v in enriched.values() if isinstance(v, dict))
    ibi_items = sum(
        len(enriched[f"Infected Blood Inquiry__{i}"]["evidence"])
        for i in range(1, added + 1)
        if f"Infected Blood Inquiry__{i}" in enriched
    )
    print(f"Added {added} IBI entries with {ibi_items} evidence items total")
    print(f"All items have approved:false — run review app to approve")


if __name__ == "__main__":
    main()
