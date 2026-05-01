#!/usr/bin/env python3
"""
AI-assisted evidence research for UK Inquiry Dashboard.

For each recommendation that has no approved evidence, asks Claude to find
a specific URL showing that recommendation was implemented.  All proposals
are written with approved=false and must be reviewed by the maintainer
before appearing on the live dashboard.

Usage:
    # Research up to 10 recommendations (default)
    python scripts/research.py

    # Filter to a single inquiry
    python scripts/research.py --inquiry "Manchester Arena"

    # Larger batch — check cost estimate first
    python scripts/research.py --limit 50

    # Preview without writing to enriched_data.json
    python scripts/research.py --dry-run

    # Use a faster/cheaper model for a first pass
    python scripts/research.py --model claude-haiku-4-5-20251001

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
"""

import json
import re
import sys
import time
import argparse
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
DATA_JSON = ROOT / "data.json"
ENRICHED_JSON = ROOT / "enriched_data.json"

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
RESEARCH_PROMPT = """\
You are helping research whether a UK public inquiry recommendation has been implemented by the government.

Inquiry: {inquiry}
Report published: {report_date}
Recommendation #{rec_num}: {rec_text}
Category: {action_category} | Change type: {change_type}

Task: Determine whether this specific recommendation was implemented.
If it was, provide ONE piece of primary evidence — a direct URL to:
  - Legislation (legislation.gov.uk)
  - An official government report (gov.uk, parliament.uk, nao.org.uk, etc.)
  - A press release or ministerial statement (gov.uk)
  - A parliamentary record (hansard.parliament.uk)

Rules:
- "Acceptance" or "welcome" by government is NOT implementation evidence.
- Progress reports or reviews are NOT sufficient unless they confirm implementation.
- If you cannot identify a specific, verifiable URL, respond with evidence_status "no_evidence_found".
- Do not guess or fabricate URLs.

Respond in JSON only (no markdown fences):
{{
  "evidence_status": "actioned" | "partial" | "no_evidence_found",
  "evidence": [
    {{
      "title": "exact title of the source",
      "url": "https://...",
      "source_type": "legislation" | "press_release" | "official_report" | "parliamentary_record" | "news_article",
      "date": "YYYY-MM-DD or null",
      "description": "1-2 sentences explaining how this evidences the recommendation being implemented",
      "evidence_type": "complete" | "partial"
    }}
  ],
  "notes": "brief research notes explaining your reasoning"
}}

evidence_type rules:
- "complete" — recommendation is fully implemented (law enacted, scheme operational, guidance published and in force)
- "partial"  — progress is visible but implementation is incomplete, paused, or only promised

If not found:
{{"evidence_status": "no_evidence_found", "evidence": [], "notes": "reason"}}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def build_enriched_map(enriched: dict) -> dict:
    return {k: v for k, v in enriched.items() if not k.startswith("_")}


def get_unevidenced(data: list, enriched_map: dict) -> list:
    """Return all recommendations that have no approved evidence."""
    rows = []
    for dept in data:
        for inquiry in dept.get("Inquiries", []):
            name = inquiry["InquiryName"]
            for idx, rec in enumerate(inquiry.get("Recommendations", [])):
                key = f"{name}__{idx}"
                existing = enriched_map.get(key)
                has_approved = (
                    existing
                    and existing.get("evidence")
                    and any(ev.get("approved") for ev in existing["evidence"])
                )
                if not has_approved:
                    rows.append({
                        "key": key,
                        "inquiry": name,
                        "report_date": inquiry.get("ReportDate", "unknown"),
                        "rec_idx": idx,
                        "rec_text": rec.get("Recommendation", ""),
                        "action_category": rec.get("ActionCategory", ""),
                        "change_type": rec.get("ChangeType", ""),
                    })
    return rows


def parse_response(text: str) -> dict | None:
    """Extract JSON from Claude's response."""
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object anywhere in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def research_recommendation(client: "anthropic.Anthropic", rec: dict, model: str) -> dict | None:
    prompt = RESEARCH_PROMPT.format(
        inquiry=rec["inquiry"],
        report_date=rec["report_date"],
        rec_num=rec["rec_idx"] + 1,
        rec_text=rec["rec_text"],
        action_category=rec["action_category"],
        change_type=rec["change_type"],
    )
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_response(message.content[0].text)
    except Exception as e:
        print(f"  API error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI-assisted evidence research for UK Inquiry Dashboard recommendations."
    )
    parser.add_argument(
        "--inquiry",
        metavar="NAME",
        help="Filter to inquiries whose name contains this string (case-insensitive)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of recommendations to research in this run (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposals as JSON without writing enriched_data.json",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model ID (default: claude-sonnet-4-6)",
    )
    args = parser.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    data = load_json(DATA_JSON)
    enriched = load_json(ENRICHED_JSON)
    enriched_map = build_enriched_map(enriched)
    unevidenced = get_unevidenced(data, enriched_map)

    if args.inquiry:
        unevidenced = [r for r in unevidenced if args.inquiry.lower() in r["inquiry"].lower()]

    total = len(unevidenced)
    print(f"{total} unevidenced recommendations", file=sys.stderr)

    batch = unevidenced[: args.limit]
    print(f"Researching {len(batch)} (limit={args.limit}, model={args.model})\n", file=sys.stderr)

    proposals: dict = {}
    found = 0

    for i, rec in enumerate(batch):
        label = f"[{i + 1}/{len(batch)}] {rec['inquiry']} rec {rec['rec_idx'] + 1}"
        print(label, file=sys.stderr)

        result = research_recommendation(client, rec, args.model)

        if result and result.get("evidence_status") in ("actioned", "partial") and result.get("evidence"):
            for ev in result["evidence"]:
                ev["approved"] = False
                ev["approved_at"] = None
                ev.setdefault("evidence_type", "partial")  # fallback if model omits it
            proposals[rec["key"]] = result
            found += 1
            print(f"  → {result['evidence_status']}: {result['evidence'][0].get('url', '')}", file=sys.stderr)
        else:
            notes = (result or {}).get("notes", "")
            print(f"  → no evidence found{': ' + notes if notes else ''}", file=sys.stderr)

        if i < len(batch) - 1:
            time.sleep(0.3)  # stay within rate limits

    print(f"\n{found}/{len(batch)} proposals found", file=sys.stderr)

    if not proposals:
        print("Nothing to write.", file=sys.stderr)
        return

    if args.dry_run:
        print(json.dumps(proposals, indent=2, ensure_ascii=False))
        return

    # Merge proposals into enriched_data.json
    # Never overwrite existing approved evidence; only append new unapproved items
    new_keys = 0
    new_items = 0
    for key, proposal in proposals.items():
        if key not in enriched:
            enriched[key] = proposal
            new_keys += 1
            new_items += len(proposal.get("evidence", []))
        else:
            existing_urls = {ev.get("url") for ev in enriched[key].get("evidence", [])}
            for ev in proposal.get("evidence", []):
                if ev.get("url") not in existing_urls:
                    enriched[key].setdefault("evidence", []).append(ev)
                    new_items += 1

    ENRICHED_JSON.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Written to enriched_data.json: {new_keys} new keys, {new_items} new evidence items"
        f" (all approved=false — review before merging)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
