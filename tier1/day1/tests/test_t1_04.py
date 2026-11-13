"""T1-04 licence lab checks. No GPU, no network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

DAY1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DAY1))

import licence_lab as L  # noqa: E402

NB = json.loads((DAY1 / "T1-04_openness_licences_gpu.ipynb").read_text(encoding="utf-8"))


def test_verify_passes():
    assert L.verify() is True


def test_find_not_found_and_hits():
    assert L.find("llama32_licence", "training data") == []
    assert L.find("ai2_guidelines", "military") == []
    assert L.find("llama32_licence", "royalty-free")
    assert L.find("llama32_licence", "hereby incorporated by reference")
    assert L.find("llama32_aup", "Military, warfare")
    assert L.find("apache", "Grant of Copyright License")
    assert L.find("ai2_guidelines", "illustrative and not exhaustive")


def test_check_format_and_classes():
    bad = L.check_format({"Q1": "", "Q2": "maybe"})
    assert bad
    ok = L.check_format({"Q1": "FOUND: §1.a — grant", "Q2": "NOT FOUND", "Q3": "NEED LINKED TERMS: AUP"})
    assert ok == []
    labels = L.check_classes({"S1": {"class": "permitted", "clause": "§2"}})
    assert labels == []
    labels = L.check_classes({"S1": {"class": "fine", "clause": ""}})
    assert labels


def test_t1_03_winner_old_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "LOGS", tmp_path)
    (tmp_path / "T1-03_scorecard.json").write_text(
        json.dumps(
            {
                "olmo": {"model": "olmo"},
                "phi": {"model": "phi"},
                "scores": {"olmo_quality_0to2": 2, "phi_quality_0to2": 1},
            }
        ),
        encoding="utf-8",
    )
    w = L.t1_03_winner()
    assert w["winner"] == "OLMo"
    assert w["olmo_score"] == 2
    assert w["phi_score"] == 1
    assert w["scale"] == "0to2"


def test_notebook_shape_and_banned_words():
    assert len(NB["cells"]) == 17
    tags = []
    blob = ""
    for c in NB["cells"]:
        src = "".join(c.get("source") or [])
        blob += src
        if c["cell_type"] == "code":
            first = src.lstrip().splitlines()[0]
            assert first.startswith(("# [RUN]", "# [CHANGE]", "# [OPTIONAL]"))
            tags.append(first)
    assert "# [RUN]" in " ".join(tags)
    low = blob.lower()
    assert "guarantee" not in low
    assert "cleared" not in low
    assert low.count("legal advice") == 1
    assert "you are allowed to" not in low
    gpu = "".join(NB["cells"][13]["source"])
    assert "Burst or standing" in gpu
    assert "4 minutes in the room" in gpu
    assert "Can it idle-stop" in gpu


def test_no_model_calls():
    blob = "".join("".join(c.get("source") or []) for c in NB["cells"] if c["cell_type"] == "code")
    assert "lab.chat" not in blob
    assert "civicdesk_eval" not in blob
