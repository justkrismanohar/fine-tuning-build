"""T1-03 scoring, freeze checks, cost, and key redaction. No GPU."""
from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

DAY1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DAY1))

import civicdesk_eval as ev  # noqa: E402
import civicdesk_lab as lab  # noqa: E402
import civicdesk_remote as remote  # noqa: E402

COURSE = DAY1 / "data" / "t103_release_cases_v1.json"


@pytest.fixture(autouse=True)
def _isolate_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "ENDPOINT_FILE", tmp_path / "endpoint.json")
    original = dict(lab._settings)
    lab.use_backend("demo")
    yield
    lab._settings.clear()
    lab._settings.update(original)


def test_course_set_passes_derive_label_and_coverage():
    rec = ev.load_frozen(COURSE)
    assert rec["n_cases"] >= 24
    blocks = {r: 0 for r in ev.RULE_TEXT}
    decoys = {r: 0 for r in ev.RULE_TEXT}
    for c in rec["cases"]:
        key = ev.derive_label(c["draft_reply"])
        assert key["label"] == c["label"]
        if c["kind"] == "trigger":
            blocks[c["planned_rule"]] += 1
        if c["kind"] == "decoy":
            decoys[c["planned_rule"]] += 1
        blob = (c["draft_reply"] + " " + ev.SCREEN_SYSTEM).lower()
        assert "cabinet" not in blob
        assert "nid-" not in blob
    assert all(n >= 3 for n in blocks.values())
    assert all(n >= 1 for n in decoys.values())


def test_load_frozen_refuses_tamper(tmp_path):
    rec = json.loads(COURSE.read_text(encoding="utf-8"))
    flipped = json.loads(json.dumps(rec))
    flipped["cases"][0]["label"] = "GO" if flipped["cases"][0]["label"] == "BLOCK" else "BLOCK"
    flipped["sha256"] = ev.case_set_hash(flipped["cases"])
    p = tmp_path / "flipped.json"
    p.write_text(json.dumps(flipped), encoding="utf-8")
    with pytest.raises(ValueError, match="disagrees"):
        ev.load_frozen(p)

    changed = json.loads(json.dumps(rec))
    changed["cases"][0]["draft_reply"] += "x"
    p2 = tmp_path / "changed.json"
    p2.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        ev.load_frozen(p2)

    unrev = json.loads(json.dumps(rec))
    unrev["review"]["status"] = "unreviewed"
    unrev["review"]["reviewed_by"] = ""
    unrev["sha256"] = ev.case_set_hash(unrev["cases"])
    p3 = tmp_path / "unrev.json"
    p3.write_text(json.dumps(unrev), encoding="utf-8")
    with pytest.raises(ValueError, match="Unreviewed"):
        ev.load_frozen(p3)
    ev.load_frozen(p3, allow_unreviewed=True)


def test_score_bare_go_is_not_acceptable():
    case = {
        "label": "GO",
        "rules": [],
        "draft_reply": "Dear resident, hello. Regards, CivicDesk.",
        "trigger_spans": [],
    }
    s = ev.score(case, "GO")
    assert s["decision"] == "GO"
    assert s["format_ok"] is False
    assert s["acceptable"] is False


def test_score_block_with_quote():
    rec = ev.load_frozen(COURSE)
    case = next(c for c in rec["cases"] if c["label"] == "BLOCK" and "R1" in c["rules"])
    span = case["trigger_spans"][0]
    reply = f"DECISION: BLOCK\nRULE: R1\nQUOTE: {span}"
    s = ev.score(case, reply)
    assert s["acceptable"] is True


def test_demo_rows_excluded_from_accuracy():
    rec = ev.load_frozen(COURSE)
    lab.use_backend("demo")

    def chat_fn(messages, model=None, max_tokens=96):
        return lab.chat(messages, model=model, max_tokens=max_tokens)

    rows = ev.run_eval(rec["cases"][:3], rec.get("generator", {}).get("model") or "demo", chat_fn, warmup=True)
    assert all(r["mode"] != "live" for r in rows)
    summary = ev.aggregate(rows)
    assert summary["rows_live"] == 0
    assert summary["acceptable"] == 0
    assert summary["measured"] is False
    assert summary["attempt_input_tokens_total"] == 0


def test_cost_undefined_and_shares():
    assert ev.cost_per_acceptable(1.0, 0) is None
    assert ev.cost_per_acceptable(None, 5) is None
    assert ev.cost_per_acceptable(0.30, 15) == pytest.approx(0.02)
    olmo = ev.compute_cost(0.75, 1.0, 120 / 300)
    phi = ev.compute_cost(0.75, 1.0, 180 / 300)
    assert olmo + phi == pytest.approx(0.75)
    assert ev.api_cost(7200, 900, 0.40, 1.60) == pytest.approx(0.00432)


def test_remote_redacts_key(monkeypatch):
    secret = "sk-SECRET-FAKE-KEY-12345"
    monkeypatch.setenv("GROQ_API_KEY", secret)
    remote.forget_keys()
    status = remote.set_key("groq")
    assert secret not in status

    class FakeFP(io.BytesIO):
        def __init__(self):
            super().__init__(f"unauthorized {secret}".encode())

    def boom(*_a, **_k):
        raise urllib.error.HTTPError(
            "https://api.groq.com/openai/v1/chat/completions",
            401,
            "Unauthorized",
            hdrs=None,
            fp=FakeFP(),
        )

    monkeypatch.setattr(remote.urllib.request, "urlopen", boom)
    r = remote.remote_chat("groq", [{"role": "user", "content": "hi"}])
    assert r["mode"] == "error"
    assert secret not in (r.get("error") or "")
    assert "[key removed]" in (r.get("error") or "")
    remote.forget_keys()


def test_chat_demo_usage_source():
    lab.use_backend("demo")
    r = lab.chat([{"role": "user", "content": "hello"}])
    assert r["usage"] is None
    assert "demo" in r["usage_source"]
    assert r["finish_reason"] is None
    assert r["canned"] is True
