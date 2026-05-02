#!/usr/bin/env python3
"""
Batch runner for research.py — works through all inquiries that have
unevidenced recommendations, in descending order of unevidenced count.

Usage:
    # Preview the plan without running anything
    python scripts/batch_research.py --list

    # Full run (Haiku, web search on)
    python scripts/batch_research.py

    # Skip specific inquiries (substrings, comma-separated)
    python scripts/batch_research.py --skip "Manchester Arena,Grenfell,Infected Blood"

    # Resume after a break (substring match)
    python scripts/batch_research.py --from "Leveson"

    # Dry run — API calls happen but nothing is written to disk
    python scripts/batch_research.py --dry-run

    # Higher quality second pass
    python scripts/batch_research.py --model claude-sonnet-4-6

    # Full audit log
    python scripts/batch_research.py --audit-log batch_audit.jsonl
"""

import json
import subprocess
import sys
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESEARCH_SCRIPT = ROOT / "scripts" / "research.py"
DATA_JSON = ROOT / "data.json"
ENRICHED_JSON = ROOT / "enriched_data.json"

# ---------------------------------------------------------------------------
# Gate thresholds
# ---------------------------------------------------------------------------

# Stop and prompt if this fraction of recs come back as no_response
NO_RESPONSE_GATE = 0.6

