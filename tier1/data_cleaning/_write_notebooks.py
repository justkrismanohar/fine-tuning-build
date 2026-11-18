"""Write the two data-cleaning notebooks. Self-contained for Colab."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GH = "justkrismanohar/fine-tuning-build"
COLAB = f"https://colab.research.google.com/github/{GH}/blob/main/tier1/data_cleaning"
BADGE = "https://colab.research.google.com/assets/colab-badge.svg"

HOW = """
**How to use this notebook**

1. **Runtime → Change runtime type → CPU** (not GPU), or run in the course Jupyter.
2. Click ▶ on each cell from the top, or **Runtime → Run all**.
3. Read the note *under* a cell after it runs.
4. Change **only** lines marked `# [CHANGE]`.
5. Nothing from work goes in a cell. CivicDesk names are fiction.
"""


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.strip("\n").split("\n")]}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in text.strip("\n").split("\n")],
    }


def nb(cells: list[dict]) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "colab": {"provenance": [], "toc_visible": True},
        },
        "cells": cells,
    }


def write(name: str, cells: list[dict]) -> None:
    path = HERE / name
    path.write_text(json.dumps(nb(cells), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", path.name)


def colab_line(name: str) -> str:
    return f"[![Open In Colab]({BADGE})]({COLAB}/{name})"


write(
    "DC-01_keep_or_throw.ipynb",
    [
        md(
            f"""# DC-01 Keep, throw, or send back

**Time:** ~20 minutes &nbsp;|&nbsp; **Need:** a browser. No GPU. No extra packages.

{colab_line("DC-01_keep_or_throw.ipynb")}

