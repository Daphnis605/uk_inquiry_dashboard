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
2. Review each proposal: open the URL, read the recommendation, confirm it evidences implementation
3. For approved items: set `"approved": true` and add `"approved_at": "YYYY-MM-DD"`
4. For rejected items: delete the entry or leave as `approved: false`
5. Open a PR — CI validates JSON syntax, schema, and spot-checks URLs

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
