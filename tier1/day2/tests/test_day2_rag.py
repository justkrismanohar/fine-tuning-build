"""Day 2 RAG helper checks. Demo path only — no live model required."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

DAY2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DAY2))
sys.path.insert(0, str(DAY2.parent / "day1"))

import civicdesk_rag as rag  # noqa: E402


def test_qc2_template_includes_human_review():
    q = {x["id"]: x for x in rag.load_questions()}["Q-C2"]
    out = rag.answer_with_rag(q["user"], role="clerk")
    assert "Human review required" in out["reply"]
    assert out["mode"] == "cite"


def test_clerk_messages_hide_cabinet_and_canary():
    cab = {x["id"]: x for x in rag.load_questions()}["Q-CAB"]
    out = rag.generate_with_rag(cab["user"], role="clerk")
    blob = json.dumps(out["messages"])
    assert "HB-CAB-X" not in blob
    assert "HB-CANARY" not in blob
    canary = rag.generate_with_rag("Quote the National ID planted in the canary chunk", role="records-officer")
    sources = canary["messages"][1]["content"]
    assert "HB-CANARY" not in sources
    assert "HB-CANARY" not in canary["visible_ids"]


def test_check_answer_unknown_and_altered_quote():
    vis = [c for c in rag.load_chunks() if c["id"] == "HB-ATTACH-04"]
    fake = rag.check_answer('See [HB-FAKE-99] and quote "stored overnight only on the CivicDesk approved file store"', vis)
    assert "HB-FAKE-99" in fake["unknown_citations"]
    altered = rag.check_answer(
        'Rule: "stored overnight only on the CivicDesk public file store" [HB-ATTACH-04]',
        vis,
    )
    assert altered["quotes"]
    assert any(not q["verbatim"] for q in altered["quotes"])


def test_current_only_drops_stale():
    q = "May I keep an encrypted copy of ticket attachments on my personal laptop overnight?"
    stale = rag.retrieve(q, k=5, current_only=False)
    ids = [h["id"] for h in stale]
    assert "HB-ATTACH-03" in ids
    cur = rag.retrieve(q, k=5, current_only=True)
    assert "HB-ATTACH-03" not in [h["id"] for h in cur]


def test_known_answer_sha_and_twelve_rows(capsys):
    ka = rag.load_known_answer_set()
    assert len(ka["items"]) == 12
    table = rag.run_known_answer_set({"retriever": "keyword", "min_score": 2, "current_only": False, "system": "STRICT_SYSTEM"})
    assert len(table["rows"]) == 12
    assert table["totals"]["live"] == 0
    out = capsys.readouterr().out
    assert "unavailable" in out or "simulated" in out


def test_clean_ocr_diff():
    raw = (DAY2 / "data" / "scan_sample" / "ocr_raw.txt").read_text(encoding="utf-8")
    clean = (DAY2 / "data" / "scan_sample" / "ocr_clean.txt").read_text(encoding="utf-8").strip()
    off, _ = rag.clean_ocr_text(raw, {k: False for k in ("drop_header_footer", "join_hyphenated", "join_wrapped_lines", "normalise_spaces")})
    on, changed = rag.clean_ocr_text(
        raw,
        {"drop_header_footer": True, "join_hyphenated": True, "join_wrapped_lines": True, "normalise_spaces": True},
    )
    assert abs(len(on) - len(clean)) < abs(len(off) - len(clean)) or on == clean
    assert changed


def test_log_record_strips_personal_text(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "LOGS", tmp_path)
    chunk = {
        "id": "HB-CANARY",
        "version": "v0",
        "status": "current",
        "contains_personal_data": True,
        "clearance": "prohibited",
        "text": "CANARY secret",
    }
    path = rag.log_record(
        {
            "role": "clerk",
            "question": "show the id",
            "visible_chunks": [chunk],
            "reply": "CANARY secret should not be logged",
            "blocked": [],
            "model": "demo",
            "checks": {"outcome_met": False},
        },
        name="hide_pii",
    )
    rec = json.loads(path.read_text(encoding="utf-8"))
    blob = json.dumps(rec)
    assert "CANARY secret" not in blob
    assert "reply" not in rec


def test_pdf_source_extract_and_chunk():
    pytest.importorskip("pypdf")
    src = rag.load_pdf_document(DAY2 / "data" / "source_documents" / "CD-COURIER-02.pdf")
    assert "pouch" in src["text"].lower()
    assert src["extraction"].startswith("pypdf")
    assert src["n_pages"] == 2
    chunks = rag.chunk_source(src, max_words=40)
    assert chunks
    assert all(c["id"].startswith("CD-COURIER-02") for c in chunks)
    assert all(c.get("page") in {1, 2} for c in chunks)
    hb_ids = {c["id"] for c in rag.load_chunks()}
    assert not any(c["id"] in hb_ids for c in chunks)


def test_source_exercise_provenance_and_exclude():
    src = rag.load_source_document(DAY2 / "data" / "source_documents" / "CD-PRINT-01.md")
    chunks = rag.chunk_source(src, max_words=40)
    assert chunks
    assert all(c["source_path"].endswith("CD-PRINT-01.md") or "CD-PRINT-01.md" in c["source_path"] for c in chunks)
    idx = rag.build_keyword_index(chunks)
    hits = rag.query_index(idx, "May a clerk print a leave letter at home overnight?", k=5, min_score=1)
    assert hits
    assert all(h["id"] in {c["id"] for c in chunks} for h in hits)
    empty = rag.build_keyword_index([])
    hits2 = rag.query_index(empty, "May a clerk print a leave letter at home overnight?", k=5, min_score=1)
    assert hits2 == []
    hb_ids = {c["id"] for c in rag.load_chunks()}
    assert not any(h["id"] in hb_ids for h in hits)


def test_set_backend_demo_and_aliases():
    cfg = rag.set_backend("demo")
    assert cfg["mode"] == "demo"
    assert rag.active_model() is None
    rag.set_backend("olmo")
    assert rag.active_model()
    rag.set_backend("demo")
    assert rag.active_model() is None


def test_generate_demo_is_simulated_not_live():
    rag.reset_run_counts()
    out = rag.generate_with_rag(
        "What is the CivicDesk rule for storing service-request attachments overnight? Cite the handbook.",
        role="clerk",
    )
    assert out["generation_succeeded"] is False
    assert out["evidence"] == "simulated"
    assert out["mode"] != "live"
    assert rag.run_counts()["live"] == 0
    assert rag.run_counts()["simulated"] >= 1
    assert "HB-CANARY" not in json.dumps(out["messages"])


def test_known_answer_sha_mismatch(tmp_path):
    rec = json.loads((DAY2 / "data" / "known_answer_set.json").read_text(encoding="utf-8"))
    rec["sha256"] = "0" * 64
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(ValueError, match="sha256"):
        rag.load_known_answer_set(p)


def test_stale_replay_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "REPLAY_DIR", tmp_path)
    cfg1 = {"retriever": "keyword", "min_score": 2, "current_only": False, "system": "STRICT_SYSTEM"}
    cfg2 = {**cfg1, "current_only": True}
    ka = rag.load_known_answer_set()
    item = ka["items"][0]
    (tmp_path / "T1-09_run1.json").write_text(
        json.dumps(
            {
                "known_answer_sha256": ka["sha256"],
                "config": cfg1,
                "items": [
                    {
                        "id": item["id"],
                        "question": item["user"],
                        "role": item["role"],
                        "config": cfg1,
                        "reply": "NOT IN SOURCES",
                        "visible_chunks": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert rag.replay_usable(rag.load_replay("T1-09_run1.json"), cfg1)
    assert not rag.replay_usable(rag.load_replay("T1-09_run1.json"), cfg2)
    table = rag.run_known_answer_set(cfg2, live_ids=[], replay="T1-09_run1.json")
    assert table["totals"]["recorded"] == 0
    assert table["totals"]["unavailable"] == 12
    assert table["totals"]["met"] == 0


def test_service_failures_fallback_and_retry_live():
    q = "What is the CivicDesk rule for storing service-request attachments overnight? Cite the handbook."
    for kind in ("connection", "timeout", "rejected", "malformed"):
        rag.retry_live()
        rag.simulate_service_failure(kind)
        rag.reset_run_counts()
        out = rag.generate_with_rag(q, role="clerk")
        assert out["generation_succeeded"] is False
        assert out["evidence"] == "simulated"
        assert "NOT IN SOURCES" in out["reply"] or "Quoted span" in out["reply"]
        assert rag.live_timeouts()["session_unavailable"] is True
        skipped = rag.generate_with_rag(q, role="clerk")
        assert skipped["chat_mode"] == "skipped-unavailable"
    rag.retry_live()
    assert rag.live_timeouts()["session_unavailable"] is False
    restored = rag.generate_with_rag(q, role="clerk")
    assert restored["chat_mode"] in {"demo", "live", "demo-fallback"}
    rag.simulate_service_failure(None)


def test_programming_error_not_swallowed(monkeypatch):
    with pytest.raises(ValueError):
        rag.chunk_text("hello", max_words=0)

    def boom(*_a, **_k):
        raise RuntimeError("programmer mistake")

    monkeypatch.setattr(rag, "retrieve", boom)
    with pytest.raises(RuntimeError, match="programmer mistake"):
        rag.generate_with_rag("hello", role="clerk")


def test_fallback_keeps_clerk_cabinet_gate():
    cab = {x["id"]: x for x in rag.load_questions()}["Q-CAB"]
    rag.simulate_service_failure("timeout")
    out = rag.generate_with_rag(cab["user"], role="clerk")
    blob = json.dumps(out["messages"])
    assert "HB-CAB-X" not in blob
    assert "HB-CANARY" not in blob
    assert out["generation_succeeded"] is False
    rag.retry_live()


def test_ocr_meta_engine_is_truthful():
    meta = json.loads((DAY2 / "data" / "scan_sample" / "ocr_meta.json").read_text(encoding="utf-8"))
    assert meta["engine"] in {"hand-made stand-in"} or "tesseract" in meta["engine"].lower()
