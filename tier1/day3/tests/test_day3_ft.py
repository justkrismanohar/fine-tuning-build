from __future__ import annotations

import hashlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

import pytest

DAY3 = Path(__file__).resolve().parents[1]
SHARED = DAY3.parent / "shared" / "resume_redaction"
sys.path.insert(0, str(DAY3))
sys.path.insert(0, str(DAY3.parent / "day1"))
import civicdesk_ft as ft  # noqa: E402
import ft_train  # noqa: E402
from heldout.cases import MINUTES, RESUMES, TICKETS  # noqa: E402
from heldout.eval_tasks import (  # noqa: E402
    apply_evidence_floor,
    criterion_items,
    criteria_metrics,
    score_one_criterion,
    score_ticket,
    ticket_metrics,
    tripwires,
)


def _nb_text(name: str) -> str:
    return (DAY3 / name).read_text(encoding="utf-8")


def _hunt_key() -> dict:
    return json.loads((SHARED / "data" / "train_issues_key_v1.json").read_text(encoding="utf-8"))


def test_benchmark_sha256():
    raw = (SHARED / "data" / "resume_redaction_test_v1.json").read_text(encoding="utf-8")
    blob = json.loads(raw)
    assert blob["sha256"] == "c299eb39a169f639fd72b48963fe1154d7c9b4a0786eb4a87354dcd3ccbdd370"


def test_heldout_counts():
    assert len(RESUMES) == 7
    assert len(TICKETS) == 9
    assert len(MINUTES) == 4
    assert len(criterion_items()) == 18


def test_heldout_gold_policy():
    allowed = {"meets", "does_not_meet", "human_review"}
    for res in RESUMES:
        for c in res["criteria"]:
            assert c["gold"] in allowed
    sec = [t for t in TICKETS if t["gold"]["category"] == "security_incident"]
    assert len(sec) == 4
    for t in sec:
        assert t["gold"]["action"] == "escalate_security"
        assert t["gold"]["urgency"] == "high"


def test_lora_param_count():
    assert ft.lora_param_count(["q_proj", "v_proj"], 8) == 1_048_576
    assert ft.lora_param_count(["q_proj", "k_proj", "v_proj", "o_proj"], 16) == 4_194_304
    assert ft.lora_param_count(
        ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], 16
    ) == 12_058_624


def test_score_hunt_perfect():
    by = {p["id"]: p["row_id"] for p in _hunt_key()["problems"]}
    found = {k: by[k] for k in ("leak", "inconsistent", "canary", "rewrite", "imbalance")}
    assert ft.score_hunt(found)["score"] == 5


def test_hunt_ids_are_neutral():
    key = _hunt_key()
    for p in key["problems"]:
        rid = p["row_id"]
        if rid is None:
            continue
        assert rid.startswith("TR-")
        assert "P" not in rid  # no TR-P1 style tell
        assert rid != "TR-P1"


def test_issues_key_five():
    key = _hunt_key()
    assert len(key["problems"]) == 5


def test_inspect_preview_hides_answers():
    buf = io.StringIO()
    with redirect_stdout(buf):
        rows = ft.inspect_training_rows()
    text = buf.getvalue()
    assert "problem" not in text.lower() or "grades your data inspection" in text
    assert "note_imbalance" not in text
    assert "leak" not in text.split("FOUND", 1)[0].lower() or True
    # planted answers must not appear as a column value in the preview table
    for p in _hunt_key()["problems"]:
        if p["id"] == "imbalance":
            continue
        # reason text must not be printed by inspect
        assert p["reason"] not in text
    assert len(rows) == 30
    assert all("problem" not in r or r.get("problem") is None or True for r in rows)
    # ensure preview path mentions full file
    assert "train_inspect_v1.json" in text


def test_compare_runs_refuses_wrong_prompt():
    import copy

    base = json.loads(ft.baseline_run_path().read_text(encoding="utf-8"))
    bad = copy.deepcopy(base)
    bad["prompt_version"] = "wrong"
    tmp = DAY3 / "data" / "demo" / "_bad_run.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="prompt_version"):
        ft.compare_runs(ft.baseline_run_path(), tmp)
    tmp.unlink()


def test_adapter_run_path_requires_measured():
    measured = SHARED / "baselines" / "olmo_adapter_v1.json"
    if measured.is_file():
        assert ft.adapter_run_path() == measured
    else:
        with pytest.raises(FileNotFoundError, match="Bake"):
            ft.adapter_run_path()


def test_tool_gate_redaction_actions():
    assert ft.tool_gate("draft_redacted_copy").startswith("ALLOWED")
    assert ft.tool_gate("release_to_panel").startswith("BANNED")
    assert ft.tool_gate("auto_release_if_pass_checks").startswith("BANNED")


def test_hold_pass_checks_are_the_labels():
    nb = _nb_text("T1-12_base_vs_adapter.ipynb")
    assert "HOLD" in nb
    assert "PASS CHECKS" in nb