Or **File → Upload notebook** at [colab.research.google.com](https://colab.research.google.com/).

{HOW}

A search pile will quote **whatever you put in it**. This notebook is the first government question: *may this page go in at all?*
"""
        ),
        md(
            """## Three buckets

| Bucket | Meaning | CivicDesk example |
|---|---|---|
| **INDEX** | Approved rule, you can select the text, id and clearance are filled | Vacancy Handbook C2 |
| **NEVER** | Names a person, a Cabinet *body*, ops notes, a live system dump | A real CV; a burgess form |
| **HOLD** | Not ready: no selectable text, OCR junk, missing circular number, letterhead soup | “page 4 of 88” printed over the rule |

**Class metadata** (“a Cabinet-class item exists”) is not the minute. You may INDEX a stub that sends the clerk to a records officer. The **body** stays NEVER.
"""
        ),
        md(
            """## Government gotchas (read once)

1. **Letterhead is not the rule.** Repeated “Ministry of … / page 4 of 88 / CONFIDENTIAL” will be retrieved as if it were the circular.
2. **A scan with no text is empty.** An image-only PDF looks like a document to a person. To the index it is nothing, or OCR garbage. HOLD. Do not upload a real page to Colab to “try OCR.”
3. **`1` that is really `l`.** Bad OCR (`app1icant`, `ho1d`) becomes a fluent wrong quote.
4. **A name walked in.** A CV, a referee, a burgess household, a live GLPI ticket — NEVER, even “just to try.”
5. **Two dates, one story.** A 2019 circular sitting next to the 2026 replacement, with no version label, is HOLD until Records says which is current.
6. **Cleaning is not rewriting.** You strip junk. You do not “improve” the legal sentence.
7. **Finding it ≠ allowed to see it.** That is Day 2 (T1-10). Today is only: does it enter the pile?
"""
        ),
        md("## 1. Label these (government desk, all fiction)"),
        code(
            """# [CHANGE] each value: index / never / hold
GUESSES = {
    "Vacancy Handbook C2, selectable text, id HB-VAC-C2, clearance internal": "index",
    "A real applicant CV exported from e-recruitment": "never",
    "Image-only PDF of the overnight-attachment circular, no selectable text": "hold",
    "OCR: 'C2. The app1icant must ho1d a diploma' plus 'page 4 of 88'": "hold",
    "Cabinet minute BODY on coastal security": "never",
    "A stub that only says 'Cabinet-class item exists — ask Records'": "index",
    "Burgess application with household names and a Couva address": "never",
    "Handbook paragraph with no circular number and no clearance": "hold",
    "2019 attachment circular next to the 2026 replacement, neither labelled current": "hold",
    "GLPI extract of this month's live tickets": "never",
}

gold = {
    "Vacancy Handbook C2, selectable text, id HB-VAC-C2, clearance internal": "index",
    "A real applicant CV exported from e-recruitment": "never",
    "Image-only PDF of the overnight-attachment circular, no selectable text": "hold",
    "OCR: 'C2. The app1icant must ho1d a diploma' plus 'page 4 of 88'": "hold",
    "Cabinet minute BODY on coastal security": "never",
    "A stub that only says 'Cabinet-class item exists — ask Records'": "index",
    "Burgess application with household names and a Couva address": "never",
    "Handbook paragraph with no circular number and no clearance": "hold",
    "2019 attachment circular next to the 2026 replacement, neither labelled current": "hold",
    "GLPI extract of this month's live tickets": "never",
}

right = 0
for item, want in gold.items():
    got = GUESSES[item].strip().lower()
    ok = got == want
    right += int(ok)
    print(("OK   " if ok else "WRONG"), f"{got:6} want={want:6}", "—", item)
print(f"score {right}/{len(gold)}")
print("If unsure, HOLD. NEVER is for people, Cabinet bodies, and live systems.")
"""
        ),
        md(
            """### Teaching note

- **INDEX** is rare and boring: an approved handbook line you can copy and cite.
- **NEVER** is the data ban you already heard on Day 1. A “small sample” of live tickets is still NEVER.
- **HOLD** is the desk being honest: this page is not ready. Send it back. Do not invent text in Colab.
"""
        ),
        md("## 2. Which gotcha is this?"),
        code(
            """# [CHANGE] pick from: letterhead / ocr / scan / pii / stale / rewrite
GUESSES = {
    "The retrieved quote is 'page 4 of 88 CONFIDENTIAL' and then C2": "letterhead",
    "The quote says 'The app1icant must ho1d a diploma'": "ocr",
    "Staff uploaded a photographed circular; copy-paste from the PDF is empty": "scan",
    "A 'handbook' chunk includes 'Maya Reid, National ID 999-00-1111'": "pii",
    "Search returns Circular 12 of 2019 after Circular 12 of 2026 replaced it": "stale",
    "Someone 'cleaned' C2 into 'the person should probably have a diploma'": "rewrite",
}

gold = {
    "The retrieved quote is 'page 4 of 88 CONFIDENTIAL' and then C2": "letterhead",
    "The quote says 'The app1icant must ho1d a diploma'": "ocr",
    "Staff uploaded a photographed circular; copy-paste from the PDF is empty": "scan",
    "A 'handbook' chunk includes 'Maya Reid, National ID 999-00-1111'": "pii",
    "Search returns Circular 12 of 2019 after Circular 12 of 2026 replaced it": "stale",
    "Someone 'cleaned' C2 into 'the person should probably have a diploma'": "rewrite",
}

right = 0
for item, want in gold.items():
    got = GUESSES[item].strip().lower()
    ok = got == want
    right += int(ok)
    print(("OK   " if ok else "WRONG"), f"{got:10} want={want:10}", "—", item[:70])
print(f"score {right}/{len(gold)}")
"""
        ),
        md(
            """## Done

You should be able to say, for a government page: **INDEX, NEVER, or HOLD** — and name the gotcha if it is HOLD.

Next: **DC-02** (strip junk, keep the rule, fill the labels).
"""
        ),
    ],
)

write(
    "DC-02_clean_then_label.ipynb",
    [
        md(
            f"""# DC-02 Clean a page, then label it

**Time:** ~25 minutes &nbsp;|&nbsp; **Need:** a browser. No GPU. No extra packages.

{colab_line("DC-02_clean_then_label.ipynb")}

Or **File → Upload notebook** at [colab.research.google.com](https://colab.research.google.com/).

{HOW}

Cleaning here = make an *approved* paragraph searchable and honest. It is **not** pandas on a live extract, and it is **not** rewriting the law.
"""
        ),
        md(
            """## What “clean” means on a government page

Keep:

- the circular number and the rule, word for word
- the office that issued it, the date, the clearance

Throw out:

- repeated letterheads and “page n of m”
- watermarks (`CONFIDENTIAL` copied onto a public handbook)
- OCR digits that were letters
- names, IDs, live ticket numbers

If you cannot get selectable text, **HOLD**. Do not run OCR on a real page in Colab.
"""
        ),
        md("## 1. Strip the soup — keep C2"),
        code(
            r'''# [CHANGE] CLEAN must be the handbook sentence only. Do not "improve" the wording.
RAW = """CivicDesk Vacancy Handbook v3          page 4 of 88
C2. The app1icant must ho1d a recognised diploma in records management or equivalent.
CONFIDENTIAL — do not circulate            page 4 of 88
"""

CLEAN = "C2. The applicant must hold a recognised diploma in records management or equivalent."

print("RAW:")
print(RAW)
print("---")
print("CLEAN:")
print(CLEAN)

low = CLEAN.lower()
problems = []
if "page 4" in low or "confidential" in low:
    problems.append("header/footer still present")
if "app1icant" in low or "ho1d" in low:
    problems.append("OCR digit-for-letter still present")
if "records management" not in low:
    problems.append("the actual rule disappeared")
if "c2" not in low:
    problems.append("criterion id disappeared")
if "should probably" in low or "maybe" in low:
    problems.append("you rewrote the rule — that is not cleaning")
if problems:
    print("HOLD — still dirty:")
    for p in problems:
        print(" ", p)
else:
    print("Text is INDEX-ready. Next cell: labels that travel with it.")
'''
        ),
        md(
            """### Teaching note

The gold line is already in the cell so you can see the target. The skill is *seeing* why RAW must not be indexed. A production desk re-types from the approved file or re-scans. Colab is not that desk.
"""
        ),
        md("## 2. A second page — overnight attachments (Finance-shaped)"),
        code(
            r'''# [CHANGE] keep the rule; drop the email thread and the footer.
RAW = """From: A. Clerk  To: Whole floor
pls see attached, PS said this is the rule now??
---
CivicDesk Records Office  Circular HB-ATTACH-04   1 March 2024
Attachments may sit overnight only in the approved file store, not in personal email
and not in a public chatbot.
This email is confidential.  page 1 of 1
"""

CLEAN = (
    "Attachments may sit overnight only in the approved file store, "
    "not in personal email and not in a public chatbot."
)

print(CLEAN)
low = CLEAN.lower()
problems = []
if "pls see" in low or "ps said" in low:
    problems.append("email thread is not the circular")
if "page 1 of 1" in low or "this email is confidential" in low:
    problems.append("footer still present")
if "approved file store" not in low:
    problems.append("the rule disappeared")
if problems:
    print("HOLD:")
    for p in problems:
        print(" ", p)
else:
    print("Keep the circular. Throw the email. An inbox is not a handbook.")
'''
        ),
        md(
            """## 3. Labels that travel with the paragraph

A chunk **missing** `id` or `clearance` is HOLD, even if the text is clean.

| Field | Why a government desk cares |
|---|---|
| `id` | So you can say later “this chunk was / was not in the index” |
| `title` | Human name of the circular |
| `source` | Handbook or circular number — not “the model told us” |
| `date` | Stale rules must not masquerade as current |
| `creator` | An **office**, never a name from a CV |
| `clearance` | internal / restricted / public — a hit is not permission |
"""
        ),
        code(
            """# [CHANGE] fill every quoted value. Fiction only.
CHUNK = {
    "id": "HB-VAC-C2",
    "title": "Vacancy Handbook v3 — criterion C2",
    "creator": "CivicDesk Records Office",
    "date": "2024-03-01",
    "source": "CivicDesk Vacancy Handbook v3",
    "clearance": "internal",
    "text": "C2. The applicant must hold a recognised diploma in records management or equivalent.",
}

required = ["id", "title", "source", "clearance", "text"]
missing = [k for k in required if not str(CHUNK.get(k, "")).strip()]
for k, v in CHUNK.items():
    print(f"{k:12} {v}")
print()
if missing:
    print("HOLD — empty:", ", ".join(missing))
elif not CHUNK["id"].startswith("HB-"):
    print("HOLD — id should look like HB-…")
elif CHUNK["clearance"] not in {"internal", "restricted", "public"}:
    print("HOLD — clearance is internal / restricted / public")
else:
    print("INDEX-ready. Day 2 stores these labels beside the paragraph, not inside the model.")
print("Creator is an office. A name from a CV would make this NEVER.")
"""
        ),
        md(
            """## 4. Two versions of the same circular

If 2019 and 2026 both say “Circular 12” and neither is labelled **current**, HOLD both until Records says which one the desk uses. Do not let search retrieve the old one because it “looks similar.”
"""
        ),
        code(
            """# [CHANGE] current / stale / hold
GUESSES = {
    "HB-ATTACH-04, 1 March 2024, marked current by Records": "current",
    "HB-ATTACH-04, 12 June 2019, superseded note on the 2024 file": "stale",
    "Two undated photocopies both headed Circular 12": "hold",
}

gold = {
    "HB-ATTACH-04, 1 March 2024, marked current by Records": "current",
    "HB-ATTACH-04, 12 June 2019, superseded note on the 2024 file": "stale",
    "Two undated photocopies both headed Circular 12": "hold",
}
right = 0
for item, want in gold.items():
    got = GUESSES[item].strip().lower()
    ok = got == want
    right += int(ok)
    print(("OK   " if ok else "WRONG"), got, "—", item)
print(f"score {right}/{len(gold)}")
print("Stale circulars stay out of the pile, or sit in a clearly labelled archive that search does not use.")
"""
        ),
        md(
            """## Done

You should be able to:

- strip letterhead and OCR junk **without rewriting** the rule
- refuse an email thread posing as policy
- fill `id`, `source`, `date`, `clearance`
- HOLD when two undated copies fight

Day 2 **T1-07** is the scored INDEX / NEVER drill. Day 2 **T1-10** is the access gate (a hit is not permission).
"""
        ),
    ],
)
