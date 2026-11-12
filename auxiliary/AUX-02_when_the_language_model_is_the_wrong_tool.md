# AUX-02 When a language model is the wrong tool

**Self-taught. 40 minutes. No GPU.**

Several EOIs describe jobs that look like “AI” but are not generation.

## Who this is for

- **Defence (assets):** “Which licences expire this month?”
- **MOWI:** GIS / project fields, risk flags, dashboards.
- **TTDF:** routes, radar, weather, landing patterns.
- **CPO:** statistical validation of costing figures.
- **Trade:** ticket counts and containment rates (after the fact).

## A simple test

Ask: **is the answer already in a table, or must a sentence be written?**

| Job | Better tool | Language model role, if any |
|---|---|---|
| Licences expiring in 30 days | SQL / report on the register | Optional: turn the table into a paragraph, still showing the rows |
| Server X hosts which VMs? | Asset CMDB | NL interface *over the CMDB*, never over model memory |
| Grade vs a rubric | Could be LM **if** the work is prose | Rubric of checkboxes is not an LM job |
| Patrol pattern by moon and tide | Classical ML / stats on tabular data | LM must not invent a route |
| “What does OPR say about $65,000?” | RAG over OPR text | This *is* an LM + retrieval job |

## Exercise

Take your EOI. Split it into:

- **A.** Rows that should be queried (N10).
- **B.** Paragraphs that should be retrieved and cited (N3).
- **C.** Labels that need a quote from the applicant/article (N1).
- **D.** Predictions over sensors or GIS (N15) — out of this course.

If C or D is the whole paper, write that on your transfer card: *language model is not the first intervention.*

## Stop

Do not fine-tune a model to remember licence expiry dates. Update the register.