# Default pause between inquiries (seconds) — lets the TPM window fully reset
DEFAULT_INTER_INQUIRY_PAUSE = 120


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_unevidenced_counts(skip_names: list[str]) -> list[tuple[str, int]]:
    """
    Return list of (inquiry_name, unevidenced_count) sorted descending,
    excluding inquiries whose names contain any of the skip substrings.
    """
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    enriched = json.loads(ENRICHED_JSON.read_text(encoding="utf-8"))

    counts: dict[str, int] = {}
    for dept in data:
        for inquiry in dept.get("Inquiries", []):
            name = inquiry["InquiryName"]
            for idx, _ in enumerate(inquiry.get("Recommendations", [])):
                key = f"{name}__{idx}"
                existing = enriched.get(key)
                has_approved = (
                    existing
                    and existing.get("evidence")
                    and any(ev.get("approved") for ev in existing["evidence"])
                )
                if not has_approved:
                    counts[name] = counts.get(name, 0) + 1

    results = [
        (name, count)
        for name, count in counts.items()
        if not any(s.lower() in name.lower() for s in skip_names if s)
    ]
    results.sort(key=lambda x: -x[1])
    return results


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_inquiry(
    name: str,
    limit: int,
    *,
    dry_run: bool,
    model: str,
    audit_log: str | None,
    no_web_search: bool,
    start_from: int = 1,
) -> dict:
    """
    Run research.py for one inquiry, streaming stderr to the terminal.
    Returns {name, returncode, attempted, no_response}.
    """
    cmd = [
        sys.executable, str(RESEARCH_SCRIPT),
        "--inquiry", name,
        "--limit", str(limit),
        "--model", model,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if audit_log:
        cmd += ["--audit-log", audit_log]
    if no_web_search:
        cmd.append("--no-web-search")
    if start_from > 1:
        cmd += ["--start-from", str(start_from)]

    attempted = 0
    no_response = 0
    last_rec = 0

    try:
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        for line in proc.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()
            stripped = line.strip()
            if stripped.startswith("[") and "/" in stripped:
                attempted += 1
                # Parse rec number from lines like "[3/288] Inquiry rec 42"
                rec_match = __import__("re").search(r"\brec (\d+)$", stripped)
                if rec_match:
                    last_rec = int(rec_match.group(1))
            if "→ no_response" in stripped:
                no_response += 1
        proc.wait()
        return {"name": name, "returncode": proc.returncode, "attempted": attempted, "no_response": no_response, "last_rec": last_rec}
    except KeyboardInterrupt:
        proc.terminate()
        raise


def check_gate(stats: dict) -> bool:
    """Return True if safe to continue; prompts user if gate fires."""
    attempted, no_response = stats["attempted"], stats["no_response"]
    if attempted == 0 or no_response / attempted < NO_RESPONSE_GATE:
        return True
    rate = no_response / attempted
    print(
        f"\n⚠  Gate: {no_response}/{attempted} recs returned no_response ({rate:.0%}). "
        f"This usually means persistent rate limit failures.",
        file=sys.stderr,
    )
    return input("   Continue to next inquiry? [y/N] ").strip().lower() == "y"


def commit_inquiry(name: str) -> bool:
    """
    Stage enriched_data.json and commit if there are changes.
    Returns True if a commit was made, False if nothing changed.
    """
    # Check whether enriched_data.json actually changed
    diff = subprocess.run(
        ["git", "diff", "--quiet", "enriched_data.json"],
        cwd=ROOT,
    )
    if diff.returncode == 0:
        print("  (no changes to enriched_data.json — nothing to commit)", file=sys.stderr)
        return False

    subprocess.run(["git", "add", "enriched_data.json"], cwd=ROOT, check=True)
    msg = f"Research: {name} — AI-assisted evidence proposals (approved:false)"
    result = subprocess.run(["git", "commit", "-m", msg], cwd=ROOT)
    if result.returncode == 0:
        print(f"  ✓ Committed enriched_data.json for: {name}", file=sys.stderr)
        return True
    else:
        print("  ⚠ git commit failed — continuing without commit", file=sys.stderr)
        return False


def pause_between(seconds: int) -> None:
    print(f"\nPausing {seconds}s before next inquiry…", file=sys.stderr, flush=True)
    for remaining in range(seconds, 0, -15):
        print(f"  {remaining}s remaining…", end="\r", file=sys.stderr, flush=True)
        time.sleep(min(15, remaining))
    print(file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-run research.py across all inquiries with unevidenced recommendations."
    )
    parser.add_argument("--list", action="store_true", help="Print plan and exit")
    parser.add_argument("--skip", metavar="NAMES",
                        help="Comma-separated substrings of inquiry names to skip")
    parser.add_argument("--from", dest="from_inquiry", metavar="NAME",
                        help="Skip ahead to the first inquiry matching this substring")
    parser.add_argument("--dry-run", action="store_true",
                        help="Pass --dry-run to research.py (nothing written to disk)")
    parser.add_argument("--no-web-search", action="store_true")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--audit-log", metavar="FILE")
    parser.add_argument("--pause", type=int, default=DEFAULT_INTER_INQUIRY_PAUSE, metavar="SECS",
                        help=f"Seconds between inquiries (default: {DEFAULT_INTER_INQUIRY_PAUSE})")
    parser.add_argument("--commit-each", action="store_true",
                        help="git commit enriched_data.json after each inquiry (useful for long runs)")
    parser.add_argument("--start-from", type=int, default=1, metavar="N",
                        help="For the first inquiry in the queue, skip recommendations numbered below N (resume mid-inquiry)")
    args = parser.parse_args()

    skip_names = [s.strip() for s in (args.skip or "").split(",")]
    queue = load_unevidenced_counts(skip_names)

    if not queue:
        print("No unevidenced recommendations found.", file=sys.stderr)
        return

    if args.list:
        total_recs = sum(c for _, c in queue)
        mode = "training knowledge" if args.no_web_search else "web search"
        print(f"Batch plan — {len(queue)} inquiries, {total_recs} unevidenced recs")
        commit_note = "  |  --commit-each" if args.commit_each else ""
        print(f"Model: {args.model}  |  mode: {mode}  |  pause: {args.pause}s{commit_note}\n")
        for i, (name, count) in enumerate(queue, 1):
            print(f"  {i:2d}. [{count:3d} recs]  {name}")
        secs_per_rec = 65 if not args.no_web_search else 1
        print(f"\nEstimated time: ~{total_recs * secs_per_rec / 3600:.1f} hours continuous")
        print("Tip: use --from NAME to resume after a break.")
        return

    if args.from_inquiry:
        start = next(
            (i for i, (name, _) in enumerate(queue)
             if args.from_inquiry.lower() in name.lower()),
            None,
        )
        if start is None:
            print(f"ERROR: --from '{args.from_inquiry}' matched no inquiry.", file=sys.stderr)
            sys.exit(1)
        queue = queue[start:]
        print(f"Resuming from: {queue[0][0]}\n", file=sys.stderr)

    total = len(queue)
    mode = "web search" if not args.no_web_search else "training knowledge only"
    print(
        f"Batch starting: {total} inquiries  |  model={args.model}  |  "
        f"pause={args.pause}s  |  {mode}",
        file=sys.stderr,
    )
    if args.dry_run:
        print("DRY RUN — nothing will be written to enriched_data.json", file=sys.stderr)
    if args.commit_each and not args.dry_run:
        print("--commit-each: will git commit enriched_data.json after each inquiry", file=sys.stderr)
    print(file=sys.stderr)

    completed = 0
    try:
        for i, (name, limit) in enumerate(queue):
            print(f"\n{'=' * 60}", file=sys.stderr)
            print(f"[{i + 1}/{total}] {name}  ({limit} unevidenced)", file=sys.stderr)
            print(f"{'=' * 60}", file=sys.stderr)

            stats = run_inquiry(
                name, limit,
                dry_run=args.dry_run,
                model=args.model,
                audit_log=args.audit_log,
                no_web_search=args.no_web_search,
                start_from=args.start_from if i == 0 else 1,
            )
            completed += 1

            if stats["returncode"] == 2:
                print(f"\n💳  Billing limit reached after {completed}/{total} inquiries — stopping.", file=sys.stderr)
                resume = f'--from "{name}" --start-from {stats["last_rec"] + 1}' if stats.get("last_rec") else f'--from "{name}"'
                print(f"Resume next month with: python scripts/batch_research.py {resume}", file=sys.stderr)
                sys.exit(2)
            if stats["returncode"] not in (0, None):
                print(f"\n✗  research.py exited {stats['returncode']} — stopping.", file=sys.stderr)
                sys.exit(1)

            if not check_gate(stats):
                print("\nStopped by user after gate check.", file=sys.stderr)
                sys.exit(0)

            if args.commit_each and not args.dry_run:
                commit_inquiry(name)

            if i < total - 1:
                pause_between(args.pause)

    except KeyboardInterrupt:
        remaining_name = queue[completed][0] if completed < total else ""
        resume = f'--from "{remaining_name}"' if remaining_name else ""
        print(
            f"\n\nInterrupted after {completed}/{total} inquiries."
            + (f"\nResume with: python scripts/batch_research.py {resume}" if resume else ""),
            file=sys.stderr,
        )
        sys.exit(130)

    print(f"\n✓  All {completed} inquiries processed.", file=sys.stderr)


if __name__ == "__main__":
    main()
