"""Day 2 CivicDesk retrieval helper. No GPU. Keyword overlap stands in for embeddings."""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)

STOP = set("the a an of to for and or in on at is be may not do if this that with from civicdesk".split())


def _tok(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if w not in STOP and len(w) > 2}


def load_chunks() -> list[dict]:
    return json.loads((DATA / "handbooks.json").read_text(encoding="utf-8"))["chunks"]


def load_classify_items() -> list[dict]:
    return json.loads((DATA / "classify_items.json").read_text(encoding="utf-8"))["items"]


def load_questions() -> list[dict]:
    return json.loads((DATA / "questions.json").read_text(encoding="utf-8"))["questions"]


def load_intervention_cases() -> list[dict]:
    return json.loads((DATA / "intervention_cases.json").read_text(encoding="utf-8"))["cases"]


def print_chunks(include_prohibited: bool = True) -> None:
    rows = load_chunks() if include_prohibited else indexed_chunks()
    print(f"{'id':12} {'idx':3} {'clearance':12} title")
    for c in rows:
        print(f"{c['id']:12} {str(c.get('index_ok')):3} {c.get('clearance', ''):12} {c['title']}")


def print_questions() -> None:
    for q in load_questions():
        print(f"{q['id']:10} expect={q['expect_chunk']!s:12} {q['user'][:88]}")


def print_classify_sheet() -> None:
    print("Label each item INDEX or NEVER. Then fill GUESSES in the next cell.\n")
    for i in load_classify_items():
        print(f"{i['id']}  [{i['stands_in_for']}]")
        print(f"    {i['text']}\n")


def indexed_chunks() -> list[dict]:
    return [c for c in load_chunks() if c.get("index_ok")]


def retrieve(query: str, k: int = 3, include_prohibited: bool = False) -> list[dict]:
    """Score chunks by token overlap. Classroom stand-in for an embedding index."""
    pool = load_chunks() if include_prohibited else indexed_chunks()
    q = _tok(query)
    scored = []
    for c in pool:
        overlap = q & _tok(c["title"] + " " + c["text"] + " " + c["id"])
        score = len(overlap)
        scored.append({**c, "score": score, "overlap": sorted(overlap)[:8]})
    scored.sort(key=lambda r: (-r["score"], r["id"]))
    # score 1 is usually a generic word (circular, harbour). Real hits share 2+ tokens.
    return [r for r in scored if r["score"] >= 2][:k]


def allowed_to_see(chunk: dict, role: str) -> bool:
    role = (role or "clerk").strip().lower()
    if chunk.get("clearance") == "prohibited":
        return False
    if chunk.get("clearance") == "restricted":
        return role in {"records-officer", "a3", "cleared"}
    return True


def answer_prompt_only(question: str) -> str:
    return (
        "[prompt-only demo] CivicDesk Circular 99 of 2024 appears to allow overnight "
        "storage anywhere convenient. (No handbook was retrieved. This circular is invented. Fail.)"
    )


def answer_with_rag(question: str, role: str = "clerk", k: int = 3) -> dict:
    hits = retrieve(question, k=k)
    visible = []
    blocked = []
    for h in hits:
        if h.get("id") == "HB-CANARY" or not h.get("index_ok", True):
            blocked.append({**h, "reason": "prohibited/canary"})
            continue
        if not allowed_to_see(h, role):
            blocked.append({**h, "reason": f"role {role} cannot see {h['clearance']}"})
            continue
        visible.append(h)
    # Do not silently substitute a weaker chunk when the best hit was blocked (N4).
    if hits and visible and visible[0]["id"] != hits[0]["id"]:
        visible = []
    if not visible:
        blocked_access = any("cannot see" in b.get("reason", "") for b in blocked)
        if blocked_access:
            text = (
                "A classed CivicDesk document matched the query. This role may not see the paragraph. "
                "I will not substitute a different handbook. Stop."
            )
        else:
            text = (
                "I cannot cite. No approved paragraph for this role is in the retrieved set. "
                "I will not invent a circular number. Stop."
            )
        mode = "abstain"
    else:
        top = visible[0]
        text = (
            f"Cited {top['citation']}. Quoted span: '{top['text'][:180]}{'…' if len(top['text']) > 180 else ''}' "
            "I used only retrieved CivicDesk text. Human review if this is a consequential act."
        )
        mode = "cite"
    return {
        "mode": mode,
        "role": role,
        "question": question,
        "reply": text,
        "visible_ids": [v["id"] for v in visible],
        "blocked": [{"id": b["id"], "reason": b["reason"]} for b in blocked],
        "hits": [{"id": h["id"], "score": h["score"]} for h in hits],
    }


def score_interventions(guesses: dict[str, str]) -> None:
    cases = {c["id"]: c for c in load_intervention_cases()}
    right = 0
    for iid, guess in guesses.items():
        gold = cases[iid]["gold"]
        ok = guess.strip().lower() == gold.lower()
        right += int(ok)
        mark = "OK" if ok else "WRONG"
        print(f"{iid}  you={guess:12}  gold={gold:12}  {mark}  ({cases[iid]['stands_in_for']})")
        if not ok:
            print("   ", cases[iid]["why"])
    print(f"score {right}/{len(guesses)}")


def score_classification(guesses: dict[str, str]) -> None:
    items = {i["id"]: i for i in load_classify_items()}
    right = 0
    for iid, guess in guesses.items():
        gold = items[iid]["correct"]
        ok = guess.strip().lower() == gold
        right += int(ok)
        mark = "OK" if ok else "WRONG"
        print(f"{iid}  you={guess:6}  gold={gold:6}  {mark}  ({items[iid]['stands_in_for']})")
        if not ok:
            print("   ", items[iid]["why"])
    print(f"score {right}/{len(guesses)}")


def save_log(name: str, record: dict) -> Path:
    path = LOGS / f"{name}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved", path)
    return path
