"""Thin CLI around TrainSession. Instructor bake / optional learner short run.

  python train_adapter.py --task criteria --max-steps 40 --out adapters/olmo-criteria-lora-v1
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ft_train import TrainSession

HERE = Path(__file__).resolve().parent


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--task", default="criteria", choices=["criteria", "tickets", "redact"])
    p.add_argument("--out", default="")
    p.add_argument("--max-steps", type=int, default=40)
    p.add_argument("--rank", type=int, default=8)
    p.add_argument("--alpha", type=int, default=16)
    p.add_argument("--targets", default="q_proj,v_proj")
    args = p.parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    defaults = {
        "criteria": HERE / "adapters" / "olmo-criteria-lora-v1",
        "tickets": HERE / "adapters" / "olmo-tickets-lora-v1",
        "redact": HERE / "adapters" / "olmo-resume-redact-lora-v1",
    }
    out = Path(args.out) if args.out else defaults[args.task]
    print("train_adapter.py → TrainSession")
    try:
        session = TrainSession(task=args.task, targets=targets, rank=args.rank, alpha=args.alpha)
    except RuntimeError as exc:
        print(exc)
        return 2
    session.summary()
    session.show_example(0)
    session.step(max(1, args.max_steps))
    session.validate()
    session.save(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
