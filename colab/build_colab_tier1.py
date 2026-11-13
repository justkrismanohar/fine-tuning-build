"""Build Colab-track copies of Tier 1 notebooks (demo replies, no Docker/GPU)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parent
TIER1 = COURSE / "tier1"
GH = "justkrismanohar/fine-tuning-build"
COLAB_BASE = f"https://colab.research.google.com/github/{GH}/blob/main/colab"


def load_nb(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_nb(path: Path, nb: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", path.relative_to(COURSE))


def md_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip("\n").split("\n")],
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in text.strip("\n").split("\n")],
    }


def src(cell: dict) -> str:
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def set_src(cell: dict, text: str) -> None:
    cell["source"] = [line + "\n" for line in text.strip("\n").split("\n")]
    if cell.get("cell_type") == "code":
        cell["outputs"] = []
        cell["execution_count"] = None


def banner(day: str, filename: str) -> dict:
    url = f"{COLAB_BASE}/{day}/{filename}"
    img = "https://colab.research.google.com/assets/colab-badge.svg"
    return md_cell(
        f"""# Colab track — no Docker, no GPU, no live OLMo

This is the **demo** copy of `{filename}`. Replies that would have come from OLMo/Phi are **scripted** (`[OLMo demo]` / `[Phi-4-mini demo]`). Days 2–3 already work without a model.

The live-hosting course is `tier1/` + Docker (or [03_own_environment.md](https://github.com/{GH}/blob/main/03_own_environment.md)).

[![Open In Colab]({img})]({url})

**Runtime → CPU.** Then **Runtime → Run all**. First code cell clones the course (or finds it if you already have the folder).
"""
    )


def bootstrap(day: str) -> dict:
    # day is "day1" | "day2" | "day3"
    extra = ""
    if day == "day2":
        extra = """
# Day 2 helper lives here; Day 3 notebooks that import rag also add ../day2
"""
    return code_cell(
        f"""# [RUN] COLAB TRACK — find or clone the course, stay on demo replies
import os
import sys
import subprocess
from pathlib import Path

os.environ["CIVICDESK_COLAB"] = "1"
os.environ["CIVICDESK_MODE"] = "demo"

def _course_root() -> Path:
    markers = Path("tier1") / "day1" / "civicdesk_lab.py"
    for base in [Path("/content/fine-tuning-build"), Path.cwd(), *Path.cwd().resolve().parents]:
        if (base / markers).is_file():
            return base
    dest = Path("/content/fine-tuning-build")
    url = "https://github.com/justkrismanohar/fine-tuning-build.git"
    print("Cloning", url)
    subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])
    return dest

ROOT = _course_root()
DAY = ROOT / "tier1" / "{day}"
os.chdir(DAY)
if str(DAY) not in sys.path:
    sys.path.insert(0, str(DAY))
if "{day}" == "day3":
    d2 = str(ROOT / "tier1" / "day2")
    if d2 not in sys.path:
        sys.path.insert(0, d2)
print("COLAB TRACK")
print(" course:", ROOT)
print(" cwd   :", Path.cwd())
print(" Live OLMo/Phi are OFF. Later chat cells use canned CivicDesk replies.")

# Markdown images in Colab resolve from /content, not cwd
import shutil
content = Path("/content") if Path("/content").is_dir() else Path.cwd()
for folder in ("images", "cards"):
    src = DAY / folder
    dest = content / folder
    if src.is_dir() and dest.resolve() != src.resolve():
        shutil.copytree(src, dest, dirs_exist_ok=True)
        print(f" {{folder}} →", dest)
{extra}"""
    )


def strip_outputs(nb: dict) -> None:
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None


def prepend(nb: dict, day: str, filename: str, extra_md: str | None = None) -> dict:
    nb = copy.deepcopy(nb)
    strip_outputs(nb)
    cells = [banner(day, filename), bootstrap(day)]
    if extra_md:
        cells.append(md_cell(extra_md))
    nb["cells"] = cells + nb.get("cells", [])
    nb.setdefault("metadata", {})
    nb["metadata"]["colab"] = {"name": filename, "provenance": [], "toc_visible": True}
    return nb


def patch_01a(nb: dict) -> None:
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        text = src(cell)
        if "import build_llms as build" in text:
            set_src(
                cell,
                """# [RUN] COLAB TRACK — simulate check(); we do not start a GPU runtime
import json
import civicdesk_lab as lab

info = lab.simulate_hosting_check()
""",
            )
        elif 'ENGINE = "skip"' in text or "ENGINE =" in text and "vllm" in text:
            set_src(
                cell,
                """# COLAB TRACK: engine is locked. Docker course may use vllm / docker / hf.
ENGINE = "skip"
MODELS = ["olmo", "phi"]
print("ENGINE =", ENGINE, "(locked on Colab track)")
print("You still learn the hosting picture. You do not fetch weights here.")
""",
            )
        elif "build.download" in text:
            set_src(
                cell,
                """# [RUN] COLAB TRACK — do not download OLMo/Phi (several GB)
