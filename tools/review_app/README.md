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

The review is split into two phases:

**Phase 1 (http://localhost:5000/) — Approve individual evidence items**

The app shows every `approved: false` evidence item grouped by inquiry and recommendation. For each item you will see:

- The **recommendation text** (from `data.json`) — what the inquiry actually recommended
- The **evidence title, URL, source type, evidence type badge, and description**

For each item, choose one of:

| Action | What it does |
|---|---|
| **Approve** | Sets `approved: true` and stamps `approved_at` — item will appear publicly once merged |
| **Reject** | Permanently removes the evidence item — use if the evidence does not support the recommendation |
| **Edit** | Opens an inline form to correct the title, URL, date, source type, evidence type, or description |
| **Approve all pending** | Bulk-approves every pending item in the current filter (with confirmation). Stamps `approved_at` on all. |

> **Warning:** Reject is permanent and cannot be undone within the app. If you reject by mistake, restore from git or re-run the import script.

When Phase 1 is complete (no items remain), click the **"Review recommendation statuses →"** link that appears.

**Phase 2 (http://localhost:5000/statuses) — Set recommendation status**

Shows each recommendation that has at least one approved item. All approved items are visible together so you can assess the full picture before setting a status. Use the dropdown at the bottom of each card:

| Status | When to use |
|---|---|
| **actioned** | At least one *complete* evidence item exists; the recommendation has been fully implemented (law enacted, scheme operational, policy in force) |
| **partial** | Evidence shows progress but implementation is incomplete, paused, or only promised |
| **no evidence found** | Researched; nothing found. Note the reason in the `notes` field |
| **not published** | The recommendation itself was not made public |

Setting a status does not auto-advance — scroll through all cards and set each one. Recommendations with no status are highlighted.

**Step 4 — Commit and push**

Once both phases are complete:

```bash
git add enriched_data.json
git commit -m "Review: approve evidence entries — [Inquiry name]"
git push
```

**Step 5 — CI passes, merge the PR**

The CI check (`Check all evidence items are approved before merging`) will now pass. The PR is ready to merge.

---

## Backfilling approved_at on existing items

If you have items that were approved before `approved_at` stamping was implemented (they show `approved_at: null`), run the backfill script:

```bash
python tools/backfill_approved_at.py --dry-run   # preview
python tools/backfill_approved_at.py             # write
```

---

## Reviewer playbook

### Phase 1 — What to check before approving

**Does the URL work?** Open it. It should be publicly accessible, not behind a login.

**Does the description match the source?** Read the actual page. The title and description should accurately describe what the source says — not what you hope it says.

**Is this evidence for *this specific recommendation*?** A government "acceptance" document for the whole inquiry is not evidence for a specific recommendation being *implemented*. The source should show something happened as a direct result of this recommendation.

**Source reliability (highest to lowest):**
1. `legislation` — legislation.gov.uk (primary legislation is definitive)
2. `official_report` — gov.uk or public body publications
3. `parliamentary_record` — Hansard, committee reports
4. `press_release` — government announcements (watch for over-claiming)
5. `news_article` — useful supporting evidence; never the sole source for `complete`

**What evidence_type to set:**

| Type | Use when |
|---|---|
| `partial` | Government accepted the recommendation; consultation launched; steps announced; policy proposed but not in force |
| `complete` | Law enacted; scheme operational; body established and functioning; policy in force |

**Edit vs Reject:**
- **Edit** if the core evidence is sound but the title or description is imprecise or too verbose.
- **Reject** if the URL does not support the claim, the source is not about this recommendation, or the URL is broken.

**Government position items (e.g. "Accepted in full — IBI Tracker"):** Keep these as `partial`. They confirm the recommendation was at minimum acknowledged, which is useful even if no further implementation evidence exists.

### Phase 2 — Setting recommendation status

Look at all approved items together before setting a status. The status is your overall judgement, not an automatic roll-up.

- **actioned**: There is at least one `complete` item AND the recommendation's core ask (new law, new body, new system) is concretely delivered and in force.
- **partial**: Some evidence of progress but the implementation is incomplete, paused, or only promised. Any mix of `partial`-type items only → use `partial`.
- **no_evidence_found**: None of the approved items actually evidence this recommendation being addressed. Add a note explaining why.
- **not_published**: Use only if the recommendation itself was never made public.

---

## Notes

- The app runs on `localhost:5000` only — it is not accessible from other machines
- Debug mode is off by default. To enable it for development: `FLASK_DEBUG=1 python tools/review_app/app.py`
- The app reads `enriched_data.json` and `data.json` from the repository root (two levels up from this file)
- If you need to restart mid-review, progress is already saved — the app reads the current state of the file on each page load