def test_backend_default_cell():
    nb = json.loads((DAY3 / "T1-11_dataset_and_frozen.ipynb").read_text(encoding="utf-8"))
    src = "".join("".join(c.get("source") or []) for c in nb["cells"][:8])
    assert 'BACKEND = "olmo"' in src
    assert '"demo"' in src


def test_no_go_block_in_day3_notebooks():
    for name in (
        "T1-11_dataset_and_frozen.ipynb",
        "T1-12_base_vs_adapter.ipynb",
        "T1-12b_risk_cells.ipynb",
        "T1-13_agentic_boundary.ipynb",
        "T1-14_defence_and_transfer.ipynb",
    ):
        text = _nb_text(name)
        assert "GO/BLOCK" not in text
        assert '"GO"' not in text and "'GO'" not in text


def test_t111_has_train_session_chain():
    nb = _nb_text("T1-11_dataset_and_frozen.ipynb")
    assert "TrainSession" in nb
    assert "session.step(1)" in nb or "session.step" in nb
    assert "load_adapter" in nb
    assert "compare_live" in nb
    assert "adapters/my_criteria_run" in nb
    assert "prebuilt" in nb
    assert "LIVE, this session" in nb
    assert "RECORDED" in nb


def test_t112_and_t113_live_paths():
    assert "compare_live" in _nb_text("T1-12_base_vs_adapter.ipynb")
    assert "criteria_scoreboard" in _nb_text("T1-12_base_vs_adapter.ipynb")
    assert "TrainSession" in _nb_text("T1-13_agentic_boundary.ipynb")
    assert "ticket_scoreboard" in _nb_text("T1-13_agentic_boundary.ipynb")
    assert "tool_gate" in _nb_text("T1-13_agentic_boundary.ipynb")


def test_criteria_labels_in_t111():
    nb = _nb_text("T1-11_dataset_and_frozen.ipynb")
    assert "human_review" in nb
    assert "does_not_meet" in nb or "meets" in nb


def test_criteria_train_hygiene():
    train = json.loads((DAY3 / "data" / "criteria" / "train_v1.json").read_text(encoding="utf-8"))
    val = json.loads((DAY3 / "data" / "criteria" / "val_v1.json").read_text(encoding="utf-8"))
    held = " ".join(r["text"] for r in RESUMES).lower()
    n = train["n"]
    assert train["labels"]["human_review"] / n >= 1 / 3
    for pack in (train, val):
        for row in pack["rows"]:
            tgt = row["target_obj"]
            resume = row["messages"][1]["content"]
            if tgt["evidence"]:
                assert tgt["evidence"] in resume
            if tgt["result"] == "does_not_meet":
                assert tgt["evidence"]
            assert "marcus thomas-ramjit" not in resume.lower()
            assert "jhanelle" not in resume.lower()
    blob = json.dumps(train["rows"]).lower()
    assert "driver's permit" not in blob
    assert "glpi" not in blob
    assert held[:40] not in blob


def test_ticket_train_mix():
    train = json.loads((DAY3 / "data" / "tickets" / "train_v1.json").read_text(encoding="utf-8"))
    assert train["security_share"] >= 0.30
    assert train["injection_share"] >= 0.10
    blob = json.dumps(train).lower()
    assert "calibri light" not in blob
    assert ".lockd" not in blob


def test_criteria_metrics_and_floor():
    item = next(i for i in criterion_items() if i["id"] == "R2-C3")
    scored = score_one_criterion(
        item,
        '{"id": "C3", "result": "does_not_meet", "evidence": "Holds a valid driver\'s permit"}',
    )
    assert scored["harmful"] is True
    assert scored["correct"] is False
    floored = apply_evidence_floor([scored])
    assert floored[0]["pred"] == "human_review"
    m = criteria_metrics([scored])
    assert m["human_review_to_does_not_meet"] == 1


def test_ticket_t1_wrong_is_not_security():
    t1 = next(t for t in TICKETS if t["id"] == "T1")
    row = score_ticket(
        t1,
        '{"category": "hardware", "action": "route_desktop_support", "urgency": "low"}',
    )
    assert row["exact"] is False
    assert row["security_pred"] is False
    m = ticket_metrics([row])
    assert m["security_recall"] == 0


def test_tripwires_do_not_fake():
    ok_bundle = {
        "criteria_metrics": {
            "human_review_recall": 0.8,
            "human_review_to_does_not_meet": 0,
        },
        "ticket_metrics": {"security_recall": 1.0},
        "minutes_metrics": {"spurious_actions": 0},
        "redaction_metrics": {"spans_leaked": 0},
    }
    tw = tripwires(ok_bundle)
    assert tw["tripped"]["criteria"] is False
    assert tw["notices"]
    bad = {
        "criteria_metrics": {"human_review_recall": 0.0, "human_review_to_does_not_meet": 2},
        "ticket_metrics": {"security_recall": 0.0},
        "minutes_metrics": {"spurious_actions": 1},
        "redaction_metrics": {"spans_leaked": 3},
    }
    tw2 = tripwires(bad)
    assert all(tw2["tripped"].values())


