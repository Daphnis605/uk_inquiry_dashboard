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

# Cheaper/faster model for a first-pass sweep
python scripts/research.py --model claude-haiku-4-5-20251001 --limit 100
```

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

**Not sufficient:** acceptance letters, welcome statements, progress reviews without
confirmation of implementation, or news articles without primary source.

### Cost

Check current pricing at [anthropic.com/pricing](https://www.anthropic.com/pricing).
Each recommendation uses roughly 400 input tokens and 300 output tokens.

A practical approach: run Haiku first for broad coverage, then Sonnet on
the recommendations Haiku couldn't find evidence for.
