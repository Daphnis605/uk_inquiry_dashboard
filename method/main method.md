# How the `data.json` was created  

This document explains the main method used to create `data.json`. Some specific steps are covered in other documents.  

## Keeping recommendations accurate 

We have taken great care to keep the original meaning of each recommendation. The wording has been preserved as much as possible to avoid changing the intent.

If you spot any mistakes or have suggestions for improvements, please raise a GitHub Issue. If you know how to fix it, you can submit a Pull Request.


## 1. Extracting recommendations and structuring them in JSON  

### No interpretation in this step  

Each inquiry report follows a similar structure, with conclusions and recommendations. However, the way recommendations are presented varies:  
- Some reports list them in tables.  
- Some highlight them in **bold** text.  
- Some use separate boxes.  

These formats make recommendations easy for people to read but difficult for machines to extract.  

We do not use AI for this step. 

### Handling bullet points  

If a recommendation contains bullet points, they should be rewritten as full sentences.  

Example:  

**Original:**  
```
I recommend the bill be amended to show:  
* Change 1  
* Change 2  
```
**Rewritten:**  
```
I recommend the bill be amended to show change 1.  
I recommend the bill be amended to show change 2.  
```
Alternatively, the whole recommendation can be kept as a single sentence. The approach depends on:  
- Whether the points belong to different Change Types or Action Categories.  
- Whether the focus is on changing the law or listing specific details.  

There may be more than one correct way to structure a recommendation. The key consideration is whether the text remains readable in the Inquiries table.  

2. Add ChangeType and Action-Based Category

    **Room for interpretation in this project**

    AI (Chat GPT 4-o LLM) has been used to define the categories based one a portion of the original data.json. This means that as more data gets added, the categories may need to change. 
    ChangeTypes and ActionCategories are more nuanced and subject to change by redefining the categories so there is not as much emphasis on getting this absolutely right as there is in the first step. AI is permissible but so far as not been of sufficient standard.

    Github Copilot has been useful in formating inital guesses via the predictive text feature but it is not able to fully capture the underlying meaning of the recommendations and the action being requested in the recommendation. Therefore a human supervisor, reading each recommendation and correcting each suggested ChangeType and ActionCategory.


    Suggestion: Split screen view with data.json beside the Action-Based Categories and Change Types to easily reference and consider options

    ### Considering what is the right ChangeType
    `More` might mean "Continue doing the correct behaviour" i.e. more across time.
    `Cease` might mean abolishing a policy
    `Diffent` might mean no action but since it is a recommendation, the action is to consider making modifying an existing thing

    ### Considering what is the right ActionCategory
        Many recommendations could fall under `Processes and Procedures` or `Law and Regulation` if not considered carefully. Consider what practically needs to change to prevent the events in the inquiry happening again. What is the systematic issue? 
        
        Sometimes there is overlap in `Communication & Reporting`,`Technology & Systems` and `Documentation and Records`; is it that you need more automation or that a document needs to be accessible to different departments? Generally err on the side that unless technology or automated process is specifically called for, it will often fall under `Communication & Reporting` or `Documentation and Records`. 

        "Equipment" or other supplies including devices handed to staff, have been considered to fall under `Infrastructure & Facilities`

        `Investigation & Redress` vs `Audits & Reviews`: Is the recommendation for another inquiry or review of whether corrective actions have been completed? or is it about a regulator creating a routine of audits and spot checks?

        See data.json for how categories have been applied.




3. Peer review and proof reading






 


## 1. Extracting recommendations and structuring them in JSON  

### No interpretation in this step  

Each inquiry report follows a similar structure, with conclusions and recommendations. However, the way recommendations are presented varies:  
- Some reports list them in tables.  
- Some highlight them in **bold** text.  
- Some use separate boxes.  

These formats make recommendations easy for people to read but difficult for machines to extract.  

We do not use AI for this step.  

### Handling bullet points  

If a recommendation contains bullet points, they should be rewritten as full sentences.  

Example:  

**Original:**  
```
I recommend the bill be amended to show:  
* Change 1  
* Change 2  
```
**Rewritten:**  
```
I recommend the bill be amended to show change 1.  
I recommend the bill be amended to show change 2.  
```
Alternatively, the whole recommendation can be kept as a single sentence. The approach depends on:  
- Whether the points belong to different Change Types or Action Categories.  
- Whether the focus is on changing the law or listing specific details.  

There may be more than one correct way to structure a recommendation. The key consideration is whether the text remains readable in the Inquiries table.  

## 2. Adding Change Type and Action-Based Category  

### Some interpretation needed in this step  

We have used AI (GPT-4o) to help define categories based on an early version of `data.json`. As more data is added, these categories may need to change.  

Change Types and Action Categories are more flexible than the wording of recommendations. AI can assist, but it has not been reliable enough to replace human review.  

GitHub Copilot has been useful for formatting initial suggestions, but it does not fully capture the meaning of recommendations. A person must check and correct every Change Type and Action Category.  

**Tip:** Use a split-screen view with `data.json` open next to the list of Action-Based Categories and Change Types for easy reference.  

### Choosing the right Change Type  

- `More` – Continue doing something that is already working.  
- `Cease` – Stop a policy or practice.  
- `Different` – Modify something rather than creating a new action.  

### Choosing the right Action Category  

Some recommendations could fit into multiple categories. Consider what needs to change in practice to prevent the issue happening again.  

- `Processes & Procedures` or `Law & Regulation` – Does the recommendation change how things are done, or does it require a legal change?  
- `Communication & Reporting`, `Technology & Systems`, or `Documentation & Records` – Does it require automation, or is it about information sharing?  
- `Infrastructure & Facilities` – Includes physical equipment or devices provided to staff.  
- `Investigation & Redress` vs `Audits & Reviews` – Is the recommendation about reviewing corrective actions or setting up ongoing audits?  

Refer to `data.json` to see how categories have been applied.  

## 3. Peer review and proofreading  

All changes are reviewed by a second person before they are finalised.  

---  

This version is clearer, more structured, and easier to read while keeping all the key details. Let me know if you’d like any further tweaks!