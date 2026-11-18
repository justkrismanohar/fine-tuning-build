"""Build a labelled demo adapter run from the measured baseline + gold expected.

measured: false. Never copy this into baselines/ as a scored run.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY3 = HERE.parent.parent
SHARED = DAY3.parent / "shared" / "resume_redaction"
sys.path.insert(0, str(SHARED))
sys.path.insert(0, str(DAY3.parent / "day1"))
import redaction_eval as R  # noqa: E402

BENCH = R.load_benchmark()
BASE = json.loads((SHARED / "baselines" / "olmo_baseline_v1.json").read_text(encoding="utf-8"))


def main() -> None:
    rows = R.evaluate(BENCH, BASE["outputs"], BASE.get("latency_s"))
    leaked_hold = [r for r in rows if r["leaked"] and str(r["decision"]).upper().startswith("HOLD")]
    altered = [r for r in rows if r["over_redacted"] or r["unrelated_edit"] or r["acceptable"]]
    by = {d["id"]: d for d in BENCH["docs"]}
    demo = deepcopy(BASE)
    demo["model"] = "demo-adapter-stand-in"
    demo["measured"] = False
    demo["notes"] = {k: "demo stand-in; not scored" for k in demo["outputs"]}
    demo["adapter_name"] = "olmo-resume-redact-lora-demo"
    demo["training_data_version"] = "train-clean-v1"
    # Two "fixed": leaked HOLD -> gold expected
    for r in leaked_hold[:2]:
        demo["outputs"][r["id"]] = by[r["id"]]["expected"]
        demo["notes"][r["id"]] = "demo: copied gold expected (illustration)"
    # Two "broken": copy a PASS-looking output and over-redact keep text
    candidates = [r for r in rows if r["id"] not in {leaked_hold[0]["id"], leaked_hold[1]["id"]}]
    for r in candidates[:2]:
        doc = by[r["id"]]
        text = doc["expected"]
        if doc["keep"]:
            text = text.replace(doc["keep"][0], "[PERSON]")
        demo["outputs"][r["id"]] = text
        demo["notes"][r["id"]] = "demo: over-redacted a keep span (illustration)"
    HERE.mkdir(parents=True, exist_ok=True)
    path = HERE / "olmo_adapter_demo_v1.json"
    path.write_text(json.dumps(demo, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path, "measured", demo["measured"])


if __name__ == "__main__":
    main()
