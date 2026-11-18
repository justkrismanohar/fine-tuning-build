# Data cleaning in a government desk — CivicDesk

**Not a contact-hour lab.** Run these two notebooks on your own, in **Google Colab** (CPU) or in the course Jupyter. About **40–50 minutes** together.

A language model will quote **whatever you stored**. Dirty pages become fluent wrong citations. This folder is how a public-service desk decides what may enter a search pile — and how to make an approved page honest — **without** pasting ministry files.

**CivicDesk fiction only.** No real CVs, Cabinet bodies, burgess forms, health records, patrol notes, or live ticket dumps.

## Open in Colab

Runtime → **CPU** → Run all. Or **File → Upload notebook** if the badge cannot reach GitHub.

| Notebook | Time | What you practise |
|---|---|---|
| [DC-01 Keep, throw, or send back](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/tier1/data_cleaning/DC-01_keep_or_throw.ipynb) | ~20 min | Three buckets, with government examples |
| [DC-02 Clean a page, then label it](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/tier1/data_cleaning/DC-02_clean_then_label.ipynb) | ~25 min | Strip junk, keep the rule, fill the labels |

## The three buckets

| Bucket | Meaning | Example |
|---|---|---|
| **INDEX** | Approved rule, readable text, id and clearance filled | Vacancy Handbook C2 |
| **NEVER** | Identifies a person, a Cabinet *body*, ops notes, live systems | A real CV; patrol notes |
| **HOLD** | Not ready: scan with no text, OCR junk, missing circular number, header soup | “page 4 of 88” over the rule |

Day 2 (T1-07) scores INDEX vs NEVER. HOLD in that scoring cell counts as NEVER until a clean copy exists.

## What this is not

You will not clean an EDMS export, run production OCR, or de-identify CVs for training. Those stay **out**.

Prep pack with official links: [`../../prep/data_cleaning_and_metadata.md`](../../prep/data_cleaning_and_metadata.md).