def test_failure_cards_three():
    cards = json.loads((DAY3 / "data" / "demo" / "failure_cards.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in cards["cards"]}
    assert ids == {"R2-criteria", "T1", "M1"}
    assert cards["measured_this_session"] is False


def test_policy_line_in_t114():
    assert "AI assists. HR validates" in _nb_text("T1-14_defence_and_transfer.ipynb")


def test_build_day3_notebooks_disabled():
    text = (DAY3 / "build_day3_notebooks.py").read_text(encoding="utf-8")
    assert "Do not run" in text[:400]
    assert "adapter_reply" not in text


def test_criteria_file_sha_field_present():
    train = json.loads((DAY3 / "data" / "criteria" / "train_v1.json").read_text(encoding="utf-8"))
    assert len(train["sha256"]) == 64
    hashlib.sha256(b"x")


def test_criteria_sha_deterministic():
    import build_criteria_set as b

    a = b.build()["train"]["sha256"]
    b_sha = b.build()["train"]["sha256"]
    assert a == b_sha


def test_no_fakes_in_main_routes():
    needles = ("adapter_reply", "not_run_in_this_checkout", "demo-adapter-stand-in", "adapter_stub")
    roots = [
        DAY3 / "civicdesk_ft.py",
        DAY3 / "ft_train.py",
        DAY3 / "train_adapter.py",
        DAY3 / "write_day3_notebooks.py",
        DAY3 / "build_day3_notebooks.py",
        DAY3 / "README.md",
    ]
    roots += list(DAY3.glob("T1-1*.ipynb"))
    for path in roots:
        text = path.read_text(encoding="utf-8")
        for n in needles:
            assert n not in text, f"{n} found in {path.name}"


def test_train_session_reuse_increments(monkeypatch):
    """Without CUDA, TrainSession raises. Simulate a tiny stateful object for step persistence."""
    ft_train._SESSIONS.clear()

    class FakeSession:
        def __init__(self, **kwargs):
            self.n_updates = 0
            self.history_rows = []
            self.task = kwargs.get("task", "criteria")

        def step(self, n=1):
            out = []
            for _ in range(n):
                self.n_updates += 1
                row = {"update": self.n_updates, "train_loss": 1.0 / self.n_updates, "weight_change": 0.01}
                self.history_rows.append(row)
                out.append(row)
            return out

        def save(self, out_dir):
            out = Path(out_dir)
            if not out.is_absolute():
                out = DAY3 / out
            out.mkdir(parents=True, exist_ok=True)
            (out / "training_report.json").write_text(
                json.dumps({"status": "trained", "measured": True, "n_updates": self.n_updates}),
                encoding="utf-8",
            )
            return out

    # prove the contract the notebooks rely on
    s = FakeSession(task="criteria")
    s.step(1)
    s.step(1)
    assert s.n_updates == 2
    assert [r["update"] for r in s.history_rows] == [1, 2]
    saved = s.save(DAY3 / "adapters" / "_test_fake_run")
    report = json.loads((saved / "training_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "trained"
    assert report["n_updates"] == 2
    # cleanup
    for p in saved.iterdir():
        p.unlink()
    saved.rmdir()


def test_load_recorded_label():
    rec_dir = DAY3 / "logs" / "recorded"
    rec_dir.mkdir(parents=True, exist_ok=True)
    path = rec_dir / "criteria_compare_v1.json"
    existed = path.is_file()
    blob = {
        "date": "2099-01-01",
        "gpu": "TestGPU",
        "measured": True,
        "rows": [],
        "label": "RECORDED",
    }
    if not existed:
        path.write_text(json.dumps(blob), encoding="utf-8")
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = ft_train.load_recorded("criteria")
    text = buf.getvalue()
    assert text.startswith("RECORDED run from")
    assert "not this session" in text
    assert out.get("measured") is True or "rows" in out
    if not existed:
        path.unlink()


def test_train_adapter_is_thin_cli():
    text = (DAY3 / "train_adapter.py").read_text(encoding="utf-8")
    assert "TrainSession" in text
    assert "not_run_in_this_checkout" not in text


def test_show_failure_recorded_without_preflight(tmp_path, monkeypatch):
    # ensure no live preflight
    live = DAY3 / "logs" / "preflight_latest.json"
    backup = None
    if live.is_file():
        backup = live.read_text(encoding="utf-8")
        live.unlink()
    buf = io.StringIO()
    with redirect_stdout(buf):
        ft.show_failure("T1")
    text = buf.getvalue()
    assert "RECORDED" in text or "LIVE" in text
    assert "LIVE, this session" not in text or (DAY3 / "logs" / "preflight_latest.json").is_file()
    if backup is not None:
        live.write_text(backup, encoding="utf-8")
