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

    # Disable live web search (training knowledge only — faster, cheaper)
    python scripts/research.py --no-web-search

    # Save a full audit log of every response (including no-evidence reasoning)
    python scripts/research.py --audit-log audit.jsonl

    # Use a faster/cheaper model for a first pass
    python scripts/research.py --model claude-haiku-4-5-20251001

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

Web search:
    Web search is enabled by default. Claude calls the Anthropic web search
    tool and searches the internet before answering — more likely to find recent
    or obscure URLs than training knowledge alone.
    Use --no-web-search to fall back to training knowledge only (faster, cheaper).
    Use --audit-log to save a full record for either mode.
"""

import json
import re
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

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
# Prompts
# ---------------------------------------------------------------------------
_PROMPT_BODY = """\
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
- Do not fabricate URLs — only provide URLs you have actually retrieved and confirmed exist.

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

RESEARCH_PROMPT = _PROMPT_BODY

RESEARCH_PROMPT_WEB = (
    "Search the web to find current, verifiable evidence before answering.\n\n"
    + _PROMPT_BODY
)


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


def extract_final_text(message) -> str:
    """Return the last text block from a message (works with or without tool use)."""
    last_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            last_text = block.text
    return last_text


def research_recommendation(
    client: "anthropic.Anthropic",
    rec: dict,
    model: str,
    web_search: bool = True,
) -> tuple[dict | None, str]:
    """Returns (parsed_result, raw_response_text)."""
    prompt_template = RESEARCH_PROMPT_WEB if web_search else RESEARCH_PROMPT
    prompt = prompt_template.format(
        inquiry=rec["inquiry"],
        report_date=rec["report_date"],
        rec_num=rec["rec_idx"] + 1,
        rec_text=rec["rec_text"],
        action_category=rec["action_category"],
        change_type=rec["change_type"],
    )

    kwargs: dict = {
        "model": model,
        "max_tokens": 2048 if web_search else 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if web_search:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    for attempt in range(3):
        try:
            message = client.messages.create(**kwargs)
            raw = extract_final_text(message)
            return parse_response(raw), raw
        except Exception as e:
            err = str(e)
            if "rate_limit_error" in err and attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"  Rate limit hit — waiting {wait}s before retry {attempt + 2}/3…", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"  API error: {e}", file=sys.stderr)
                return None, ""
    return None, ""


def write_audit_entry(audit_file: IO, rec: dict, result: dict | None, raw: str) -> None:
    """Append one JSONL entry to the audit log."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "key": rec["key"],
        "inquiry": rec["inquiry"],
        "rec_num": rec["rec_idx"] + 1,
        "rec_text": rec["rec_text"],
        "outcome": (result or {}).get("evidence_status", "parse_error"),
        "notes": (result or {}).get("notes", ""),
        "evidence_count": len((result or {}).get("evidence", [])),
        "raw_response": raw,
    }
    audit_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    audit_file.flush()


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
        "--no-web-search",
        action="store_true",
        help="Disable live web search and use training knowledge only (faster, cheaper, less accurate)",
    )
    parser.add_argument(
        "--audit-log",
        metavar="FILE",
        help="Path to a JSONL file to append full responses to (for auditing no-evidence conclusions)",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        help="Claude model ID (default: claude-haiku-4-5-20251001)",
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

    use_web_search = not args.no_web_search
    mode = "web search" if use_web_search else "training knowledge only"
    batch = unevidenced[: args.limit]
    print(f"Researching {len(batch)} (limit={args.limit}, model={args.model}, mode={mode})\n", file=sys.stderr)

    audit_file = open(args.audit_log, "a", encoding="utf-8") if args.audit_log else None
    if audit_file:
        print(f"Audit log: {args.audit_log}", file=sys.stderr)

    proposals: dict = {}
    found = 0

    try:
        for i, rec in enumerate(batch):
            label = f"[{i + 1}/{len(batch)}] {rec['inquiry']} rec {rec['rec_idx'] + 1}"
            print(label, file=sys.stderr)

            result, raw = research_recommendation(client, rec, args.model, web_search=use_web_search)

            if audit_file:
                write_audit_entry(audit_file, rec, result, raw)

            if result and result.get("evidence_status") in ("actioned", "partial") and result.get("evidence"):
                for ev in result["evidence"]:
                    ev["approved"] = False
                    ev["approved_at"] = None
                    ev.setdefault("evidence_type", "partial")  # fallback if model omits it
                proposals[rec["key"]] = result
                found += 1
                url = result["evidence"][0].get("url", "")
                notes = result.get("notes", "")
                print(f"  → {result['evidence_status']}: {url}", file=sys.stderr)
                if notes:
                    print(f"     {notes}", file=sys.stderr)
            else:
                notes = (result or {}).get("notes", "")
                status = (result or {}).get("evidence_status", "no_response")
                print(f"  → {status}", file=sys.stderr)
                if notes:
                    for line in notes.splitlines():
                        print(f"     {line}", file=sys.stderr)

            if i < len(batch) - 1:
                time.sleep(5 if use_web_search else 0.3)  # web search responses are larger
    finally:
        if audit_file:
            audit_file.close()

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
