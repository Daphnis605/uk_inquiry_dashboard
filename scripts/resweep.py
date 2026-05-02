#!/usr/bin/env python3
"""
Monthly re-sweep — checks for new evidence on recommendations that previously
returned no evidence, and checks whether partial implementations are now complete.

Run this monthly (or after major news events) to keep the dashboard up to date.

Usage:
    # Preview what would be re-checked (no API calls)
    python scripts/resweep.py --list

    # Full re-sweep
    python scripts/resweep.py

    # Re-sweep partial implementations only
    python scripts/resweep.py --mode partial

    # Re-sweep no-evidence recs only
    python scripts/resweep.py --mode no-evidence

    # Higher quality pass
    python scripts/resweep.py --model claude-sonnet-4-6

    # Save audit log
    python scripts/resweep.py --audit-log resweep.jsonl

What gets re-checked:
    no-evidence  Recommendations where no evidence was ever found. New laws, bodies,
                 or policies may have been introduced since the last sweep.
    partial      Recommendations where evidence was found but implementation was
                 incomplete. These are re-checked to see if they are now actioned.

Skipped:
    actioned     Already fully implemented — no need to re-check.
    (new recs)   Recommendations with no entry at all are handled by research.py /
                 batch_research.py, not this script.

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
"""

import json
import subprocess
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RESEARCH_SCRIPT = ROOT / "scripts" / "research.py"
DATA_JSON = ROOT / "data.json"
ENRICHED_JSON = ROOT / "enriched_data.json"

DEFAULT_SKIP = ["Manchester Arena", "Grenfell Tower", "Infected Blood"]
DEFAULT_INTER_INQUIRY_PAUSE = 120


def load_resweep_targets(mode: str, skip_names: list[str]) -> dict[str, dict]:
    """
    Returns {inquiry_name: {"no_evidence": N, "partial": N}} for inquiries
    that have recs matching the requested mode.
    """
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    enriched = json.loads(ENRICHED_JSON.read_text(encoding="utf-8"))

    targets: dict[str, dict] = {}

    for dept in data:
        for inquiry in dept.get("Inquiries", []):
            name = inquiry["InquiryName"]
            if any(s.lower() in name.lower() for s in skip_names if s):
                continue

            no_evidence_count = 0
            partial_count = 0

            for idx, _ in enumerate(inquiry.get("Recommendations", [])):
                key = f"{name}__{idx}"
                entry = enriched.get(key)
                if not entry or not isinstance(entry, dict):
                    continue
                status = entry.get("evidence_status", "")
                has_approved = any(
                    ev.get("approved") for ev in entry.get("evidence", [])
                )
                if status == "no_evidence_found" and not has_approved:
                    no_evidence_count += 1
                elif status == "partial" and has_approved:
                    partial_count += 1

            if mode in ("no-evidence", "all") and no_evidence_count:
                targets.setdefault(name, {"no_evidence": 0, "partial": 0})
                targets[name]["no_evidence"] = no_evidence_count
            if mode in ("partial", "all") and partial_count:
                targets.setdefault(name, {"no_evidence": 0, "partial": 0})
                targets[name]["partial"] = partial_count

    return targets


def run_inquiry(
    name: str,
    *,
    include_partial: bool,
    model: str,
    audit_log: str | None,
    limit: int,
) -> int:
    """Run research.py for one inquiry. Returns process returncode."""
    cmd = [
        sys.executable, str(RESEARCH_SCRIPT),
        "--inquiry", name,
        "--limit", str(limit),
        "--model", model,
    ]
    if include_partial:
        cmd.append("--include-partial")
    if audit_log:
        cmd += ["--audit-log", audit_log]

    proc = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
    )
    for line in proc.stderr:
        sys.stderr.write(line)
        sys.stderr.flush()
    proc.wait()
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monthly re-sweep for UK Inquiry Dashboard."
    )
    parser.add_argument(
        "--mode",
        choices=["all", "partial", "no-evidence"],
        default="all",
        help="Which recs to re-check (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Preview targets without making any API calls",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        help="Claude model ID (default: claude-haiku-4-5-20251001)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        metavar="N",
        help="Max recs to research per inquiry per run (default: 50)",
    )
    parser.add_argument(
        "--audit-log",
        metavar="FILE",
        help="Path to a JSONL file to append full responses to",
    )
    parser.add_argument(
        "--skip",
        metavar="NAMES",
        default=",".join(DEFAULT_SKIP),
        help=f"Comma-separated inquiry name substrings to skip (default: {', '.join(DEFAULT_SKIP)})",
    )
    parser.add_argument(
        "--from",
        dest="from_inquiry",
        metavar="NAME",
        help="Skip inquiries before this one (substring match, for resuming)",
    )
    args = parser.parse_args()

    skip_names = [s.strip() for s in args.skip.split(",") if s.strip()]
    targets = load_resweep_targets(args.mode, skip_names)

    if not targets:
        print("Nothing to re-sweep.", file=sys.stderr)
        return

    # Sort: most outstanding recs first
    sorted_targets = sorted(
        targets.items(),
        key=lambda x: -(x[1]["no_evidence"] + x[1]["partial"]),
    )

    total_no_evidence = sum(v["no_evidence"] for v in targets.values())
    total_partial = sum(v["partial"] for v in targets.values())
    print(
        f"\nRe-sweep targets: {len(targets)} inquiries — "
        f"{total_no_evidence} no-evidence, {total_partial} partial\n",
        file=sys.stderr,
    )

    for name, counts in sorted_targets:
        tag = []
        if counts["no_evidence"]:
            tag.append(f"{counts['no_evidence']} no-evidence")
        if counts["partial"]:
            tag.append(f"{counts['partial']} partial")
        print(f"  {name}: {', '.join(tag)}", file=sys.stderr)

    if args.list:
        return

    print(file=sys.stderr)

    # Apply --from filter
    if args.from_inquiry:
        marker = args.from_inquiry.lower()
        before = len(sorted_targets)
        found = next(
            (i for i, (n, _) in enumerate(sorted_targets) if marker in n.lower()), None
        )
        if found is None:
            print(f"--from '{args.from_inquiry}' not found in target list.", file=sys.stderr)
            sys.exit(1)
        sorted_targets = sorted_targets[found:]
        print(f"--from: skipping {found} inquiries, starting at '{sorted_targets[0][0]}'", file=sys.stderr)

    include_partial = args.mode in ("partial", "all")

    try:
        for i, (name, counts) in enumerate(sorted_targets):
            print(f"\n[{i + 1}/{len(sorted_targets)}] {name}", file=sys.stderr)
            rc = run_inquiry(
                name,
                include_partial=include_partial,
                model=args.model,
                audit_log=args.audit_log,
                limit=args.limit,
            )
            if rc == 2:
                print("Billing limit reached — stopping.", file=sys.stderr)
                sys.exit(2)
            if rc != 0:
                print(f"research.py exited {rc} — stopping.", file=sys.stderr)
                sys.exit(rc)
            if i < len(sorted_targets) - 1:
                print(f"  pausing {DEFAULT_INTER_INQUIRY_PAUSE}s between inquiries…", file=sys.stderr)
                time.sleep(DEFAULT_INTER_INQUIRY_PAUSE)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)

    print(
        f"\nRe-sweep complete. Review new proposals in tools/review_app/app.py",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
