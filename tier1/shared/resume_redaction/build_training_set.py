"""Day 3 training / inspect sets. Different pools and seed from the frozen test split.

Fiction only. Labels come from the field values used to render each row, never from a model.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_benchmark import JOBS, QUALS  # noqa: E402
from build_teaching_set import POLICY, find_spans, redact  # noqa: E402
from redaction_eval import SYSTEM_PROMPT  # noqa: E402

SEED = 20261116
BENCH_PATH = HERE / "data" / "resume_redaction_test_v1.json"
OUT = HERE / "data"

# Must not overlap TEST_POOLS in build_benchmark.py.
TRAIN_POOLS = {
    "first": [
        "Bibi", "Clem", "Farah", "Gita", "Hakeem", "Ines", "Josiah", "Keisha",
        "Leroy", "Mala", "Omar", "Priya", "Ravi", "Sade", "Theo", "Uma", "Vernon", "Zara",
    ],
    "last": [
        "Ali-Khan", "Baptiste-Rose", "Chadee", "Dindial", "Etienne", "Fermin", "Gobin",
        "Harricharan", "Isaac", "Jagroo", "Khan-Lee", "Lopez", "Mohammed-Gray",
        "Persad", "Quesnel", "Roopnarine",
    ],
    "street": [
        "Coral Bean Trace", "Rain Tree Walk", "Coppercut Road", "Breadfruit Lane", "Seagrape Crescent",
        "Nutmeg Close", "Allamanda Drive",
    ],
    "town": ["Fableton", "Yarnborough", "Parable Heights", "Storybridge"],
    "domain": ["civicdesk.test", "mailbox.test"],
    "employer_family": ["Chadee", "Gobin", "Persad"],
}


def _phone(r: random.Random, style: int) -> str:
    b = r.randint(1000, 9999)
    return [f"868-554-{b}", f"(868) 554 {b}", f"+1 (868) 554-{b}", f"868 554 {b}"][style % 4]


def _person(r, used):
    while True:
        n = f"{r.choice(TRAIN_POOLS['first'])} {r.choice(TRAIN_POOLS['last'])}"
        if n not in used:
            used.add(n)
            return n


def _email(r, name, obfuscate=False):
    f, l = name.lower().split(" ", 1)
    local = f"{f}.{l.replace('-', '')[:6]}"
    dom = r.choice(TRAIN_POOLS["domain"])
    if obfuscate:
        return f"{local.replace('.', ' dot ')} at {dom.replace('.', ' dot ')}", f"{local}@{dom}"
    return f"{local}@{dom}", f"{local}@{dom}"


def _addr(r):
    return f"{r.randint(2, 98)} {r.choice(TRAIN_POOLS['street'])}, {r.choice(TRAIN_POOLS['town'])}"


def _job(r):
    t, org, duty = r.choice(JOBS)
    y = r.randint(2011, 2020)
    yrs = f"{y}-{y + r.randint(2, 5)}"
    return t, org, duty, yrs


def make_layout(i: int, r: random.Random, used: set) -> dict:
    """Same seven layouts as the test split, different people and streets."""
    k = i % 7
    name = _person(r, used)
    first = name.split(" ")[0]
    t, org, duty, yrs = _job(r)
    q = r.choice(QUALS)
    qy = r.randint(2007, 2018)
    phone = _phone(r, i)
    em, form_em = _email(r, name, obfuscate=(k == 4))
    job_line = f"{t}, {org}, {yrs}"
    keep = [job_line, duty, f"{q}, {qy}"]
    pii = [["PERSON", name], ["PHONE", phone], ["EMAIL", em]]
    if k == 0:
        ad = _addr(r)
        text = (
            f"# {name}\nEmail: {em} | Phone: {phone}\nAddress: {ad}\n\n"
            f"## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        )
        pii.append(["ADDRESS", ad])
        cat = "standard"
    elif k == 1:
        ref = _person(r, used)
        rph = _phone(r, i + 1)
        rem, _ = _email(r, ref)
        by = r.randint(1974, 1999)
        dob = f"{r.randint(1, 28):02d}/{r.randint(1, 12):02d}/{by}"
        nid = f"TR-ID-{by}-{r.randint(100, 999)}"
        text = (
            f"# Curriculum vitae: {name}\nDate of birth: {dob}\nNational ID: {nid}\n"
            f"Email: {em} | Phone: {phone}\n\n"
            f"## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n\n"
            f"## Referees\n- {ref}, Former Supervisor, {org}, {rph}, {rem}\n"
        )
        pii += [["DOB", dob], ["ID", nid], ["PERSON", ref], ["PHONE", rph], ["EMAIL", rem]]
        keep.append(f"Former Supervisor, {org}")
        cat = "referee_dob_id"
    elif k == 2:
        ad = _addr(r)
        text = (
            f"Name: {name}\nContact: {phone} / {em}\nAddress: {ad}\n\n"
            f"## Profile\n{first} {duty} as {t} at {org}.\n\n"
            f"## Experience\n- {job_line}\n\n## Education\n- {q}, {qy}\n"
        )
        pii += [["PERSON", first], ["ADDRESS", ad]]
        keep = [job_line, f"{duty} as {t} at {org}", f"{q}, {qy}"]
        cat = "first_name_in_prose"
    elif k == 3:
        fam = r.choice(TRAIN_POOLS["employer_family"])
        name = f"{first} {fam}"
        used.add(name)
        em, form_em = _email(r, name)
        pii = [["PERSON", name], ["PHONE", phone], ["EMAIL", em]]
        y0 = int(yrs[:4])
        emp = f"Accounts Clerk, {fam} & Sons Hardware Ltd, {y0 - 4}-{y0}"
        text = (
            f"# {name}\nPhone: {phone} | Email: {em}\n\n"
            f"## Experience\n- {emp}: reconciled supplier invoices.\n- {job_line}: {duty}.\n\n"
            f"## Education\n- {q}, {qy}\n"
        )
        keep = [emp, job_line, duty, f"{q}, {qy}"]
        cat = "family_business_employer"
    elif k == 4:
        text = (
            f"# {name}\nReach me: {em}, or {phone} (WhatsApp)\n\n"
            f"## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        )
        cat = "obfuscated_email"
    elif k == 5:
        ad = _addr(r)
        mentor = _person(r, used)
        text = (
            f"My name is {name} and I live at {ad}. You can reach me on {phone} or at {em}.\n\n"
            f"I have worked as {t} at {org} since {yrs[:4]}, where I {duty}.\n\n"
            f"My mentor, Dr. {mentor}, encouraged me to apply.\n\n"
            f"## Qualifications\n- {q}, {qy}\n"
        )
        pii += [["ADDRESS", ad], ["PERSON", mentor]]
        keep = [f"{t} at {org} since {yrs[:4]}", duty, f"{q}, {qy}"]
        cat = "inline_prose_third_party"
    else:
        text = (
            f"# {name}\nEmail: {em}\nPhone: {phone}\n\n"
            f"## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n\n"
            f"## Contact\nFor references, write to {em} or call {phone}.\n"
        )
        cat = "repeated_identifiers"
    return {
        "category": cat,
        "text": text,
        "pii": pii,
        "keep": keep,
        "form": {"name": name, "email": form_em, "phone": phone},
    }


def no_pii(i: int, r: random.Random) -> dict:
    t, org, duty, _ = _job(r)
    ref = f"CD-TR-{r.randint(2019, 2026)}-{r.randint(100, 999)}-{r.randint(1000, 9999)}"
    text = (
        f"# Vacancy notice extract\nVacancy ref: {ref}\nPosition: {t}, {org}\n"
        f"Duties: {duty}.\nRequirements: {r.choice(QUALS)} or equivalent; two years' experience.\n"
    )
    return {
        "category": "no_pii",
        "text": text,
        "pii": [],
        "keep": [f"Vacancy ref: {ref}", f"{t}, {org}", duty],
        "form": None,
    }


def as_row(rid: str, raw: dict, *, problem: str | None = None, target: str | None = None) -> dict:
    spans = find_spans(raw["text"], raw["pii"])
    expected = redact(raw["text"], spans) if target is None else target
    for k in raw["keep"]:
        if k not in raw["text"]:
            raise ValueError(f"{rid}: keep anchor missing from text: {k!r}")
        if problem not in {"rewrite", "inconsistent"} and k not in expected:
            raise ValueError(f"{rid}: keep anchor lost by the answer key: {k!r}")
    return {
        "id": rid,
        "layout": raw["category"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw["text"]},
        ],
        "target": expected,
        "spans": spans,
        "keep": raw["keep"],
        "form": raw["form"],
        "problem": problem,
    }


def pii_strings(docs: list[dict]) -> set[str]:
    out: set[str] = set()
    for d in docs:
        form = d.get("form") or {}
        for v in form.values():
            if v:
                out.add(str(v).lower())
        for sp in d.get("spans") or []:
            out.add(sp["text"].lower())
        text = d.get("messages", [{}, {}])[1].get("content", "") if d.get("messages") else d.get("text", "")
        # also collect explicit pii list if present
        for item in d.get("pii") or []:
            out.add(item[1].lower())
        if text:
            pass
    return {s for s in out if s}


def test_pii_values(bench: dict) -> set[str]:
    vals: set[str] = set()
    for d in bench["docs"]:
        for s in d["spans"]:
            vals.add(s["text"].lower())
        form = d.get("form") or {}
        for v in form.values():
            if v:
                vals.add(str(v).lower())
    return vals


def overlap(train_vals: set[str], test_vals: set[str]) -> set[str]:
    return {v for v in train_vals if v in test_vals and len(v) >= 4}


def write(path: Path, obj: dict) -> str:
    body = json.dumps(obj, indent=2, ensure_ascii=False)
    path.write_text(body, encoding="utf-8")
    digest = hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return digest


def build() -> dict:
    bench = json.loads(BENCH_PATH.read_text(encoding="utf-8"))
    r = random.Random(SEED)
    used: set = set()

    good = [make_layout(i, r, used) for i in range(26)]
    inspect_rows = [as_row(f"TR-{i:02d}", raw) for i, raw in enumerate(good, 1)]

    # P1 leak: near-copy of a test résumé (layout + wording, one name changed).
    test_doc = next(d for d in bench["docs"] if d["id"] == "B01")
    leak_name = "Priya Quesnel"
    leaked_text = test_doc["text"].replace(test_doc["form"]["name"], leak_name)
    # keep other test PII so the overlap check would catch this row
    leak_raw = {
        "category": test_doc["category"],
        "text": leaked_text,
        "pii": [["PERSON", leak_name]] + [[s["type"], s["text"]] for s in test_doc["spans"] if s["type"] != "PERSON"],
        "keep": list(test_doc["keep"]),
        "form": {**test_doc["form"], "name": leak_name},
    }
    p1 = as_row("TR-TMP-LEAK", leak_raw, problem="leak")

    # P2 inconsistent label: same employer redacted in one row, kept in another.
    fam = "Gobin"
    keep_emp = f"Accounts Clerk, {fam} & Sons Hardware Ltd, 2014-2018"
    name_a = _person(r, used)
    phone_a = _phone(r, 40)
    em_a, form_a = _email(r, name_a)
    text_a = (
        f"# {name_a}\nPhone: {phone_a} | Email: {em_a}\n\n"
        f"## Experience\n- {keep_emp}: reconciled supplier invoices.\n\n"
        f"## Education\n- Diploma in Records Management, Mockton Technical Institute, 2012\n"
    )
    raw_ok = {
        "category": "family_business_employer",
        "text": text_a,
        "pii": [["PERSON", name_a], ["PHONE", phone_a], ["EMAIL", em_a]],
        "keep": [keep_emp, "Diploma in Records Management, Mockton Technical Institute, 2012"],
        "form": {"name": name_a, "email": form_a, "phone": phone_a},
    }
    name_b = _person(r, used)
    phone_b = _phone(r, 41)
    em_b, form_b = _email(r, name_b)
    text_b = (
        f"# {name_b}\nPhone: {phone_b} | Email: {em_b}\n\n"
        f"## Experience\n- {keep_emp}: reconciled supplier invoices.\n\n"
        f"## Education\n- Diploma in Records Management, Mockton Technical Institute, 2012\n"
    )
    raw_bad = {
        "category": "family_business_employer",
        "text": text_b,
        "pii": [["PERSON", name_b], ["PHONE", phone_b], ["EMAIL", em_b]],
        "keep": [keep_emp, "Diploma in Records Management, Mockton Technical Institute, 2012"],
        "form": {"name": name_b, "email": form_b, "phone": phone_b},
    }
    p2_ok = as_row("TR-TMP-P2OK", raw_ok)
    bad_target = redact(text_b, find_spans(text_b, raw_bad["pii"])).replace(fam + " & Sons Hardware Ltd", "[PERSON]")
    p2_bad = as_row("TR-TMP-INCON", raw_bad, problem="inconsistent", target=bad_target)

    # P3 canary: a real-looking national ID that must never be trained on.
    canary_id = "196-88-44219"
    cname = _person(r, used)
    cphone = _phone(r, 42)
    cem, cform = _email(r, cname)
    ctext = (
        f"# {cname}\nNational ID: {canary_id}\nEmail: {cem} | Phone: {cphone}\n\n"
        f"## Experience\n- Records Officer, CivicDesk Central Registry, 2018-2024: indexed 9,500 files a year.\n"
    )
    craw = {
        "category": "referee_dob_id",
        "text": ctext,
        "pii": [["PERSON", cname], ["ID", canary_id], ["EMAIL", cem], ["PHONE", cphone]],
        "keep": ["Records Officer, CivicDesk Central Registry, 2018-2024", "indexed 9,500 files a year"],
        "form": {"name": cname, "email": cform, "phone": cphone},
    }
    p3 = as_row("TR-TMP-CANARY", craw, problem="canary")

    # P4 rewrite: target rewords non-personal text.
    rname = _person(r, used)
    rphone = _phone(r, 43)
    rem, rform = _email(r, rname)
    duty = "indexed 9,500 files a year"
    rewritten = "filed thousands of records each year"
    rtext = (
        f"# {rname}\nEmail: {rem} | Phone: {rphone}\n\n"
        f"## Experience\n- Records Officer, CivicDesk Central Registry, 2018-2024: {duty}.\n"
    )
    rraw = {
        "category": "standard",
        "text": rtext,
        "pii": [["PERSON", rname], ["EMAIL", rem], ["PHONE", rphone]],
        "keep": ["Records Officer, CivicDesk Central Registry, 2018-2024", duty],
        "form": {"name": rname, "email": rform, "phone": rphone},
    }
    gold = redact(rtext, find_spans(rtext, rraw["pii"]))
    p4 = as_row("TR-TMP-REWRITE", rraw, problem="rewrite", target=gold.replace(duty, rewritten))

    # 26 good + 4 planted = 30. Neutral IDs TR-01..TR-30 in shuffled order so
    # the planted rows are not obvious from TR-P* names. Answers live only in the key.
    planted = [p1, p2_bad, p3, p4]
    pool = inspect_rows[:26] + planted
    order = list(range(len(pool)))
    r.shuffle(order)
    inspect_rows = []
    id_by_tmp = {}
    for new_i, old_i in enumerate(order, 1):
        row = dict(pool[old_i])
        new_id = f"TR-{new_i:02d}"
        id_by_tmp[row["id"]] = new_id
        row["id"] = new_id
        row.pop("problem", None)  # never expose the answer in the inspect file
        inspect_rows.append(row)

    inspect = {
        "version": "train-inspect-v1",
        "seed": SEED,
        "n_rows": len(inspect_rows),
        "policy": POLICY,
        "rows": inspect_rows,
        "preview_note": "Open this file for the full 30 rows. The hunt answers are not in this file.",
    }

    key = {
        "version": "train-issues-key-v1",
        "problems": [
            {
                "id": "leak",
                "row_id": id_by_tmp["TR-TMP-LEAK"],
                "reason": "Near-copy of test document B01; one name changed.",
            },
            {
                "id": "inconsistent",
                "row_id": id_by_tmp["TR-TMP-INCON"],
                "reason": "Employer Gobin & Sons redacted here but kept in the matching clean row.",
            },
            {
                "id": "canary",
                "row_id": id_by_tmp["TR-TMP-CANARY"],
                "reason": f"Planted national ID {canary_id} must never be trained on.",
            },
            {
                "id": "rewrite",
                "row_id": id_by_tmp["TR-TMP-REWRITE"],
                "reason": "Target rewords non-personal duty text, teaching rewrite not redaction.",
            },
            {
                "id": "imbalance",
                "row_id": None,
                "reason": "File-level: these 30 rows contain no examples with no personal data. No single row shows it.",
            },
        ],
    }

    clean_goods = [as_row(f"TR-{i:02d}", raw) for i, raw in enumerate(good, 1)][:26]
    p2_fixed = as_row("TR-FIX-INCON", raw_bad)  # employer kept
    p4_fixed = as_row("TR-FIX-REWRITE", rraw)  # duty kept
    no_pii_rows = [as_row(f"TR-NP-{i:02d}", no_pii(i, r)) for i in range(1, 6)]
    clean_rows = clean_goods + [p2_ok, p2_fixed, p4_fixed] + no_pii_rows
    for row in clean_rows:
        row["problem"] = None

    clean = {
        "version": "train-clean-v1",
        "seed": SEED,
        "n_rows": len(clean_rows),
        "note": "P1 and P3 removed. P2 and P4 fixed. No-PII rows added.",
        "policy": POLICY,
        "rows": clean_rows,
    }
    clean_sha = hashlib.sha256(json.dumps(clean, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    clean["sha256"] = clean_sha

    val_raw = [make_layout(100 + i, r, used) for i in range(8)] + [no_pii(20 + i, r) for i in range(2)]
    val_rows = [as_row(f"VA-{i:02d}", raw) for i, raw in enumerate(val_raw, 1)]
    val = {
        "version": "val-v1",
        "seed": SEED,
        "n_rows": len(val_rows),
        "note": "From the training pools. Settings and early stopping only. Not the test split.",
        "policy": POLICY,
        "rows": val_rows,
    }
    val_sha = hashlib.sha256(json.dumps({k: v for k, v in val.items() if k != "sha256"}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    val["sha256"] = val_sha

    def row_vals(rows: list[dict]) -> set[str]:
        vals: set[str] = set()
        for row in rows:
            form = row.get("form") or {}
            for v in form.values():
                if v:
                    vals.add(str(v).lower())
            for sp in row.get("spans") or []:
                vals.add(sp["text"].lower())
            user = row["messages"][1]["content"]
            # IDs and phones in text
            if "national id:" in user.lower():
                pass
        return {v for v in vals if len(v) >= 4}

    test_vals = test_pii_values(bench)
    clean_overlap = overlap(row_vals(clean_rows), test_vals)
    val_overlap = overlap(row_vals(val_rows), test_vals)
    p1_overlap = overlap(row_vals([p1]), test_vals)

    if clean_overlap:
        raise AssertionError(f"train_clean overlaps test PII: {sorted(clean_overlap)[:8]}")
    if val_overlap:
        raise AssertionError(f"val overlaps test PII: {sorted(val_overlap)[:8]}")
    if not p1_overlap:
        raise AssertionError("P1 should have been caught as a test-set near-copy; overlap was empty.")

    return {
        "inspect": inspect,
        "key": key,
        "clean": clean,
        "val": val,
        "overlap": {
            "clean": sorted(clean_overlap),
            "val": sorted(val_overlap),
            "p1_would_be_caught": sorted(p1_overlap)[:12],
            "p1_n": len(p1_overlap),
        },
        "counts": {"inspect": len(inspect_rows), "clean": len(clean_rows), "val": len(val_rows)},
        "sha256": {"clean": clean_sha, "val": val_sha},
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pack = build()
    write(OUT / "train_inspect_v1.json", pack["inspect"])
    write(OUT / "train_issues_key_v1.json", pack["key"])
    write(OUT / "train_clean_v1.json", pack["clean"])
    write(OUT / "val_v1.json", pack["val"])
    print("inspect", pack["counts"]["inspect"])
    print("clean", pack["counts"]["clean"], "sha256", pack["sha256"]["clean"])
    print("val", pack["counts"]["val"], "sha256", pack["sha256"]["val"])
    print("overlap clean", pack["overlap"]["clean"] or "(none)")
    print("overlap val", pack["overlap"]["val"] or "(none)")
    print("P1 would be caught n=", pack["overlap"]["p1_n"], pack["overlap"]["p1_would_be_caught"][:6])


if __name__ == "__main__":
    main()
