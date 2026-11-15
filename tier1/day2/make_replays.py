"""Instructor: record genuine live RAG runs in the course container.

Do not hand-write replay contents. Commit the JSON only after a live run
(mode == live, generation_succeeded True). Demo/fallback replies are refused.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import civicdesk_rag as rag

HERE = Path(__file__).resolve().parent
OUT = HERE / "logs" / "replay"
OUT.mkdir(parents=True, exist_ok=True)


def _meta(lab) -> dict:
    cfg = lab.endpoint_config()
    return {
        "date": time.strftime("%Y-%m-%d"),
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "civicdesk_lab": cfg,
        "hardware": lab.gpu_note(),
        "decoding": {"temperature": 0.0, "max_tokens": 256, "timeout_s": rag.CHAT_TIMEOUT_S},
        "known_answer_sha256": rag.load_known_answer_set()["sha256"],
    }


def main() -> None:
    lab = rag.import_lab()
    if lab.endpoint_config().get("mode") != "live":
        raise SystemExit("make_replays.py needs a live Day 1 backend. Refusing demo/fallback.")
    meta = _meta(lab)
    qs = {x["id"]: x for x in rag.load_questions()}
    ka = {i["id"]: i for i in rag.load_known_answer_set()["items"]}

    for qid in ("Q-ATTACH", "Q-C2", "Q-PWD"):
        out = rag.generate_with_rag(qs[qid]["user"], role="clerk", item=ka.get(qid))
        if not out["generation_succeeded"]:
            raise SystemExit(f"{qid} was not live: {out.get('fallback_reason')}")
        rec = {**meta, "id": qid, **{k: out[k] for k in out if k != "visible_chunks"}}
        rec["visible_chunks"] = [
            {"id": c["id"], "text": c["text"], "version": c.get("version"), "status": c.get("status")}
            for c in out["visible_chunks"]
        ]
        rec["question"] = qs[qid]["user"]
        rec["role"] = "clerk"
        rec["config"] = {"retriever": "keyword", "min_score": 2, "current_only": False, "system": "STRICT_SYSTEM"}
        (OUT / f"T1-08_{qid}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", f"T1-08_{qid}.json", "model", out.get("model"))

    def dump_set(name: str, config: dict, live_ids: list[str]) -> None:
        rag.reset_run_counts()
        table = rag.run_known_answer_set(config, live_ids=live_ids, replay=None)
        if table["totals"]["live"] == 0:
            raise SystemExit(f"{name}: no live items")
        items = []
        for row in table["rows"]:
            items.append({**row, "question": ka[row["id"]]["user"], "role": ka[row["id"]].get("role", "clerk"), "config": config})
        rec = {**meta, "config": config, "items": items, "totals": table["totals"]}
        (OUT / name).write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", name)

    cfg1 = {"retriever": "keyword", "min_score": 2, "current_only": False, "system": "STRICT_SYSTEM", "k": 3}
    dump_set("T1-09_run1.json", cfg1, [i["id"] for i in rag.load_known_answer_set()["items"] if i["id"] != "Q-INJECT"])
    dump_set(
        "T1-09_run2_current_only.json",
        {**cfg1, "current_only": True},
        [i["id"] for i in rag.load_known_answer_set()["items"] if i["id"] != "Q-INJECT"],
    )

    inj = rag.load_injection_chunk()
    out = rag.generate_with_rag("May attachments stay on a personal laptop overnight?", role="clerk", chunks_override=[inj])
    if not out["generation_succeeded"]:
        raise SystemExit("injection replay was not live")
    rec = {**meta, "id": "Q-INJECT", **{k: out[k] for k in out if k != "visible_chunks"}}
    (OUT / "T1-10_injection.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote T1-10_injection.json")


if __name__ == "__main__":
    main()
