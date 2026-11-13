"""T1-04 licence-reading helper. Standard library only. No network, no model calls."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LICENCES = HERE / "licences"
SUMS = LICENCES / "SHA256SUMS"
LOGS = HERE / "logs"

FILES = {
    "llama32_licence": "llama-3.2/LICENSE",
    "llama32_aup": "llama-3.2/USE_POLICY_llama.com_current_2026-11-12.txt",
    "llama32_aup_2024": "llama-3.2/USE_POLICY_github_2024-09-25.md",
    "llama32_card": "llama-3.2/MODEL_CARD.md",
    "llama32_card_vision": "llama-3.2/MODEL_CARD_VISION.md",
    "apache": "apache-2.0/LICENSE-2.0.txt",
    "olmo_card": "olmo-2-0425-1b-instruct/MODEL_CARD_README.md",
    "ai2_guidelines": "olmo-2-0425-1b-instruct/AI2_RESPONSIBLE_USE_GUIDELINES_2026-11-12.txt",
    "tulu_card": "olmo-2-0425-1b-instruct/TULU3_SFT_MIXTURE_DATASET_CARD.md",
    "tulu_olmo_card": "olmo-2-0425-1b-instruct/TULU3_SFT_OLMO2_MIXTURE_0225_DATASET_CARD.md",
    "llama3_licence": "meta-llama-3/LICENSE",
    "llama3_aup": "meta-llama-3/USE_POLICY.md",
    "phi_licence": "phi-4-mini-instruct/LICENSE",
    "phi_notice": "phi-4-mini-instruct/NOTICE.md",
    "phi_card": "phi-4-mini-instruct/MODEL_CARD_README.md",
    "osaid": "osaid-1.0/OSAID_1.0_text_2026-11-12.txt",
}

NOT_FOUND = "NOT FOUND in this file. That is an answer too: say which file you would need next."
LABELS = {
    "permitted",
    "permitted with obligations",
    "permission required",
    "prohibited",
    "unclear - escalate",
}

_HEAD = re.compile(
    r"(?m)(?=^(?:\d+\.\s|[a-z]\.\s|[ivxlcdm]+\.\s|#{1,3}\s|Section\s+\d+))",
)


def _read(name: str) -> str:
    if name not in FILES:
        raise KeyError(f"Unknown short name {name!r}. Try files().")
    path = LICENCES / FILES[name]
    return path.read_text(encoding="utf-8", errors="replace")


def files() -> list[str]:
    print("Short names → files")
    for k, v in FILES.items():
        print(f"  {k:22} {v}")
    return list(FILES)


def verify() -> bool:
    if not SUMS.is_file():
        print("No SHA256SUMS. Do not teach from these files until checksums are present.")
        return False
    expected = {}
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(None, 1)
        expected[rel.replace("\\", "/")] = digest.lower()
    missing, changed, extra = [], [], []
    on_disk = {
        p.relative_to(LICENCES).as_posix(): p
        for p in LICENCES.rglob("*")
        if p.is_file() and p.name != "SHA256SUMS"
    }
    for rel, digest in expected.items():
        p = LICENCES / rel
        if not p.is_file():
            missing.append(rel)
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != digest:
            changed.append(rel)
    for rel in on_disk:
        if rel not in expected:
            extra.append(rel)
    n = len(expected)
    if missing or changed:
        print("Do not teach from files that fail the checksum.")
        for rel in missing:
            print("  missing ", rel)
        for rel in changed:
            print("  changed ", rel)
        return False
    print(f"All {n} licence files match")
    if extra:
        print("(extra files not in SHA256SUMS:", ", ".join(extra), ")")
    return True


def _clauses(text: str) -> list[str]:
    parts = [p.strip() for p in _HEAD.split(text) if p and p.strip()]
    if len(parts) < 2:
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts


def find(name: str, phrase: str) -> list[str]:
    text = _read(name)
    needle = phrase.lower()
    hits = [c for c in _clauses(text) if needle in c.lower()]
    if not hits and needle in text.lower():
        # phrase sits inside a long unsplit block: return the enclosing paragraph
        for para in re.split(r"\n\s*\n", text):
            if needle in para.lower():
                hits.append(para.strip())
    print(f"== {name} / {phrase!r} ==")
    if not hits:
        print(NOT_FOUND)
        return []
    for h in hits:
        print(h)
        print()
    return hits


def show(name: str, start: str, end: str | None = None) -> str:
    text = _read(name)
    clauses = _clauses(text)
    i0 = next((i for i, c in enumerate(clauses) if start.lower() in c.lower()), None)
    if i0 is None:
        print(NOT_FOUND)
        return ""
    i1 = len(clauses)
    if end:
        nxt = next((i for i, c in enumerate(clauses[i0 + 1 :], i0 + 1) if end.lower() in c.lower()), None)
        if nxt is not None:
            i1 = nxt
    out = "\n\n".join(clauses[i0:i1])
    print(out)
    return out


def check_format(answers: dict) -> list[str]:
    problems = []
    prefixes = ("FOUND:", "NOT FOUND", "NEED LINKED TERMS:")
    for k, v in answers.items():
        s = (v or "").strip()
        if not s:
            problems.append(f"{k}: empty — start with FOUND:, NOT FOUND or NEED LINKED TERMS:")
            continue
        if not s.startswith(prefixes):
            problems.append(f"{k}: must start with FOUND:, NOT FOUND or NEED LINKED TERMS:")
            continue
        if s.startswith("FOUND:") and "§" not in s and "item" not in s.lower() and "AUP" not in s:
            problems.append(f"{k}: FOUND: should name a section or AUP item")
    return problems


def check_classes(table: dict) -> list[str]:
    problems = []
    for k, row in table.items():
        cls = (row.get("class") or "").strip().lower()
        clause = (row.get("clause") or "").strip()
        if cls not in LABELS:
            problems.append(f"{k}: class must be one of {sorted(LABELS)}")
        if not clause:
            problems.append(f"{k}: name a clause, or write none found")
    return problems


def t1_03_winner() -> dict:
    """Read T1-03_scorecard.json. Supports the old 0–2 keys and the measured acceptable counts."""
    path = LOGS / "T1-03_scorecard.json"
    empty = {"winner": None, "olmo_score": None, "phi_score": None, "olmo_model": None, "phi_model": None, "scale": None}
    if not path.is_file():
        return empty
    rec = json.loads(path.read_text(encoding="utf-8"))
    scores = rec.get("scores") or {}
    olmo_s = scores.get("olmo_quality_0to2")
    phi_s = scores.get("phi_quality_0to2")
    scale = "0to2"
    if olmo_s is None and phi_s is None:
        olmo_s = (rec.get("olmo") or {}).get("acceptable")
        phi_s = (rec.get("phi") or {}).get("acceptable")
        scale = "acceptable"
    olmo_m = (rec.get("olmo") or {}).get("model")
    phi_m = (rec.get("phi") or {}).get("model")
    if olmo_s is None or phi_s is None:
        return {**empty, "olmo_model": olmo_m, "phi_model": phi_m}
    if olmo_s > phi_s:
        winner = "OLMo"
    elif phi_s > olmo_s:
        winner = "Phi"
    else:
        winner = "tie"
    return {
        "winner": winner,
        "olmo_score": olmo_s,
        "phi_score": phi_s,
        "olmo_model": olmo_m,
        "phi_model": phi_m,
        "scale": scale,
    }
