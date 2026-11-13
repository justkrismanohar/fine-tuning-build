"""T1-05 canvas + résumé-redaction lab. No GPU required."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

DAY1 = Path(__file__).resolve().parents[1]
SHARED = DAY1.parent / "shared" / "resume_redaction"
sys.path.insert(0, str(DAY1))
sys.path.insert(0, str(SHARED))

import redaction_eval as R  # noqa: E402

NB = json.loads((DAY1 / "T1-05_usecase_canvas.ipynb").read_text(encoding="utf-8"))
TEACH_SHA = "39c0e0ea82d2ef8783bc9ffa4e145c0803a7d5b394c2af57adad65bef059e7f2"
BENCH_SHA = "c299eb39a169f639fd72b48963fe1154d7c9b4a0786eb4a87354dcd3ccbdd370"


def test_builders_and_hashes():
    teach = R.load_fixture()
    bench = R.load_benchmark()
    replay = R.load_replay()
    assert teach["sha256"] == TEACH_SHA
    assert bench["sha256"] == BENCH_SHA
    assert replay["fixture_sha256"] == TEACH_SHA
    assert len(teach["docs"]) == 7
    assert sum(len(d["spans"]) for d in teach["docs"]) == 26
    assert len(bench["docs"]) == 40
    assert Counter(d["category"] for d in bench["docs"]) == Counter(
        {
            "standard": 5,
            "referee_dob_id": 5,
            "first_name_in_prose": 5,
            "family_business_employer": 5,
            "obfuscated_email": 5,
            "inline_prose_third_party": 5,
            "repeated_identifiers": 5,
            "no_pii": 5,
        }
    )
    assert sum(len(d["spans"]) for d in bench["docs"]) == 165
    assert Counter(s["type"] for d in bench["docs"] for s in d["spans"]) == Counter(
        {"PERSON": 50, "EMAIL": 45, "PHONE": 45, "ADDRESS": 15, "DOB": 5, "ID": 5}
    )


def test_cell6_decisions():
    teach = R.load_fixture()
    replay = R.load_replay()
    rows = R.evaluate(teach, replay["outputs"])
    got = [(r["id"], r["decision"].startswith("HOLD"), r["acceptable"], r["leaked"]) for r in rows]
    assert got[0] == ("R01", False, True, False)
    assert got[1][0] == "R02" and got[1][1] is True
    assert got[2][0] == "R03" and got[2][1] is True
    assert got[3] == ("R04", False, False, False)
    assert got[4] == ("R05", False, False, True)
    assert got[5][0] == "R06" and got[5][1] is True
    assert got[6] == ("R07", True, True, False)


def test_scorer_on_expected_and_raw():
    bench = R.load_benchmark()
    lat = {d["id"]: 0.2 for d in bench["docs"]}
    rows = R.evaluate(bench, {d["id"]: d["expected"] for d in bench["docs"]}, lat)
    summary = R.summary_table(bench, rows)
    assert summary["spans_missed"] == 0
    assert summary["docs_over_redacted"] == []
    assert len(summary["acceptable_as_is"]) == 40
    assert R.check_rule(rows, lat)["meets_rule"] is True
    assert len(summary["held"]) == 10
    raw = R.evaluate(bench, {d["id"]: d["text"] for d in bench["docs"]})
    s2 = R.summary_table(bench, raw)
    assert s2["docs_leaked"] == 35
    assert s2["docs_with_pii"] == 35
    assert s2["span_recall"] == 0.0


def test_demo_run_live_not_measured():
    bench = R.load_benchmark()
    run = R.run_live(bench, "olmo")
    assert run["measured"] is False
    assert all(v.startswith("not measured") for v in run["notes"].values())
    assert all(v == "" for v in run["outputs"].values())


def test_dead_endpoint_is_fallback_not_outputs(monkeypatch):
    import civicdesk_lab as lab

    ep = lab.ENDPOINT_FILE
    backup = ep.read_bytes() if ep.is_file() else None
    try:
        lab.use_backend("custom", olmo_url="http://127.0.0.1:1/v1", fallback_to_demo=True)
        run = R.run_live(R.load_fixture(), "olmo", timeout_s=2)
        assert run["measured"] is False
        assert all("demo-fallback" in v for v in run["notes"].values())
        assert all(v == "" for v in run["outputs"].values())
    finally:
        lab._settings["mode"] = "demo"
        lab._settings["backend"] = "demo"
        lab._settings["fallback_to_demo"] = True
        if backup is None:
            if ep.is_file():
                ep.unlink()
        else:
            ep.write_bytes(backup)


def test_notebook_shape_and_go_block():
    assert len(NB["cells"]) == 18
    blob_all = []
    for i, c in enumerate(NB["cells"]):
        src = "".join(c.get("source") or [])
        blob_all.append(src)
        if c["cell_type"] == "code":
            first = src.lstrip().splitlines()[0]
            assert first.startswith(("# [RUN]", "# [CHANGE]", "# [OPTIONAL]"))
    text = "\n".join(blob_all)
    cell3 = blob_all[3]
    assert "GO/BLOCK" in cell3
    rest = text.replace(cell3, "")
    assert re.search(r"\bGO\b", rest) is None
    assert re.search(r"\bBLOCK\b", rest) is None
    extras = []
    for folder in (DAY1 / "cards", SHARED):
        for path in folder.rglob("*"):
            if path.suffix.lower() in {".md", ".py", ".json"}:
                blob = path.read_text(encoding="utf-8")
                if re.search(r"\bGO\b", blob) or re.search(r"\bBLOCK\b", blob):
                    extras.append(str(path))
    assert extras == []
    assert "lab.chat" not in "".join(blob_all[k] for k, c in enumerate(NB["cells"]) if c["cell_type"] == "code" and k != 8)
    gpu = blob_all[8]
    assert 'MODE = "replay"' in gpu


def test_synthetic_domains_and_555_phones():
    email_re = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)")
    allowed = {"example.invalid", "example.org", "example.net"}
    for path in SHARED.rglob("*.json"):
        raw = path.read_text(encoding="utf-8")
        for m in email_re.finditer(raw):
            domain = m.group(1).rstrip(".")
            assert domain in allowed, (path, m.group(0))
    phones = []
    for fx in (R.load_fixture(), R.load_benchmark()):
        for doc in fx["docs"]:
            phones.extend(s["text"] for s in doc["spans"] if s["type"] == "PHONE")
            form = doc.get("form") or {}
            if form.get("phone"):
                phones.append(form["phone"])
    assert phones
    for p in phones:
        digits = re.sub(r"\D", "", p)
        if digits.startswith("1") and len(digits) == 11:
            digits = digits[1:]
        assert "555" in digits, p


def test_notebook_code_cells_except_live_baseline():
    """Replay baseline is produced in the course container; skip cell 8 and 17 here."""
    g: dict = {"__name__": "__main__"}
    skip = {8, 17}
    for i, cell in enumerate(NB["cells"]):
        if cell["cell_type"] != "code" or i in skip:
            continue
        src = "".join(cell.get("source") or [])
        exec(compile(src, f"T1-05:cell{i}", "exec"), g)
    assert "R01" in "".join(g["teach"]["docs"][0]["id"])
    assert g["gold_pairs"]
