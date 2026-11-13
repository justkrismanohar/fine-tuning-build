"""Deterministic builder for the frozen, held-out resume-redaction benchmark (Day 1 baseline, Day 3 reuse).

Everything is fictional. Labels come from the field values used to render each document, never from a
model. Name, street and email pools are split: the 'test' pools below are reserved for this benchmark
and must never be used to build Day 3 training or validation data.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from build_teaching_set import POLICY, find_spans, redact

BENCH_VERSION = "resume-redaction-test-v1"
SEED = 20261112
N_PII_DOCS = 35  # 7 layouts x 5
N_NO_PII_DOCS = 5

# Reserved for the TEST split only.
TEST_POOLS = {
    "first": ["Anjali", "Darnell", "Ifeoma", "Kavita", "Marlon", "Nadira", "Quincy", "Renuka", "Shivon",
              "Tariq", "Umeko", "Vashti", "Wendell", "Yolanda", "Zahir", "Chiamaka", "Deoraj", "Esperanza"],
    "last": ["Balgobin", "Charles-Mohan", "Dass", "Gopaul", "Hosein", "Jaggernauth", "Lalla", "Maharaj-Pierre",
             "Nanan", "Okafor", "Rampersad", "Sankar", "Thomas-Ali", "Vialva", "Waithe", "Ying"],
    "street": ["Pommerac Lane", "Silk Cotton Drive", "Old Mission Road", "Calabash Street", "Sapodilla Trace",
               "Mango Rose Avenue", "Lagoon View Road", "Hibiscus Close"],
    "town": ["Fictionville", "Mockton", "Sampleton", "Placeholder Bay", "Testbridge"],
    "domain": ["example.invalid", "example.org", "example.net"],
    "employer_family": ["Gopaul", "Hosein", "Lalla", "Sankar"],
}

JOBS = [
    ("Records Officer", "CivicDesk Central Registry", "indexed 9,500 files a year"),
    ("Lands Clerk", "CivicDesk Lands Office", "processed 40 survey requests a month"),
    ("ICT Support Officer", "CivicDesk Trade Unit", "closed 85% of tickets within two days"),
    ("Accounts Officer", "CivicDesk Finance Unit", "reconciled 600 supplier invoices a quarter"),
    ("Health Records Assistant", "CivicDesk District Clinic", "maintained registers for 3 clinics"),
    ("Data Entry Clerk", "CivicDesk Permits Office", "keyed 250 permit forms a week"),
]
QUALS = ["BSc Information Management, University of Fictionville", "Diploma in Records Management, Mockton Technical Institute",
         "ACCA Applied Knowledge", "Associate Degree in Office Administration, Sampleton College"]


def _phone(r: random.Random, style: int) -> str:
    b = r.randint(1000, 9999)
    return [f"868-555-{b}", f"(868) 555 {b}", f"+1 (868) 555-{b}", f"868 555 {b}"][style % 4]


def _person(r, used):
    while True:
        n = f"{r.choice(TEST_POOLS['first'])} {r.choice(TEST_POOLS['last'])}"
        if n not in used:
            used.add(n)
            return n


def _email(r, name, obfuscate=False):
    f, l = name.lower().split(" ", 1)
    local = f"{f}.{l.replace('-', '')[:6]}"
    dom = r.choice(TEST_POOLS["domain"])
    if obfuscate:
        return f"{local.replace('.', ' dot ')} at {dom.replace('.', ' dot ')}", f"{local}@{dom}"
    return f"{local}@{dom}", f"{local}@{dom}"


def _addr(r):
    return f"{r.randint(2, 98)} {r.choice(TEST_POOLS['street'])}, {r.choice(TEST_POOLS['town'])}"


def _job(r):
    t, org, duty = r.choice(JOBS)
    y = r.randint(2012, 2020)
    return t, org, duty, f"{y}-{y + r.randint(2, 5)}"


def layout(i: int, r: random.Random, used: set) -> dict:
    k = i % 7
    name = _person(r, used)
    first = name.split(" ")[0]
    t, org, duty, yrs = _job(r)
    q = r.choice(QUALS)
    qy = r.randint(2008, 2019)
    phone = _phone(r, i)
    em, form_em = _email(r, name, obfuscate=(k == 4))
    job_line = f"{t}, {org}, {yrs}"
    keep = [job_line, duty, f"{q}, {qy}"]
    pii = [["PERSON", name], ["PHONE", phone], ["EMAIL", em]]
    if k == 0:  # standard headed
        ad = _addr(r)
        text = f"# {name}\nEmail: {em} | Phone: {phone}\nAddress: {ad}\n\n## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        pii.append(["ADDRESS", ad]); cat = "standard"
    elif k == 1:  # DOB, ID, referee
        ref = _person(r, used)
        rph = _phone(r, i + 1)
        rem, _ = _email(r, ref)
        by = r.randint(1975, 2000)
        dob = f"{r.randint(1, 28):02d}/{r.randint(1, 12):02d}/{by}"
        nid = f"CD-ID-{by}-{r.randint(100, 999)}"
        text = (f"# Curriculum vitae: {name}\nDate of birth: {dob}\nNational ID: {nid}\nEmail: {em} | Phone: {phone}\n\n"
                f"## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n\n## Referees\n- {ref}, Former Supervisor, {org}, {rph}, {rem}\n")
        pii += [["DOB", dob], ["ID", nid], ["PERSON", ref], ["PHONE", rph], ["EMAIL", rem]]
        keep.append(f"Former Supervisor, {org}"); cat = "referee_dob_id"
    elif k == 2:  # first name alone in prose
        ad = _addr(r)
        text = (f"Name: {name}\nContact: {phone} / {em}\nAddress: {ad}\n\n## Profile\n{first} {duty} as {t} at {org}.\n\n"
                f"## Experience\n- {job_line}\n\n## Education\n- {q}, {qy}\n")
        pii += [["PERSON", first], ["ADDRESS", ad]]
        keep = [job_line, f"{duty} as {t} at {org}", f"{q}, {qy}"]; cat = "first_name_in_prose"
    elif k == 3:  # employer carries family name (kept by policy)
        fam = r.choice(TEST_POOLS["employer_family"])
        name = f"{first} {fam}"
        used.add(name)
        em, form_em = _email(r, name)
        pii = [["PERSON", name], ["PHONE", phone], ["EMAIL", em]]
        y0 = int(yrs[:4])
        emp = f"Accounts Clerk, {fam} & Sons Hardware Ltd, {y0 - 4}-{y0}"
        text = f"# {name}\nPhone: {phone} | Email: {em}\n\n## Experience\n- {emp}: reconciled supplier invoices.\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        keep = [emp, job_line, duty, f"{q}, {qy}"]; cat = "family_business_employer"
    elif k == 4:  # spelled-out email
        text = f"# {name}\nReach me: {em}, or {phone} (WhatsApp)\n\n## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        cat = "obfuscated_email"
    elif k == 5:  # cover-letter prose, third person
        ad = _addr(r)
        mentor = _person(r, used)
        text = (f"My name is {name} and I live at {ad}. You can reach me on {phone} or at {em}.\n\n"
                f"I have worked as {t} at {org} since {yrs[:4]}, where I {duty}.\n\nMy mentor, Dr. {mentor}, encouraged me to apply.\n\n"
                f"## Qualifications\n- {q}, {qy}\n")
        pii += [["ADDRESS", ad], ["PERSON", mentor]]
        keep = [f"{t} at {org} since {yrs[:4]}", duty, f"{q}, {qy}"]; cat = "inline_prose_third_party"
    else:  # repeated identifiers
        text = (f"# {name}\nEmail: {em}\nPhone: {phone}\n\n## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n\n"
                f"## Contact\nFor references, write to {em} or call {phone}.\n")
        cat = "repeated_identifiers"
    return {"category": cat, "text": text, "pii": pii, "keep": keep,
            "form": {"name": name, "email": form_em, "phone": phone}}


def no_pii(i: int, r: random.Random) -> dict:
    t, org, duty, _ = _job(r)
    ref = f"CD-{r.randint(2019, 2026)}-{r.randint(100, 999)}-{r.randint(1000, 9999)}"
    text = (f"# Vacancy notice extract\nVacancy ref: {ref}\nPosition: {t}, {org}\n"
            f"Duties: {duty}.\nRequirements: {r.choice(QUALS)} or equivalent; two years' experience.\n")
    return {"category": "no_pii", "text": text, "pii": [], "keep": [f"Vacancy ref: {ref}", f"{t}, {org}", duty], "form": None}


def build() -> dict:
    r = random.Random(SEED)
    used: set = set()
    raw = [layout(i, r, used) for i in range(N_PII_DOCS)] + [no_pii(i, r) for i in range(N_NO_PII_DOCS)]
    docs = []
    for n, d in enumerate(raw, 1):
        spans = find_spans(d["text"], d["pii"])
        expected = redact(d["text"], spans)
        for k in d["keep"]:
            if k not in d["text"] or k not in expected:
                raise ValueError(f"B{n:02d}: keep anchor lost by the answer key: {k!r}")
        docs.append({"id": f"B{n:02d}", "category": d["category"], "text": d["text"], "spans": spans,
                     "expected": expected, "keep": d["keep"], "form": d["form"]})
    body = {"policy": POLICY, "docs": docs}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"benchmark_version": BENCH_VERSION, "split": "test (held out: never train, tune prompts or pick examples on it)",
            "seed": SEED, "provenance": "Synthetic, rendered from fictional field values; labels derived from those values, not by a model.",
            "sha256": digest, **body}


if __name__ == "__main__":
    b = build()
    (Path(__file__).resolve().parent / "data" / "resume_redaction_test_v1.json").write_text(json.dumps(b, indent=2, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print(len(b["docs"]), "docs", Counter(d["category"] for d in b["docs"]))
    print("spans", sum(len(d["spans"]) for d in b["docs"]), Counter(s["type"] for d in b["docs"] for s in d["spans"]))
    print("sha256", b["sha256"])
