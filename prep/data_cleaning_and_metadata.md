# Data cleaning and metadata basics — send with the repo

This page is the **pack** to attach when you share `course/`. It is literacy for CivicDesk / Day 2, not a ministry ETL course and not permission to upload scans.

**Do this:** skim the table, open the two official pages, then run [PREP-02b](PREP-02b_clean_and_label.ipynb) in Colab (CPU, ~25–35 min). CivicDesk fiction only.

**Do not:** install Tesseract or pandas; OCR a real circular; paste CVs, Cabinet bodies, burgess forms, or patrol notes.

## What “cleaning” and “metadata” mean here

A language model will retrieve **whatever you stored**. Garbage in the pile becomes a fluent wrong citation.

| Word | CivicDesk meaning | Not this |
|---|---|---|
| **Cleaning** | Make a *searchable, honest* copy of an *approved* paragraph: strip repeated headers/footers, refuse image-only PDFs until there is selectable text, keep PII out | Recoding a live EDMS extract in pandas |
| **Metadata** | Labels that **travel with** the paragraph: id, title, date, source, clearance, rights | The paragraph itself; a ChatGPT summary of the file |
| **Dataset card** | One page that says what is in the *pile*, who may use it, licence | A **model** card (T1-04 — who published OLMo/Phi) |

Day 2 T1-07 still drills **INDEX vs NEVER**. Real desks also need a third bucket:

| Bucket | Use when | Classroom drill |
|---|---|---|
| **INDEX** | Approved rule, selectable text, id + clearance filled | May enter the pile |
| **NEVER** | PII, Cabinet *body*, ops notes, canary, live register dump | Must not enter |
| **HOLD** | Image-only scan, OCR garbage, missing id/date/clearance, header soup | Send back for a clean copy. In T1-07, treat HOLD as **NEVER** for the scoring cell |

Finance-shaped note: **class metadata** (“a Cabinet-class item exists”) is not the same as indexing the **body**. T1-10 is the access gate.

## CivicDesk fields ↔ Dublin Core

You do not need to become a cataloguer. These six labels are enough for the classroom pile. Names follow [Dublin Core](https://www.dublincore.org/specifications/dublin-core/dces/) so records staff recognise them.

| CivicDesk field (Day 2 chunks) | Dublin Core | Why it exists |
|---|---|---|
| `id` (e.g. `HB-VAC-C2`) | **Identifier** | So you can cite and audit “this chunk was / was not in the index” (N14) |
| `title` | **Title** | Human name of the circular or handbook section |
| `citation` / handbook name | **Source** | Where the paragraph was copied from |
| `stands_in_for` | **Subject** (classroom only) | Which EOI type this fiction stands in for |
| `clearance` | **Rights** / accessRights | Clerk vs records-officer; a hit is not permission (N4) |
| date of the circular (when you have it) | **Date** | Stale circulars should not masquerade as current |
| who published the rule | **Creator** / Publisher | A vacancy handbook is not “the model”; it is Records Office |

A chunk **missing** identifier or clearance is **HOLD**, not INDEX.

## What the course already rehearses

| Where | What you practise |
|---|---|
| **PREP-02** | INDEX vs NEVER; retrieve then cite or abstain |
| **PREP-02b** (this pack) | HOLD; messy vs clean text; fill a metadata form; dataset card vs model card |
| **T1-07** | Score CI-01…CI-10 INDEX/NEVER; metadata = `id`, `clearance`, `citation` |
| **T1-08** | Search only `index_ok: true` chunks |
| **T1-10** | Same hit, wrong role |
| **T1-11** | Inspect an SFT JSONL: splits, canaries, refuse dirty rows — still not a cleaning factory |

Tier 2 of the workplan (dataset sheet, de-identification, train/held-out) is **not** this three-day path.

## Online resources (open in a browser)

### Everyone (about 20–30 minutes total)

1. [Dublin Core — Creating Metadata](https://www.dublincore.org/resources/userguide/creating_metadata/) — skim **Title, Creator, Date, Identifier, Rights, AccessRights**. Stop. You will not write RDF.
2. [Dublin Core Metadata Element Set (15 elements)](https://www.dublincore.org/specifications/dublin-core/dces/) — the named list. Current documentation of the same terms: [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/).
3. [Hugging Face — Dataset cards](https://huggingface.co/docs/hub/datasets-cards) — what is in the *data*, licence, intended use. Different from a [model card](https://huggingface.co/docs/hub/model-cards) (T1-04).

### Paper → softcopy (awareness only)

4. [Tesseract — Improving the quality of the output](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html) — headings only: resolution, contrast, skew, image-only vs searchable PDF. **Do not install. Do not upload a real page.** A bad scan becomes a bad index. Classroom action is **HOLD**, not “run OCR in Colab.”

### Optional primer (records / IM staff)

5. [NISO, Understanding Metadata (2017 primer)](https://www.niso.org/publications/understanding-metadata-2017) — what metadata *is for* (find, identify, select, obtain). Cultural-heritage examples; map them to circulars and handbooks, not museum objects.

### Technical staff only (tables, not scans)

6. [10 minutes to pandas](https://pandas.pydata.org/docs/user_guide/10min.html) and [Working with missing data](https://pandas.pydata.org/docs/user_guide/missing_data.html) — toy tables. Never a ministry extract. Day 2 is still INDEX vs NEVER, not a pandas lab.

## One-page dataset sheet (print if you like)

Fill this for *CivicDesk fiction* or an approved public circular. Leave ministry files out.

```text
Title / Identifier:  HB-________
Creator / office:    
Date of the rule:    
Source (handbook, circular no.):    
Clearance:           internal / restricted / public
Rights / may it leave the building?:  
Selectable text?     yes / no (if no → HOLD)
PII or ops content?  no / yes (if yes → NEVER)
INDEX / NEVER / HOLD:
```

## Honest claim

**Safe to say:** after this pack a participant can refuse a dirty or classed file, name the labels that must sit on a chunk, and not confuse a dataset card with a model card.

**Unsafe to say:** they can clean an EDMS export, run production OCR, or de-identify CVs for training.
