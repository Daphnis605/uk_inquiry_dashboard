## What does this PR change?

<!-- Describe what you changed and why. Link to the relevant Issue if applicable. -->

---

## Checklist

### For all PRs
- [ ] JSON is valid (CI will check this automatically)
- [ ] Schema validation passes (CI will check this automatically)

### For PRs that change `data.json`
- [ ] No existing `Recommendation` text has been altered (recommendation text is verbatim from the original inquiry report and must never change)
- [ ] Any new recommendations include `ChangeType` and `ActionCategory`
- [ ] `ReportDate` is in DD/MM/YYYY format
- [ ] `ReportLink` points to the official inquiry report

### For PRs that change `enriched_data.json`
- [ ] Every new evidence item has a real, working URL (CI will spot-check this)
- [ ] `approved` is set to `false` for any newly submitted evidence (the maintainer sets this to `true` after review)
- [ ] `evidence_status` accurately reflects the evidence provided
- [ ] This is evidence of *implementation*, not just *acceptance* of the recommendation

### For PRs that change `schema/*.json`
- [ ] Existing valid data still validates against the updated schema
- [ ] Changes are backwards compatible, or a migration path is described

---

*Issues or questions? Add a comment to this PR.*
