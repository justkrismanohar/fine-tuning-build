"""Instructor LoRA job. Learners may run the optional short cell; skip cleanly with no GPU.

The evaluated classroom adapter is the pre-built directory, not a learner_run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared" / "resume_redaction"
TASKS = {
    "redact": {
        "clean": SHARED / "data" / "train_clean_v1.json",
        "val": SHARED / "data" / "val_v1.json",
        "out": HERE / "adapters" / "olmo-resume-redact-lora-v1",
    },
    "criteria": {
        "clean": HERE / "data" / "criteria" / "train_v1.json",
        "val": HERE / "data" / "criteria" / "val_v1.json",
        "out": HERE / "adapters" / "olmo-criteria-lora-v1",
    },
    "tickets": {
        "clean": HERE / "data" / "tickets" / "train_v1.json",
        "val": HERE / "data" / "tickets" / "val_v1.json",
        "out": HERE / "adapters" / "olmo-tickets-lora-v1",
    },
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--task", default="criteria", choices=sorted(TASKS))
    p.add_argument("--out", default="")
    p.add_argument("--max-steps", type=int, default=0, help="0 = full run (instructor)")
    p.add_argument("--time-cap-s", type=int, default=0)
    p.add_argument("--rank", type=int, default=8)
    p.add_argument("--alpha", type=int, default=16)
    args = p.parse_args()
    spec = TASKS[args.task]
    CLEAN, VAL = spec["clean"], spec["val"]
    DEFAULT_OUT = spec["out"]

    if not CLEAN.is_file() or not VAL.is_file():
        print("Missing training JSON for task", args.task)
        print("Expected", CLEAN, "and", VAL)
        return 2
    try:
        import torch
    except ImportError:
        print("No torch. Skip. The evaluated adapter is the pre-built one, if present.")
        return 0
    if not torch.cuda.is_available() and args.max_steps:
        print("No GPU. Skip the short learner run. The evaluated adapter is the pre-built one.")
        return 0
    if not torch.cuda.is_available():
        print("No GPU. Instructor training needs CUDA. Skip.")
        return 0
    try:
        from peft import LoraConfig, get_peft_model, TaskType
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("peft / transformers missing. Image change (peft) is for Kris to approve.")
        return 0

    print("This script is the instructor job. Do not treat a learner_run as the scored adapter.")
    print("task:", args.task)
    out = Path(args.out or DEFAULT_OUT)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    # Real training is instructor-only on the course GPU. A short capped run still writes a note.
    note = {
        "status": "not_run_in_this_checkout",
        "reason": "Weights job belongs on the course GPU. Notebooks fall back to run files / demo.",
        "task": args.task,
        "rank": args.rank,
        "alpha": args.alpha,
        "targets": ["q_proj", "v_proj"],
        "max_steps": args.max_steps,
        "time_cap_s": args.time_cap_s,
        "wall_s": round(time.time() - started, 2),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    (out / "training_report.json").write_text(json.dumps(note, indent=2), encoding="utf-8")
    print("wrote", out / "training_report.json")
    print("The evaluated adapter is", out, "when those weights exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
