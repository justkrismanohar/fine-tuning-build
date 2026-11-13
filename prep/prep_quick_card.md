# Prep quick card — bring to Day 1 if you want

Read list: `readings.md` (Hugging Face ch. 1, OSI Open Source AI, Dublin Core + dataset cards for PREP-02b, model cards / Hub security for technical staff, OWASP + NIST for IT/policy). Cleaning pack to send with the repo: `data_cleaning_and_metadata.md`. Python: PREP-00b is enough; Tutorial 1–4 is optional.

## Python you will *see* (you do not write programs)

```
# [CHANGE]  → edit the text inside "quotes" only
NAME = "demo"              # a label
print(NAME)                # show it underneath
lab.chat("a question")     # toolbox.action(input)
form = { "field": "value" }
```

Red error: usually a missing `"`. Undo. Do not rewrite the cell.

## Data ban

No real CVs, Cabinet/EDMS, case, health, burgess, patrol, passwords, live serials.

## Three boxes

**Prompt** (what you type) → **API / notebook** (the door) → **weights** (the frozen files that guess the next token).

The weights are not your EDMS.

## Two roles in a chat

- **system** = standing instruction on the wall (never hire, never reset a password)
- **user** = this visitor’s sentence

## Five labels you will hear on Day 2

| Label | One line |
|---|---|
| prompt | Same model, better wall instruction |
| RAG | Find an approved paragraph, then answer from it |
| integration | Query a register / ticket store — not the model |
| fine-tune | Small extra file on frozen weights (inspect, don’t train) |
| none | Maybe no language model, or the act is banned |

## INDEX / NEVER / HOLD

- **INDEX** — approved rule, selectable text, `id` + clearance filled
- **NEVER** — PII, Cabinet body, ops notes, canary
- **HOLD** — image-only scan, OCR junk, missing id — send back (T1-07 scores HOLD as NEVER)

Metadata travels **with** the chunk (Dublin Core: Identifier, Title, Date, Source, Rights). Dataset card ≠ model card.

## Cite or abstain

If the paragraph is not there: **I cannot cite. Stop.** Do not invent a circular number.

## Access ≠ retrieval

A search hit is not permission. Clerk ≠ records officer.

## Saying ≠ doing

Draft a ticket: allowed. Reset password / award / hire / write GLPI: banned.
