1. Copy-pasted recommendations from the Inquiry's website (covid19.public-inquiry.uk/inquiry-recommendations/) and used Sublime to remove new lines and additional spacing
2. Initially added in {"Recommendations": "<recommendation>"}
3. Manually added "ChangeType": "", "ActionCategory": "" using find and replace to detect the unique indent, allowing VS Code to auto-suggest an answer, then considering and deciding which ActionCategory and ChangeType suits each recommendation

Note on ReportDate/ReportLink: the UK Covid-19 Inquiry is ongoing and publishes a separate standalone final report per module (Module 1, Module 2, Module 5, etc. — each permanently final, not superseded by a later consolidated report). This entry bundles recommendations across modules under one InquiryName so it reads as a single inquiry in the dashboard's charts, rather than fragmenting into one chart node per module.

ReportDate is set to 18/07/2024, the publication date of Module 1 (the first report) — it does not reflect the true publication date of every recommendation in this entry, since later modules were published on different dates. ReportLink points to the Inquiry's live recommendations index rather than a single PDF, since no single report covers all recommendations here.

This is a deliberate choice, not an oversight