print("skipped download")
print("Official ids (Docker course fetches these):")
print("  allenai/OLMo-2-0425-1B-Instruct")
print("  microsoft/Phi-4-mini-instruct")
""",
            )
        elif "build.serve" in text:
            set_src(
                cell,
                """# [RUN] COLAB TRACK — no :8000 / :8001
import civicdesk_lab as lab

print("No local server. T1-01 will use canned [demo] replies.")
lab.simulate_hosting_skip_serve()
""",
            )
        elif "ping(" in text and "8000" in text:
            set_src(
                cell,
                """# [OPTIONAL] skipped — there is no live /v1 on this track
print("olmo", "demo (no HTTP)")
print("phi ", "demo (no HTTP)")
""",
            )


def patch_01(nb: dict) -> None:
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        text = src(cell)
        if "lab.use_backend" in text and "BACKEND" in text:
            text2 = text.replace('BACKEND = "local"', 'BACKEND = "demo"')
            text2 = text2.replace(
                'BACKEND = "demo"          # "demo" | "local" | "shared" | "custom"',
                'BACKEND = "demo"          # locked on Colab track',
            )
            if "CIVICDESK_COLAB" not in text2:
                text2 = text2.replace(
                    "cfg = lab.use_backend(BACKEND, **kwargs)",
                    "cfg = lab.use_backend(BACKEND, **kwargs)  # Colab forces demo",
                )
            set_src(cell, text2)


def patch_03(nb: dict) -> None:
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        text = src(cell)
        if "olmo = lab.chat" not in text:
            continue
        text2 = text.replace(
            '# lab.use_backend("local")   # or "demo" / "shared" / "custom"',
            'lab.use_backend("demo")  # Colab track — scripted OLMo vs Phi wording',
        )
        if "lab.use_backend(" not in text2:
            text2 = text2.replace(
                "import civicdesk_lab as lab\n",
                'import civicdesk_lab as lab\nlab.use_backend("demo")\n',
                1,
            )
        set_src(cell, text2)


DAYS = {
    "day1": [
        "T1-01a_build_from_scratch.ipynb",
        "T1-01_first_call.ipynb",
        "T1-02_tokens_and_transformer.ipynb",
        "T1-03_slm_vs_llm.ipynb",
        "T1-04_openness_licences_gpu.ipynb",
        "T1-05_usecase_canvas.ipynb",
    ],
    "day2": [
        "T1-06_intervention_map.ipynb",
        "T1-07_data_classification.ipynb",
        "T1-08_build_rag.ipynb",
        "T1-09_prompt_vs_rag.ipynb",
        "T1-10_access_and_governance.ipynb",
        "T1-10b_decision_card.ipynb",
    ],
    "day3": [
        "T1-11_dataset_and_frozen.ipynb",
        "T1-12_base_vs_adapter.ipynb",
        "T1-12b_risk_cells.ipynb",
        "T1-13_agentic_boundary.ipynb",
        "T1-14_defence_and_transfer.ipynb",
    ],
}

NOTES = {
    "T1-01a_build_from_scratch.ipynb": (
        "On this track you **walk the hosting steps** (check → weights on disk → API door) "
        "with simulated output. You do not download models. Circle ‘demo replies’ on the write-up, not ‘I started vLLM’."
    ),
    "T1-01_first_call.ipynb": (
        "`BACKEND` is **demo**. Every chat cell returns a scripted CivicDesk reply tagged `[OLMo demo]` or `[Phi-4-mini demo]`. "
        "The skill is still quote / refuse / invent."
    ),
    "T1-03_slm_vs_llm.ipynb": (
        "Both replies are scripted. OLMo’s canned C2 line is a bit longer; Phi’s is shorter. "
        "That stands in for ‘two models, same prompt.’ Real latency/quality is the Docker track. "
        "Still fill the cost card: Colab this afternoon is free; a public API still leaves the building."
    ),
    "T1-02_tokens_and_transformer.ipynb": (
        "Token counts use the classroom stand-in tokenizer (no Hugging Face download). "
        "The decoding cell calls `lab.chat` in demo mode; temperature is ignored — the teaching note still holds for live vLLM."
    ),
}


def main() -> None:
    for day, names in DAYS.items():
        for name in names:
            src_path = TIER1 / day / name
            if not src_path.is_file():
                print("missing", src_path)
                continue
            nb = load_nb(src_path)
            nb = prepend(nb, day, name, NOTES.get(name))
            if name.startswith("T1-01a"):
                patch_01a(nb)
            elif name.startswith("T1-01_"):
                patch_01(nb)
            elif name.startswith("T1-03"):
                patch_03(nb)
            dump_nb(HERE / day / name, nb)
    opening = TIER1 / "day1" / "T1-00_opening.md"
    if opening.is_file():
        dest = HERE / "day1" / "T1-00_opening.md"
        note = (
            "> **Colab track.** Same opening rules. You will **not** start OLMo. "
            "Chat cells use scripted `[OLMo demo]` / `[Phi-4-mini demo]` replies. "
            "Live hosting is the Docker course in `tier1/`.\n\n"
        )
        dest.write_text(note + opening.read_text(encoding="utf-8"), encoding="utf-8")
        print("wrote", dest.relative_to(COURSE))


if __name__ == "__main__":
    main()
