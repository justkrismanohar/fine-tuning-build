"""Download OLMo and Phi into /models so docker build bakes the weights in.

Same ids as tier1/day1/build_llms.py. This is copy-to-disk, not training.
"""
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download

OLMO = "allenai/OLMo-2-0425-1B-Instruct"
PHI = "microsoft/Phi-4-mini-instruct"
ROOT = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models"))

MODELS = {
    "olmo": OLMO,
    "phi": PHI,
}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    wanted = [m.strip() for m in os.environ.get("CIVICDESK_DOWNLOAD", "olmo,phi").split(",") if m.strip()]
    for key in wanted:
        repo = MODELS[key]
        dest = ROOT / key
        print("downloading", repo, "->", dest)
        snapshot_download(repo_id=repo, local_dir=str(dest))
        print("  done", dest)


if __name__ == "__main__":
    main()
