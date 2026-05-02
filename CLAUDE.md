# UK Inquiry Dashboard — Claude Code Guide

## What this repo is

A static dashboard tracking whether UK public inquiry recommendations have been implemented by government. Data is in `data.json`; evidence of implementation lives in `enriched_data.json`.

Live site: GitHub Pages from `main`.

## Key files

| File | Purpose |
|------|---------|
| `data.json` | Source of truth — inquiries, recommendations, metadata. Do not modify recommendation text. |
| `enriched_data.json` | Evidence entries keyed by `InquiryName__N` (0-indexed). All AI proposals land here with `approved:false`. |
| `index.html` + `styles.css` | The dashboard UI. Vanilla JS, no build step. |
| `scripts/research.py` | AI-assisted evidence research via Claude API + web search. |
| `scripts/batch_research.py` | Runs research.py across all inquiries in sequence. |
| `tools/review_app/app.py` | Local Flask app to approve/reject evidence proposals. Run with `python tools/review_app/app.py`. |
| `.github/workflows/validate.yml` | CI: validates JSON, checks all evidence is `approved:true`, spot-checks URLs. |

## enriched_data.json format

Keys are `InquiryName__N` where N is **0-indexed** (matches `enumerate()` in research.py).

```json
"Brook House Inquiry__0": {
  "evidence_status": "actioned",
  "evidence": [
    {
      "title": "...",
      "url": "https://...",
      "source_type": "official_report",
      "date": "YYYY-MM-DD",
      "description": "...",
      "evidence_type": "complete",
      "approved": false,
      "approved_at": null
    }
  ],
  "notes": "one sentence"
}
```

Rejected items are shrunk to `{"url": "...", "rejected": true}` — URL kept to prevent re-proposal, all other fields stripped.

## Branching conventions

- `fix/*` — hotfixes direct to main
- `feature/*` — new UI/tool features
- `data/*` — enriched_data.json proposals (blocked by CI until reviewed)
- `research/*` — research script runs (legacy; use `data/*` going forward)

CI blocks merge if any evidence item has `approved:false` and is not `rejected:true`.

## Workflow: adding evidence

1. `python scripts/research.py --inquiry "Name" --limit 10` — proposals → `enriched_data.json`
2. `python tools/review_app/app.py` → review at http://localhost:5000
3. Commit reviewed file → open `data/*` PR
4. CI passes once all items are `approved:true`

## Known gotchas

- `load_recommendations()` in review app uses 0-based indexing to match research.py keys. Do not change to 1-based.
- Rejected items (`rejected:true`) must be skipped in CI approved-check and URL-check — already handled in validate.yml.
- Mid Staffordshire (288 recs) is excluded from batch sweeps — responses reference a single bulk document rather than individual evidence URLs.
- The Anthropic web_search tool uses `max_uses: 1` to cap input tokens at ~20–40k. Without this each call uses ~178k tokens.
- Default model is `claude-haiku-4-5-20251001`. Use `--model claude-sonnet-4-6` for a higher-quality second pass.

## Excluded inquiries (covered by official dashboards)

Manchester Arena, Grenfell Tower, Infected Blood.

## CSS / UI notes

- Mobile breakpoint: `max-width: 768px`
- Contents nav tray: slides from right on mobile, left on desktop
- Put mobile overrides **after** desktop base rules in styles.css or the cascade will ignore them
