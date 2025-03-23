# UK Inquiry Dashboard

## Overview

The UK Inquiry Dashboard is a project aimed at compiling and visualizing recommendations from various public inquiries in the United Kingdom. The goal is to identify areas of improvement and prevent tragedies from reoccurring by making these recommendations accessible and actionable.

## Purpose
Easier to access, Easier to learn from, Easier to prevent


## Mission
 I hope we can all agree that public inquiries are triggered by events we never want to see repeated. They involve extensive and expensive investigation, testimony from those affected, and expert analysis to uncover root causes. These efforts carry weight—not just in cost, but in the responsibility to act.

 Not all recommendations carry the same weight, but the easier they are to access, the easier they are to learn from—and the greater the chance that every necessary change is made, so even if we can't fix everything, atleast we don't see the same tragedies twice.


## Data Source

The data for this project is stored in `data.json`. This file contains exact quotes from the inquiry reports, ensuring that the recommendations are not paraphrased or rewritten. These recommendations have been carefully crafted through a rigorous and expensive process, and it is crucial to maintain their integrity.

### How the Data is Made

1. **Extracting Recommendations**: The recommendations are extracted directly from the inquiry reports. This involves identifying the recommendation section and looking for premade lists or sentences that start with phrases like "I recommend" or similar.
2. **Assigning ChangeType and ActionCategory**: Each recommendation is manually read to determine the appropriate `ChangeType` and `ActionCategory`. It is important to note that ChatGPT recommended the action-based categories based on reading the `data.json`, but it has not been used for assigning them to the data as test cases were misinterpreted and miscategorized. A discussion in a Pull Request(PR) may help resolve any uncertainty in the recommendation categorization.
3. **Maintaining Integrity**: The recommendations are not paraphrased or rewritten to ensure their integrity. If you identify any missed or incorrect recommendations, please raise a request for improvement.

### Action-Based Categories

The action-based categories were recommended by ChatGPT based on the reading of the `data.json`. However, they were not used for assigning categories to the data due to potential misinterpretations. The categories include:

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


### Change Types

The change types assigned to each recommendation include:

- <strong style="color:#1f77b4;">More</strong> – Increase in a particular activity or resource.
- <strong style="color:#ff7f0e">Less</strong> – Decrease in a particular activity or resource.
- <strong style="color:#9467bd">Different</strong> – Change in the nature or approach of a process.
- <strong style="color:#2ca02c">New</strong> – Introduction of a new system, policy, or procedure.
- <strong style="color:#d62728">Cease</strong> – Discontinuation of a practice or activity.


## Inquiry Reports

The list of inquiries was taken from Wikipedia: [List of public inquiries in the United Kingdom](https://en.wikipedia.org/wiki/List_of_public_inquiries_in_the_United_Kingdom). The report links are included in the `data.json`. If you identify any missed or incorrect information, please raise a request for improvement.


## Contributing

If you would like to contribute to this project, please follow these guidelines:

1. **Pull Requests**: Submit a pull request with your changes. Ensure that you provide a detailed description of the changes and the reasoning behind them.
2. **Discussions**: If there is any uncertainty in the recommendation categorization, please initiate a discussion in the PR to resolve it.
3. **Reporting Issues**: If you identify any missed or incorrect recommendations, please raise a request for improvement.

Thank you for your contributions to this project.