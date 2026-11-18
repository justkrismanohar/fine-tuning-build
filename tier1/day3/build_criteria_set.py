"""Synthetic résumé-criteria training rows. Different names, layouts and criterion types from the held-out set.

Fiction only. Labels come from the line we planted, never from a model.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from heldout.cases import MINUTES, RESUMES, TICKETS  # noqa: E402
from heldout.prompts import CRITERIA_SYSTEM_ONE  # noqa: E402

SEED = 20261117
OUT = HERE / "data" / "criteria"

FIRST = [
    "Nalini", "Orson", "Paulette", "Quincy", "Rehana", "Stefan", "Tessa", "Ulric",
    "Verna", "Winston", "Yasmin", "Andre", "Chantal", "Daryl", "Elena", "Fitzroy",
]
LAST = [
    "Seepersad-Moon", "Dolly-King", "Mahabir-Cross", "Nanton", "Ollivierre",
    "Parris-Chen", "Sampleton", "Telesford", "Unnamed-Rowe", "Villaroel",
]
STREET = ["Poui Ridge", "Coconut Walk", "Tannia Trace", "Cedar Grove", "Limekiln Hill"]
TOWN = ["Fableton", "Parable Heights", "Yarnborough", "Storybridge"]
EMPLOYER = [
    "CivicDesk Records Office", "Harbour CivicDesk Unit", "Fableton Borough Desk",
    "Yarnborough CivicDesk College", "Storybridge Council Secretariat",
]
QUAL_OK = [
    "Diploma in Public Administration, CivicDesk Evening College, 2019",
    "Bachelor of Social Work, 2018",
    "Certificate in First Aid, 2024",
    "PMP certification, 2022",
]
JOB = [
    "Cashier, Fableton Market Unit, 2014 to 2026 (12 years)",
    "Librarian, Yarnborough Public Library, 2015 to 2026",
    "Stores Clerk, Harbour CivicDesk Unit, 2012 to 2024",
    "Translator (Spanish), Storybridge Council Secretariat, 2018 to 2026",
]

# Held-out criterion types stay out of training.
TRAIN_CRITERIA = [
    {"id": "F1", "text": "Holds a valid forklift operator licence."},
    {"id": "F2", "text": "At least five years of cashier experience."},
    {"id": "F3", "text": "Holds a current first-aid certificate."},
    {"id": "F4", "text": "Degree in Public Administration or Social Work."},
    {"id": "F5", "text": "Certified translator (Spanish)."},
    {"id": "F6", "text": "At least four years as a librarian."},
    {"id": "F7", "text": "Holds a PMP certification."},
    {"id": "F8", "text": "At least six years as a stores clerk."},
]


def _needles() -> list[str]:
    out = []
    for res in RESUMES:
        out.append(res["text"])
        for p in res["pii"]:
            out.append(p["value"])
            out.extend(p.get("tells") or [])
        for c in res["criteria"]:
            out.append(c["text"])
        out.extend(res.get("keep") or [])
    for t in TICKETS:
        out.append(t["text"])
        out.append(t["id"])
    for m in MINUTES:
        out.append(m["text"])
        out.append(m["id"])
    skip = {"meets", "does_not_meet", "human_review", "present"}
    return [n for n in out if n and len(str(n).strip()) >= 5 and str(n).strip().lower() not in skip]


def _person(r: random.Random, used: set) -> str:
    while True:
        n = f"{r.choice(FIRST)} {r.choice(LAST)}"
        if n not in used:
            used.add(n)
            return n


def _layout(kind: int, name: str, extra_lines: list[str]) -> str:
    email = name.lower().replace(" ", ".") + "@mailbox.test"
    phone = "868-554-2%03d" % (hash(name) % 800)
    addr = f"{2 + (hash(name) % 90)} {STREET[hash(name) % len(STREET)]}, {TOWN[hash(name) % len(TOWN)]}"
    job = JOB[hash(name) % len(JOB)]
    qual = QUAL_OK[hash(name) % len(QUAL_OK)]
    body = "\n".join(extra_lines)
    if kind == 0:
        return f"Dear Sir/Madam,\nI am {name}.\n{qual}\n{job}\n{body}\nYours,\n{name}"
    if kind == 1:
        return f"SKILLS-FIRST CV\n{qual}\n{job}\n{body}\nSigned {name} | {phone}"
    if kind == 2:
        return f"{name}\n{addr}\nHours: shift 06:00-14:00\n{qual}\n{job}\n{body}"
    if kind == 3:
        return f"Cover note\nPlease find my CV.\n---\n{name} · {email}\n{qual}\n{job}\n{body}"
    if kind == 4:
        return f"{name}\t{phone}\n{qual}\n{job}\n{body}\n{addr}"
    return f"Application\n{name}\n{email}\n{qual}\n{job}\n{body}"


def _row(rid: str, resume: str, crit: dict, result: str, evidence: str, subtype: str | None) -> dict:
    if result == "does_not_meet" and not evidence:
        raise ValueError(f"{rid}: does_not_meet with empty evidence")
    if evidence and evidence not in resume:
        raise ValueError(f"{rid}: evidence is not a substring")
    user = f"Résumé:\n{resume}\n\nCriterion:\n{crit['id']}: {crit['text']}"
    target = {"id": crit["id"], "result": result, "evidence": evidence}
    return {
        "id": rid,
        "split": "train",
        "hr_subtype": subtype,
        "criterion_type": crit["id"],
        "layout": "synthetic",
        "messages": [
            {"role": "system", "content": CRITERIA_SYSTEM_ONE},
            {"role": "user", "content": user},
        ],
        "target": json.dumps(target, ensure_ascii=False),
        "target_obj": target,
    }


def overlap_hits(text: str, needles: list[str]) -> list[str]:
    low = text.lower()
    hits = []
    for n in needles:
        s = str(n).lower()
        if len(s) >= 5 and s in low:
            hits.append(n)
    return hits


def build() -> dict:
    r = random.Random(SEED)
    used: set[str] = set()
    rows: list[dict] = []
    n = 0

    def add(resume, crit, result, evidence, subtype=None):
        nonlocal n
        n += 1
        rows.append(_row(f"CR-T-{n:03d}", resume, crit, result, evidence, subtype))

    # Contrast: forklift licence silent / holds / does not hold
    for _ in range(6):
        name = _person(r, used)
        silent = _layout(r.randint(0, 5), name, [])
        hold_line = "I hold a valid forklift operator licence."
        no_line = "I do not hold a forklift operator licence."
        add(silent, TRAIN_CRITERIA[0], "human_review", "", "absent")
        add(_layout(r.randint(0, 5), name, [hold_line]), TRAIN_CRITERIA[0], "meets", hold_line)
        add(_layout(r.randint(0, 5), name, [no_line]), TRAIN_CRITERIA[0], "does_not_meet", no_line)

    # Contrast: first-aid current vs expired vs in progress vs absent
    for _ in range(4):
        name = _person(r, used)
        add(_layout(0, name, []), TRAIN_CRITERIA[2], "human_review", "", "absent")
        line = "First-aid certificate, 2024."
        add(_layout(1, name, [line]), TRAIN_CRITERIA[2], "meets", line)
        exp = "First-aid certificate (expired 2022)."
        add(_layout(2, name, [exp]), TRAIN_CRITERIA[2], "does_not_meet", exp)
        prog = "First-aid certificate (in progress, due 2028)."
        add(_layout(3, name, [prog]), TRAIN_CRITERIA[2], "human_review", prog, "in-progress")

    # Degree in Public Admin / Social Work: held, in progress, different qualification, silent
    for _ in range(4):
        name = _person(r, used)
        add(_layout(4, name, []), TRAIN_CRITERIA[3], "human_review", "", "absent")
        held = "Bachelor of Social Work, 2018"
        add(_layout(0, name, [held]), TRAIN_CRITERIA[3], "meets", held)
        prog = "Diploma in Public Administration (in progress, due 2028)"
        add(_layout(1, name, [prog]), TRAIN_CRITERIA[3], "human_review", prog, "in-progress")
        other = "BA Literature, 2015"
        add(_layout(2, name, [other]), TRAIN_CRITERIA[3], "human_review", other, "different-qualification")

    # Years: cashier clearly meets / clearly fails / overlapping roles = human_review
    for _ in range(4):
        name = _person(r, used)
        meet = "Cashier, Fableton Market Unit, 2014 to 2026 (12 years)"
        add(_layout(3, name, [meet]), TRAIN_CRITERIA[1], "meets", meet)
        fail = "I have two years of cashier experience."
        add(_layout(4, name, [fail]), TRAIN_CRITERIA[1], "does_not_meet", fail)
        amb = "Cashier, Fableton Market Unit, April 2021 to 2026\nClerk, Fableton Market Unit, 2019 to 2021"
        add(_layout(5, name, [amb.split("\n")[0], amb.split("\n")[1]]), TRAIN_CRITERIA[1], "human_review", "Cashier, Fableton Market Unit, April 2021 to 2026", "partial")

    # Librarian years, translator, PMP, stores clerk — mix
    for _ in range(3):
        name = _person(r, used)
        lib = "Librarian, Yarnborough Public Library, 2015 to 2026"
        add(_layout(0, name, [lib]), TRAIN_CRITERIA[5], "meets", lib)
        add(_layout(1, name, []), TRAIN_CRITERIA[5], "human_review", "", "absent")
        trans = "Certified translator (Spanish), 2020"
        add(_layout(2, name, [trans]), TRAIN_CRITERIA[4], "meets", trans)
        no_t = "I do not hold a translator stamp."
        add(_layout(3, name, [no_t]), TRAIN_CRITERIA[4], "does_not_meet", no_t)
        pmp = "PMP certification, 2022"
        add(_layout(4, name, [pmp]), TRAIN_CRITERIA[6], "meets", pmp)
        pmp_exp = "PMP certification (expired 2022)."
        add(_layout(5, name, [pmp_exp]), TRAIN_CRITERIA[6], "does_not_meet", pmp_exp)
        stores = "Stores Clerk, Harbour CivicDesk Unit, 2012 to 2024"
        add(_layout(0, name, [stores]), TRAIN_CRITERIA[7], "meets", stores)
        stores_fail = "I have one year as a stores clerk."
        add(_layout(1, name, [stores_fail]), TRAIN_CRITERIA[7], "does_not_meet", stores_fail)
        part = "Stores Clerk, Harbour CivicDesk Unit, June 2022 to 2026"
        add(
            _layout(2, name, [part, "Messenger, Harbour CivicDesk Unit, 2018 to 2022"]),
            TRAIN_CRITERIA[7],
            "human_review",
            part,
            "partial",
        )
        other = "Certificate in Warehouse Safety, 2020"
        add(_layout(3, name, [other]), TRAIN_CRITERIA[7], "human_review", other, "different-qualification")
        prog = "Stores-clerk certificate (in progress, due 2028)"
        add(_layout(4, name, [prog]), TRAIN_CRITERIA[7], "human_review", prog, "in-progress")

    # Validation: disjoint people, same criterion types
    val: list[dict] = []
    for i in range(12):
        name = _person(r, used)
        kind = i % 4
        if kind == 0:
            resume = _layout(0, name, [])
            crit, result, evidence, sub = TRAIN_CRITERIA[0], "human_review", "", "absent"
        elif kind == 1:
            line = "I hold a valid forklift operator licence."
            resume = _layout(1, name, [line])
            crit, result, evidence, sub = TRAIN_CRITERIA[0], "meets", line, None
        elif kind == 2:
            line = "I have two years of cashier experience."
            resume = _layout(2, name, [line])
            crit, result, evidence, sub = TRAIN_CRITERIA[1], "does_not_meet", line, None
        else:
            line = "Diploma in Public Administration (in progress, due 2028)"
            resume = _layout(3, name, [line])
            crit, result, evidence, sub = TRAIN_CRITERIA[3], "human_review", line, "in-progress"
        row = _row(f"CR-V-{i+1:03d}", resume, crit, result, evidence, sub)
        row["split"] = "val"
        val.append(row)

    needles = _needles()
    blob_train = json.dumps(rows, ensure_ascii=False)
    blob_val = json.dumps(val, ensure_ascii=False)
    hits_train = overlap_hits(blob_train, needles)
    hits_val = overlap_hits(blob_val, needles)
    if hits_train or hits_val:
        raise SystemExit(f"overlap with held-out: train={hits_train[:8]} val={hits_val[:8]}")

    def pack(split_rows, name):
        raw = json.dumps({"rows": split_rows}, ensure_ascii=False, indent=2)
        sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        labels = {}
        hr = {}
        for row in split_rows:
            lab = row["target_obj"]["result"]
            labels[lab] = labels.get(lab, 0) + 1
            if lab == "human_review":
                hr[row.get("hr_subtype") or "other"] = hr.get(row.get("hr_subtype") or "other", 0) + 1
        if labels.get("human_review", 0) / len(split_rows) < 1 / 3 - 1e-9 and name == "train":
            raise SystemExit(f"human_review below one third: {labels}")
        return {
            "name": name,
            "n": len(split_rows),
            "sha256": sha,
            "labels": labels,
            "hr_subtypes": hr,
            "seed": SEED,
            "prompt": "criteria-one-v1",
            "rows": split_rows,
        }

    train_pack = pack(rows, "train")
    val_pack = pack(val, "val")
    return {"train": train_pack, "val": val_pack, "overlap_train": hits_train, "overlap_val": hits_val}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    built = build()
    for key in ("train", "val"):
        path = OUT / f"{key}_v1.json"
        blob = dict(built[key])
        raw = json.dumps(blob, ensure_ascii=False, indent=2)
        blob["sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        path.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")
        print(key, "n", blob["n"], "labels", blob["labels"], "sha256", blob["sha256"])
    print("overlap train", built["overlap_train"] or "none")
    print("overlap val", built["overlap_val"] or "none")


if __name__ == "__main__":
    main()
