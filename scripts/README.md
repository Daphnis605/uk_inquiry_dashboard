# Scripts

Maintainer tools for the UK Inquiry Dashboard. Not deployed — run locally.

## research.py — AI-assisted evidence research

Uses the Claude API to propose evidence URLs for recommendations that currently
have no verified outcome. All proposals are written with `approved: false` and
**must be reviewed by the maintainer** before they appear on the live dashboard.

### Setup

```bash
pip install -r scripts/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

### Usage

```bash
# Research 10 recommendations (default batch size)
python scripts/research.py

# Filter to one inquiry
python scripts/research.py --inquiry "Manchester Arena"

# Larger batch
python scripts/research.py --limit 50

# Preview without writing to disk
python scripts/research.py --dry-run

# Save a full audit log of every response including no-evidence reasoning
python scripts/research.py --audit-log audit.jsonl

# Disable web search (training knowledge only — faster, cheaper, less accurate)
python scripts/research.py --no-web-search

# Use Sonnet for a higher-quality second pass on items Haiku couldn't find
python scripts/research.py --model claude-sonnet-4-6 --limit 50
```

### Training knowledge vs. web search

Web search is **on by default**. Claude queries the internet before answering, making it
significantly more likely to find recent or obscure URLs. Use `--no-web-search` to fall back
to training knowledge only — faster and cheaper, but will miss anything published after the
model's knowledge cutoff or not well represented in training data.

Use `--audit-log audit.jsonl` to save the full raw response for every recommendation
processed, including the reasoning notes for "no evidence found" conclusions. This lets you
spot-check whether the model genuinely searched and why it gave up.

### Workflow

1. Run `research.py` — proposals are appended to `enriched_data.json` as `approved: false`
2. Open the review app to approve or reject each proposal:
   ```bash
   pip install flask
   python tools/review_app/app.py
   # opens http://localhost:5000
   ```
   For each item: open the URL, read the recommendation, then approve or reject in the UI.
3. Commit the reviewed file and open a PR:
   ```bash
   git add enriched_data.json
   git commit -m "Research: [inquiry name] — AI-assisted evidence proposals"
   ```
4. CI validates the schema and spot-checks URLs — it passes only when all evidence items
   are `approved: true`, so unapproved proposals block the merge until reviewed.

See [tools/review_app/README.md](../tools/review_app/README.md) for full review app instructions.

### What counts as valid evidence

- Legislation enacted (`legislation.gov.uk`)
- Official government report confirming implementation (`gov.uk`, `nao.org.uk`, etc.)
- Ministerial statement or press release announcing the action
- Parliamentary record confirming the change was made
- A credible news article or public body page confirming the thing is in place (where no primary source is available)

**Not sufficient:** acceptance letters, welcome statements, progress reviews without
confirmation of implementation.

### What gets rejected

AI proposals are rejected in the review app when:
- The URL no longer exists or doesn't contain the claimed content
- The source mentions the inquiry but doesn't confirm the recommendation was actually implemented
- The source is an acceptance or welcome of a recommendation, not evidence of action taken
- The URL is for a different recommendation or a different inquiry

Rejected URLs are kept as markers so the research script doesn't re-propose the same URL on future runs.

### Cost

Check current pricing at [anthropic.com/pricing](https://www.anthropic.com/pricing).
Each recommendation uses roughly 400 input tokens and 300 output tokens (more with web search).

Haiku is the default — good for broad coverage at low cost. Switch to Sonnet
(`--model claude-sonnet-4-6`) for a higher-quality pass on items Haiku couldn't find.

---

## batch_research.py — full sweep across all inquiries

Runs `research.py` across all 21 target inquiries in priority order, with
automatic pacing and gates to stop if the API is misbehaving.

Excluded from the batch (covered by official UK inquiry dashboards):
Manchester Arena, Grenfell Tower, Infected Blood.

### Usage

```bash
# Preview the plan (no API calls)
python scripts/batch_research.py --list

# Full sweep (Haiku, web search on)
python scripts/batch_research.py

# Resume after a break
python scripts/batch_research.py --from "Leveson"

# Higher quality second pass
python scripts/batch_research.py --model claude-sonnet-4-6

# Save a full audit log
python scripts/batch_research.py --audit-log batch_audit.jsonl
```

### Pacing

Web search is capped at 1 search per call (`max_uses: 1`), keeping each call to
~15–40k input tokens against the Haiku 50k ITPM limit. Sleep between requests is
computed dynamically: `max(60s, tokens/50k × 60s + 15s)` — typically 60s per rec.
Full sweep of ~463 non-Mid Staffs recs takes ~8 hours; use `--from` to split across
multiple sessions.

### Gates

If more than 60% of recs in an inquiry return `no_response` (exhausted retries),
the script pauses and asks whether to continue. Non-zero exit from `research.py`
stops the batch immediately.
