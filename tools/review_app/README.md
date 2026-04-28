# Evidence Review App

A local Flask app for reviewing and approving evidence entries in `enriched_data.json`. Used by the maintainer to work through bulk data PRs before they can be merged.

---

## When to use this

Any PR that adds entries to `enriched_data.json` will **fail CI** until all entries have `approved: true`. The review app is the tool for doing that review.

If you have opened a single-evidence GitHub Issue instead of a bulk PR, you do not need this app — use it only for PRs.

---

## Prerequisites

Python 3.9+ and Flask:

```bash
pip install flask
```

---

## Workflow: reviewing a bulk data PR

**Step 1 — Check out the branch**

```bash
git fetch origin
git checkout feature/evidence-ibi   # or whichever branch the PR is on
```

**Step 2 — Start the review app**

```bash
python tools/review_app/app.py
```

Open http://localhost:5000 in your browser.

**Step 3 — Review each entry**

The app shows every `approved: false` evidence item grouped by inquiry. For each item you will see:

- The **recommendation text** (from `data.json`) — what the inquiry actually recommended
- The **evidence title, source, date, and description** — what the submission claims as evidence

For each item, choose one of:

| Action | What it does |
|---|---|
| **Approve** | Sets `approved: true` — entry will appear publicly once the PR is merged |
| **Reject** | Permanently removes the evidence item — use if the evidence does not support the recommendation |
| **Set status** | Updates `evidence_status` for the recommendation (`actioned`, `partial`, `no_evidence_found`, `not_published`) |

> **Warning:** Reject is permanent and cannot be undone within the app. If you reject by mistake, re-run the original data import script or restore from git.

Changes are written to `enriched_data.json` immediately on each action. You do not need to save manually.

**Step 4 — Commit and push**

Once you have reviewed all entries:

```bash
git add enriched_data.json
git commit -m "Review: approve evidence entries — [Inquiry name]"
git push
```

**Step 5 — CI passes, merge the PR**

The CI check (`Check all evidence items are approved before merging`) will now pass. The PR is ready to merge.

---

## Notes

- The app runs on `localhost:5000` only — it is not accessible from other machines
- Debug mode is off by default. To enable it for development: `FLASK_DEBUG=1 python tools/review_app/app.py`
- The app reads `enriched_data.json` and `data.json` from the repository root (two levels up from this file)
- If you need to restart mid-review, progress is already saved — the app reads the current state of the file on each page load
