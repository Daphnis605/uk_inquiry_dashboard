# Contributing to UK Inquiry Dashboard

Thank you for contributing. This project tracks whether the recommendations from UK public inquiries have been implemented. Every verified piece of evidence matters.

---

## Ways to contribute

### 1. Submit evidence for a recommendation

If you find a news article, legislation page, gov.uk publication, or parliamentary record that shows a recommendation has been acted on, please submit it.

**How to submit:**
- **GitHub Issue** (preferred): Open an [evidence submission issue](../../issues/new?template=evidence-submission.md). Use the template — the structured fields make review much faster.
- **Google Form**: If you prefer not to use GitHub, use the [public contribution form](https://forms.gle/eiPVUv8C). Submissions are reviewed regularly.

**What counts as evidence:**
- A law or statutory instrument that was enacted
- An official government publication, guidance document, or policy update
- A parliamentary debate or select committee report confirming action taken
- A credible news article reporting the specific action

**What does NOT count as evidence:**
- A government "acceptance" letter or commitment document — accepting a recommendation is not the same as implementing it
- General documents that mention the inquiry but do not confirm the specific recommendation was acted on
- Social media posts
- Documents behind a login or paywall

**Key principle: blank is better than wrong.** If you are not certain the evidence specifically relates to this recommendation being implemented, do not submit it. An empty field is honest. A wrong URL is not.

---

### 2. Report a data error

If you spot an error in a recommendation, its category, or its change type:

1. Open a [data error issue](../../issues/new?template=data-error.md)
2. Describe what is wrong and provide a link to the source that proves the correct value
3. Recommendation text is verbatim from original inquiry reports — if you believe the text is wrong, provide the specific page in the original PDF

---

### 3. Submit a pull request

For code or schema changes:

1. Fork the repository
2. Create a branch: `feature/your-change` or `fix/your-fix`
3. Make your changes
4. Open a pull request using the PR template
5. CI will run automatically — fix any failures before requesting review

All PRs must pass CI validation before they can be merged. The maintainer reviews all PRs.

---

## Evidence review process

All submitted evidence is reviewed by the maintainer before it appears on the dashboard. This is not because we distrust contributors — it is because the project's credibility depends entirely on accuracy.

Every piece of evidence enters the system with `approved: false` and is **never shown publicly** until a maintainer has read it and explicitly approved it. CI enforces this: a PR cannot be merged if it contains any unapproved evidence items.

---

### For single issue submissions

When you open an evidence submission issue, the process is:

1. CI checks that the URL is accessible (HEAD request)
2. The maintainer reads the recommendation text and the evidence side by side
3. The maintainer decides: **Approve** / **Reject** / **Needs more research**
4. If approved, the evidence is added to `enriched_data.json` with `approved: true` and the PR is merged
5. The dashboard updates automatically

You will receive a notification on your GitHub issue when a decision is made.

---

### For bulk data PRs

When a PR adds multiple evidence entries directly to `enriched_data.json` (section 3 above):

1. The PR is opened — all new entries have `approved: false`
2. **CI fails immediately** — this is expected and signals that review is required
3. The maintainer checks out the branch and runs the local review app:
   ```
   git checkout <branch-name>
   python tools/review_app/app.py
   # opens http://localhost:5000
   ```
4. Each entry is reviewed side by side with the recommendation text; entries are approved or rejected
5. The maintainer commits the reviewed file and pushes:
   ```
   git add enriched_data.json
   git commit -m "Review: approve evidence entries"
   git push
   ```
6. CI now passes — the PR can be merged
7. The dashboard updates automatically

See [tools/review_app/README.md](tools/review_app/README.md) for full instructions on running the review app.

---

## Data principles

These are non-negotiable:

**1. Recommendation text is sacred.**
The text of every recommendation is taken verbatim from the original inquiry report PDF. It is never paraphrased, summarised, or altered in any way. The `ActionCategory` and `ChangeType` labels are the maintainer's own categorisation and are clearly labelled as such.

**2. Blank is better than wrong.**
If no verified evidence exists for a recommendation, it shows as blank — not "not done." The distinction matters enormously. An absence of evidence is not evidence of absence, but it is honest.

**3. Implementation, not acceptance.**
A government can accept a recommendation in 2024 and still not have enacted the legislation by 2026. This project tracks what was actually done, not what was promised. Evidence must show a specific, completed action.

**4. Every URL must be real and clickable.**
No inferred outcomes. No fabricated links. If a URL returns a 404, it will be rejected by CI and by the reviewer.

**5. Independence.**
This project is not affiliated with the UK government, any political party, or any inquiry body. It does not take positions on whether recommendations should have been accepted. It only records what was recommended and what evidence exists of it being implemented.

---

## Questions?

Open a GitHub issue or start a discussion. If you are unsure whether a piece of evidence qualifies, open an issue and ask — that is better than not submitting something valuable.
