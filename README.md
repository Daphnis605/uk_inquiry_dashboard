# UK Inquiry Dashboard

## Overview

The UK Inquiry Dashboard collects and displays recommendations from public inquiries. The aim is to make them easier to find, understand, and act on—helping to prevent future tragedies.

## Purpose

- Easier to access
- Easier to learn from
- Easier to prevent

## Why This Matters

Public inquiries happen after serious events that should never be repeated. They involve detailed investigations, expert analysis, and testimony from those affected. These efforts come at a high cost—not just financially, but in terms of responsibility to act.

Not all recommendations are equal, but the easier they are to find and learn from, the greater the chance of real change. Even if not everything can be fixed, we should never see the same failures happen twice.

[Lords committee calls for major overhaul of public inquiries(Sept 2024)](https://www.parliament.uk/business/lords/media-centre/house-of-lords-media-notices/2024/september-2024/lords-committee-report-on-the-effectiveness-of-statutory-inquiries-to-be-published-next-week/)

## Data Source

The data is stored in `data.json`. It contains exact quotes from inquiry reports to preserve their meaning and accuracy.

### How the Data is Processed

The main method used to create the `data.json` is described in the `method/main method.md`. Some specific steps are covered in other documents in the method folder

1. **Extracting Recommendations**
   - Recommendations are taken directly from inquiry reports.
   - They are structured in JSON format for consistency.
   - No AI is used in this step to ensure accuracy.

2. **Assigning ChangeType and ActionCategory**
   - Each recommendation is reviewed and categorised.
   - AI was tested for this but was not reliable. All final decisions are made by a person.
   - If a recommendation is unclear, discussion in a pull request (PR) helps resolve it.

3. **Maintaining Accuracy**
   - No recommendations are rewritten.
   - If you spot an error, raise an issue or submit a PR with a fix.

### Action-Based Categories

Recommendations are grouped into categories to highlight what kind of change is needed:

- <strong style="color:#CB9608">Law & Regulation</strong> – Changes in legal frameworks, policies, and compliance rules.
- <strong style="color:#c4ab09">Enforcement & Compliance</strong> – Strengthening or adjusting enforcement mechanisms.
- <strong style="color:#bdbf09">Accountability & Oversight</strong> – Who is responsible and how they are monitored.
- <strong style="color:#97b430">Governance & Structure</strong> – Organizational, management, and leadership changes.
- <strong style="color:#70a957">Processes & Procedures</strong> – Internal workflows, operational protocols, and best practices.
- <strong style="color:#2292a4">Training & Education</strong> – Learning, qualifications, and professional development.
- <strong style="color:#4aa4b2">Documentation & Records</strong> – Record-keeping, reporting standards, and data retention.
- <strong style="color:#6F499E">Technology & Systems</strong> – IT, software, tracking systems, and digital transformation.
- <strong style="color:#499e7e">Communication & Reporting</strong> – How information is shared internally and externally.
- <strong style="color:#70797b">Funding & Resources</strong> – Budget allocations, financial support, and resource planning.
- <strong style="color:#ab9826">Emergency & Risk Management</strong> – Crisis handling, mitigation strategies, and safety planning.
- <strong style="color:#47a12f">Audits & Reviews</strong> – Evaluations, performance assessments, and feedback loops.
- <strong style="color:#49899E">Infrastructure & Facilities</strong> – Physical buildings, equipment, and safety improvements.
- <strong style="color:#D3A4EA">Investigation & Redress</strong> – Fact-finding, inquiries, and corrective actions.
- <strong style="color:#93499E">Support & Welfare</strong> – Assistance for affected individuals, victims, and communities.
- <strong style="color:#878c8f">None published</strong> – Recommended actions if they exist, have not been published or are not available.



### Change Types

The change types assigned to each recommendation include:

- <strong style="color:#1f77b4;">More</strong> – Increase in a particular activity or resource.
- <strong style="color:#ff7f0e">Less</strong> – Decrease in a particular activity or resource.
- <strong style="color:#9467bd">Different</strong> – Change in the nature or approach of a process.
- <strong style="color:#2ca02c">New</strong> – Introduction of a new system, policy, or procedure.
- <strong style="color:#d62728">Cease</strong> – Discontinuation of a practice or activity.
- <strong style="color:#878c8f">None</strong> – No (published) recommendations.

## Inquiry Reports

The list of inquiries comes from [Wikipedia](https://en.wikipedia.org/wiki/List_of_public_inquiries_in_the_United_Kingdom). Report links are in `data.json`. If you notice missing or incorrect data, raise an issue or submit a PR.

## Contributing

You can help improve this project:

1. **Pull Requests** – Submit changes with a clear explanation.
2. **Discussions** – If a recommendation’s category is unclear, open a PR discussion.
3. **Report Issues** – Found an error? Raise an issue or submit a fix.

Thank you for contributing!
