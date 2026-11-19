"""Download OLMo and Phi into /models so docker build bakes the weights in.

Same ids as tier1/day1/build_llms.py. This is copy-to-disk, not training.
Pins a Hugging Face revision and writes CIVICDESK_REVISION.txt beside the weights.
"""
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download

OLMO = "allenai/OLMo-2-0425-1B-Instruct"
PHI = "microsoft/Phi-4-mini-instruct"
ROOT = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models"))

# MODELS = {
#     "olmo": OLMO,
#     "phi": PHI,
# }


MODELS = {
    "olmo": OLMO
}

# OLMo pin from the T1-03 live check (12 Nov 2026). Phi pin is current main as of that week.
REVISIONS = {
    "olmo": os.environ.get("CIVICDESK_OLMO_REVISION", "48d788eca847d4d7548f375ad03d3c9312f6139e"),
    "phi": os.environ.get("CIVICDESK_PHI_REVISION", "cfbefacb99257ffa30c83adab238a50856ac3083"),
}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    # wanted = [m.strip() for m in os.environ.get("CIVICDESK_DOWNLOAD", "olmo,phi").split(",") if m.strip()]
    wanted = [m.strip() for m in os.environ.get("CIVICDESK_DOWNLOAD", "olmo").split(",") if m.strip()]
    for key in wanted:
        repo = MODELS[key]
        dest = ROOT / key
        revision = REVISIONS.get(key) or None
        print("downloading", repo, "revision", revision or "(unpinned)", "->", dest)
        snapshot_download(repo_id=repo, local_dir=str(dest), revision=revision)
        (dest / "CIVICDESK_REVISION.txt").write_text(revision or "unknown (not pinned)", encoding="utf-8")
        print("  done", dest, "revision", revision)


if __name__ == "__main__":
    main()
