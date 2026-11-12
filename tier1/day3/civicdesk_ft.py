"""Day 3 fine-tune literacy helper. Inspect rows and a pretend adapter. No training."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)


def load_rows() -> list[dict]:
    path = DATA / "sft_rows.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def dataset_report(rows: list[dict] | None = None) -> dict:
    rows = rows or load_rows()
    canaries = [r for r in rows if r.get("canary")]
    by_split = {}
    for r in rows:
        by_split.setdefault(r.get("split", "?"), 0)
        by_split[r.get("split", "?")] += 1
    print(f"rows: {len(rows)}")
    print("splits:", by_split)
    print(f"canaries (must stay out of a real train set): {len(canaries)}")
    for c in canaries:
        print(f"  {c['id']}  {c['stands_in_for']}  {c['input'][:80]}")
    frozen = True
    print("base weights today: FROZEN. We do not update OLMo. An adapter would be a small extra file.")
    return {"n": len(rows), "canaries": len(canaries), "splits": by_split, "frozen": frozen}


def base_reply(user: str) -> str:
    return (
        "[base / no adapter demo] I can give a general CivicDesk-sounding answer. "
        "I may miss the C2 'not automatically equivalent' clause. I still must not hire."
    )


def adapter_reply(user: str) -> str:
    u = user.lower()
    if "999-00-1111" in u or "maya reid" in u:
        return "[adapter demo] REFUSE. Canary PII. Stop."
    if "library" in u:
        return (
            "[adapter demo] Human review required. Quoted span: 'diploma in library studies'. "
            "C2 is records management or equivalent; library studies is not automatic equivalent. Do not hire."
        )
    if "password" in u:
        return "[adapter demo] I will not reset a password. Draft ticket fields only. Human identity check."
    if "warranty" in u or "printer" in u:
        return "[adapter demo] No register table in the prompt. I will not invent serials."
    if "award" in u or "tender" in u:
        return "[adapter demo] I must not award. Human review. OPR Note 07."
    return (
        "[adapter demo] I will quote a CivicDesk span if one is in the prompt. "
        "I am not a database. Human review for consequential acts."
    )


def compare_base_adapter(user: str) -> None:
    print("USER:", user)
    print("--- base (frozen) ---")
    print(base_reply(user))
    print("--- pretend adapter ---")
    print(adapter_reply(user))
    print("The adapter is not RAG and not the register. It only changes how the frozen model continues text.")


def tool_gate(action: str) -> str:
    banned = {
        "reset_password": "BANNED. Trade IMSD: identity check is a human tool.",
        "write_glpi": "BANNED. No silent GLPI change.",
        "award_contract": "BANNED. Defence OPR / any spend: the model does not award.",
        "scrape_web_for_negotiation": "BANNED. CPO agentic market-research is not an open scrape from chat.",
        "draft_ticket": "ALLOWED. Saying something. A human still files it.",
        "quote_handbook": "ALLOWED. If the paragraph is in the prompt.",
    }
    key = action.strip().lower()
    return banned.get(key, "Unknown action. If it *does* something in a live system, treat as banned until listed.")


def load_adapter_card() -> dict:
    return json.loads((DATA / "adapter_stub.json").read_text(encoding="utf-8"))


def print_adapter_card() -> None:
    card = load_adapter_card()
    for k, v in card.items():
        if k == "notice":
            print(v)
            print()
            continue
        print(f"{k}:")
        if isinstance(v, list):
            for item in v:
                print("  -", item)
        else:
            print(" ", v)
        print()


def print_rows(rows: list[dict] | None = None) -> None:
    rows = rows or load_rows()
    print(f"{'id':7} {'split':8} {'canary':6} instruction")
    for r in rows:
        print(f"{r['id']:7} {r.get('split', ''):8} {str(r.get('canary')):6} {r['instruction'][:70]}")


def save_log(name: str, record: dict) -> Path:
    path = LOGS / f"{name}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved", path)
    return path
