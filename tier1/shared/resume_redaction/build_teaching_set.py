"""Deterministic builder for the T1-05 teaching set (7 worked documents) and the shared redaction policy.

Labels come from the listed field values, never from a model. Spans = every exact occurrence
of each listed value; longer values win where they overlap (an email that contains a name is
one EMAIL span). Expected output = original with each span replaced by its placeholder.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY = {
    "version": "T1-05-policy-v1",
    "redact": {
        "PERSON": "Name of the applicant, referees, or any other private individual named in the text",
        "EMAIL": "Any email address, including spelled-out forms such as 'name dot x at y dot z'",
        "PHONE": "Any phone number, in any format",
        "ADDRESS": "Home or postal address (street, lot, village or town line)",
        "DOB": "Date of birth",
        "ID": "National ID or other personal identification number",
    },
    "keep": [
        "Employer and institution names, even when they contain a family name",
        "Job titles, duties, dates of employment, qualifications, skills, numbers about the work",
        "Vacancy or document reference numbers",
    ],
    "placeholders": ["[PERSON]", "[EMAIL]", "[PHONE]", "[ADDRESS]", "[DOB]", "[ID]"],
    "out_of_scope": "Photographs, scanned images, non-English text, documents over the token budget: not processed, routed to manual.",
}

DOCS = [
    {
        "id": "R01",
        "layout": "standard headed CV",
        "text": (
            "# Anika Ramnarine\n"
            "Email: anika.ramnarine@example.invalid | Phone: 868-555-0142\n"
            "Address: 14 Cedar Grove Trace, Fictionville\n"
            "\n"
            "## Experience\n"
            "- Records Officer, CivicDesk Central Registry, 2019-2025: indexed 12,000 files a year.\n"
            "\n"
            "## Education\n"
            "- BSc Information Management, University of Fictionville, 2018\n"
            "\n"
            "## Skills\n"
            "Retention schedules, EDMS indexing, spreadsheets\n"
        ),
        "pii": [
            ["PERSON", "Anika Ramnarine"],
            ["EMAIL", "anika.ramnarine@example.invalid"],
            ["PHONE", "868-555-0142"],
            ["ADDRESS", "14 Cedar Grove Trace, Fictionville"],
        ],
        "keep": [
            "Records Officer, CivicDesk Central Registry, 2019-2025",
            "indexed 12,000 files a year",
            "BSc Information Management, University of Fictionville, 2018",
            "Retention schedules, EDMS indexing, spreadsheets",
        ],
        "form": {"name": "Anika Ramnarine", "email": "anika.ramnarine@example.invalid", "phone": "868-555-0142"},
        "tests": "Baseline case: every identifier on its own labelled line.",
    },
    {
        "id": "R02",
        "layout": "CV with date of birth, ID and a referee block",
        "text": (
            "# Curriculum vitae: Tevin Okonkwo-Sealy\n"
            "Date of birth: 03/07/1994\n"
            "National ID: CD-ID-1994-0377\n"
            "Email: tevin.os@example.org\n"
            "\n"
            "## Experience\n"
            "- Lands Clerk, CivicDesk Lands Office, 2017-2024: processed survey plan requests.\n"
            "\n"
            "## Referees\n"
            "- Gail Ramsaran, Former Supervisor, CivicDesk Lands Office, 868-555-0177, g.ramsaran@example.invalid\n"
        ),
        "pii": [
            ["PERSON", "Tevin Okonkwo-Sealy"],
            ["DOB", "03/07/1994"],
            ["ID", "CD-ID-1994-0377"],
            ["EMAIL", "tevin.os@example.org"],
            ["PERSON", "Gail Ramsaran"],
            ["PHONE", "868-555-0177"],
            ["EMAIL", "g.ramsaran@example.invalid"],
        ],
        "keep": [
            "Lands Clerk, CivicDesk Lands Office, 2017-2024",
            "processed survey plan requests",
            "Former Supervisor, CivicDesk Lands Office",
        ],
        "form": {"name": "Tevin Okonkwo-Sealy", "email": "tevin.os@example.org", "phone": "868-555-0190"},
        "tests": "Referee contact details at the end; DOB and ID lines.",
    },
    {
        "id": "R03",
        "layout": "short profile with the first name repeated in prose",
        "text": (
            "Name: Oyelaran Dookhie\n"
            "Contact: (868) 555 0119 / o.dookhie@example.org\n"
            "Address: LP 27, Branch Road, Fictionville Village\n"
            "\n"
            "## Profile\n"
            "Oyelaran built the service-desk queue dashboard and reduced average queue time by 30%.\n"
            "\n"
            "## Experience\n"
            "- ICT Support Officer, CivicDesk Trade Unit, 2020-2025\n"
        ),
        "pii": [
            ["PERSON", "Oyelaran Dookhie"],
            ["PERSON", "Oyelaran"],
            ["PHONE", "(868) 555 0119"],
            ["EMAIL", "o.dookhie@example.org"],
            ["ADDRESS", "LP 27, Branch Road, Fictionville Village"],
        ],
        "keep": [
            "built the service-desk queue dashboard",
            "reduced average queue time by 30%",
            "ICT Support Officer, CivicDesk Trade Unit, 2020-2025",
        ],
        "form": {"name": "Oyelaran Dookhie", "email": "o.dookhie@example.org", "phone": "868-555-0119"},
        "tests": "Unfamiliar first name used alone in prose; phone with brackets and spaces.",
    },
    {
        "id": "R04",
        "layout": "CV where the employer carries the applicant's family name",
        "text": (
            "# Keisha Ramdass\n"
            "Phone: +1 (868) 555-0161 | Email: keisha.r@example.invalid\n"
            "\n"
            "## Experience\n"
            "- Accounts Clerk, Ramdass & Sons Hardware Ltd, 2016-2021: reconciled supplier invoices.\n"
            "- Accounts Officer, CivicDesk Finance Unit, 2021-2025\n"
            "\n"
            "## Education\n"
            "- ACCA Applied Knowledge, 2019\n"
        ),
        "pii": [
            ["PERSON", "Keisha Ramdass"],
            ["PHONE", "+1 (868) 555-0161"],
            ["EMAIL", "keisha.r@example.invalid"],
        ],
        "keep": [
            "Accounts Clerk, Ramdass & Sons Hardware Ltd, 2016-2021",
            "reconciled supplier invoices",
            "Accounts Officer, CivicDesk Finance Unit, 2021-2025",
            "ACCA Applied Knowledge, 2019",
        ],
        "form": {"name": "Keisha Ramdass", "email": "keisha.r@example.invalid", "phone": "868-555-0161"},
        "tests": "Policy keeps employer names; a family business name is a quasi-identifier the policy owner must rule on.",
    },
    {
        "id": "R05",
        "layout": "informal contact line with a spelled-out email",
        "text": (
            "# Rajiv Persaud\n"
            "Reach me: rajiv dot persaud at example dot invalid, or 868 555 0133 (WhatsApp)\n"
            "\n"
            "## Experience\n"
            "- Data Entry Clerk, CivicDesk Permits Office, 2022-2025: keyed 300 permit forms a week.\n"
        ),
        "pii": [
            ["PERSON", "Rajiv Persaud"],
            ["EMAIL", "rajiv dot persaud at example dot invalid"],
            ["PHONE", "868 555 0133"],
        ],
        "keep": [
            "Data Entry Clerk, CivicDesk Permits Office, 2022-2025",
            "keyed 300 permit forms a week",
        ],
        "form": {"name": "Rajiv Persaud", "email": "rajiv.persaud@example.invalid", "phone": "868-555-0133"},
        "tests": "Obfuscated email: pattern checks and exact form matching both miss it.",
    },
    {
        "id": "R06",
        "layout": "cover-letter prose with inline address and a third person named",
        "text": (
            "My name is Sharleen Bisnath and I live at 9 Hillview Road, Fictionville. "
            "You can reach me on 868-555-0188.\n"
            "\n"
            "I have worked as a Health Records Assistant at CivicDesk District Clinic since 2021, "
            "where I maintain appointment registers for 4 clinics.\n"
            "\n"
            "My mentor, Dr. Imran Sookdeo, encouraged me to apply for this post.\n"
            "\n"
            "## Qualifications\n"
            "- Diploma in Health Information, Fictionville Technical Institute, 2020\n"
        ),
        "pii": [
            ["PERSON", "Sharleen Bisnath"],
            ["ADDRESS", "9 Hillview Road, Fictionville"],
            ["PHONE", "868-555-0188"],
            ["PERSON", "Imran Sookdeo"],
        ],
        "keep": [
            "Health Records Assistant at CivicDesk District Clinic since 2021",
            "maintain appointment registers for 4 clinics",
            "Diploma in Health Information, Fictionville Technical Institute, 2020",
        ],
        "form": {"name": "Sharleen Bisnath", "email": "s.bisnath@example.invalid", "phone": "868-555-0188"},
        "tests": "Identifiers inside sentences, not on labelled lines; a third party who is not a referee.",
    },
    {
        "id": "R07",
        "layout": "vacancy notice extract with no personal data",
        "text": (
            "# Vacancy notice extract\n"
            "Vacancy ref: CD-2024-117-3302\n"
            "Position: Records Assistant, CivicDesk Central Registry\n"
            "Requirements: diploma in records management or equivalent; two years' experience.\n"
        ),
        "pii": [],
        "keep": [
            "Vacancy ref: CD-2024-117-3302",
            "Records Assistant, CivicDesk Central Registry",
            "diploma in records management or equivalent",
        ],
        "form": None,
        "tests": "No PII at all: anything masked is over-redaction. The reference number looks like a phone number to a loose pattern.",
    },
]


def find_spans(text: str, pii: list[list[str]]) -> list[dict]:
    cands = []
    for typ, value in pii:
        start = 0
        found = False
        while True:
            i = text.find(value, start)
            if i < 0:
                break
            cands.append((i, i + len(value), typ, value))
            found = True
            start = i + 1
        if not found:
            raise ValueError(f"label value not in text: {value!r}")
    # longest first; drop any candidate overlapping an accepted span
    cands.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
    taken: list[tuple[int, int, str, str]] = []
    for c in cands:
        if all(c[1] <= t[0] or c[0] >= t[1] for t in taken):
            taken.append(c)
    taken.sort()
    return [{"type": t, "text": v, "start": s, "end": e} for s, e, t, v in taken]


def redact(text: str, spans: list[dict]) -> str:
    out = text
    for sp in sorted(spans, key=lambda s: -s["start"]):
        out = out[: sp["start"]] + f"[{sp['type']}]" + out[sp["end"] :]
    return out


def build() -> dict:
    docs = []
    for d in DOCS:
        spans = find_spans(d["text"], d["pii"])
        expected = redact(d["text"], spans)
        for k in d["keep"]:
            if k not in d["text"] or k not in expected:
                raise ValueError(f"{d['id']}: keep anchor lost by the answer key: {k!r}")
        docs.append({
            "id": d["id"], "layout": d["layout"], "tests": d["tests"], "text": d["text"],
            "spans": spans, "expected": expected, "keep": d["keep"], "form": d["form"],
        })
    body = {"policy": POLICY, "docs": docs}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {
        "fixture_version": "teaching-set-v1",
        "split": "teaching (worked example only; not the benchmark, never training data)",
        "provenance": "Synthetic. Written by the course author from fictional field values. Labels derived deterministically from those values, not by a model. No real person's data.",
        "sha256": digest,
        **body,
    }


if __name__ == "__main__":
    fx = build()
    (Path(__file__).resolve().parent / "data" / "teaching_set_v1.json").write_text(json.dumps(fx, indent=2, ensure_ascii=False), encoding="utf-8")
    for d in fx["docs"]:
        print(d["id"], len(d["spans"]), "spans", [s["type"] for s in d["spans"]])
    print("sha256", fx["sha256"][:12])
