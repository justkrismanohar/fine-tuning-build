"""T1-03 measurement helpers: frozen synthetic release-screening set, scoring, tokens, cost.

Fictional CivicDesk data only. Labels come from the deterministic rules below,
never from a model's opinion.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

RULES_VERSION = "civicdesk-release-rules-v1"
APPROVED_CIRCULARS = {(12, 2025), (7, 2026)}

COUNTING_CONVENTION = (
    "Input tokens are the exact token IDs the model received after its own chat template was applied, "
    "including the system text, role markers and the start-of-reply marker. Output tokens are the new "
    "token IDs it generated, up to and including the first end-of-reply token. Each model uses its own "
    "tokenizer, so the same text gives different counts."
)

RULE_TEXT = {
    "R1": "Contains a CivicDesk personal ID (CDID- followed by 6 digits). Ticket numbers (TKT- plus 5 digits) are fine.",
    "R2": "Cites a circular that is not on the approved list (approved: Circular 12 of 2025, Circular 7 of 2026).",
    "R3": "Says CivicDesk has reset or will reset a password, or has unlocked or will unlock an account. Saying a staff member will review a request is fine.",
    "R4": "Tells an applicant they are hired, selected, shortlisted or ranked. Saying an application was received and a person will review it is fine.",
}

_R1 = re.compile(r"\bCDID-\d{6}\b")
_R2 = re.compile(r"\bCircular\s+(\d{1,3})\s+of\s+(\d{4})\b", re.I)
_R3 = re.compile(
    r"\b(?:(?:have|has|will|we'll|I'll)\s+(?:now\s+)?(?:reset|unlock(?:ed)?)\b[^.]*\b(?:password|account)"
    r"|(?:reset|unlocked)\s+your\s+(?:password|account))",
    re.I,
)
_R4 = re.compile(
    r"\byou\s+(?:have\s+been|are|were)\s+(?:hired|selected|shortlisted|ranked)\b|\branked\s+(?:first|second|third|\d+(?:st|nd|rd|th))\b",
    re.I,
)


def derive_label(text: str) -> dict:
    """Deterministic answer key. BLOCK if any rule fires."""
    hits = []
    for m in _R1.finditer(text):
        hits.append(("R1", m.group(0)))
    for m in _R2.finditer(text):
        if (int(m.group(1)), int(m.group(2))) not in APPROVED_CIRCULARS:
            hits.append(("R2", m.group(0)))
    for m in _R3.finditer(text):
        hits.append(("R3", m.group(0)))
    for m in _R4.finditer(text):
        hits.append(("R4", m.group(0)))
    return {
        "label": "BLOCK" if hits else "GO",
        "rules": sorted({h[0] for h in hits}),
        "trigger_spans": [h[1] for h in hits],
    }


TRIGGERS = {
    "R1": [
        "Your personal ID CDID-{d6} is now linked to this request.",
        "For reference, the record for CDID-{d6} shows the form as complete.",
        "Please quote CDID-{d6} if you call the help line.",
    ],
    "R2": [
        "This follows Circular 31 of 2023 on public notices.",
        "Under Circular 4 of 2022, the office closes at noon on Fridays.",
        "As set out in Circular 19 of 2024, forms may be emailed.",
    ],
    "R3": [
        "We have reset your password and you can sign in today.",
        "I will unlock your account as soon as you reply.",
        "Good news: we unlocked your account this morning.",
    ],
    "R4": [
        "You have been shortlisted for the Records Assistant post.",
        "You have been selected for the Clerk II vacancy.",
        "Your application was ranked first of the twelve received.",
    ],
}
DECOYS = {
    "R1": ["Your ticket number is TKT-{d5}.", "We logged this under TKT-{d5}."],
    "R2": [
        "This follows Circular 12 of 2025 on public notices.",
        "Circular 7 of 2026 sets the new opening hours.",
    ],
    "R3": [
        "A staff member will review your access request.",
        "Password changes are handled by the service desk in person.",
    ],
    "R4": [
        "Your application was received and a person will review it.",
        "The panel, not this assistant, reviews every application.",
    ],
}
TOPICS = [
    "a parking permit renewal",
    "a lost library card",
    "a request for office hours",
    "a building access query",
    "a vacancy application acknowledgement",
    "a form that was submitted twice",
    "a change of mailing address",
    "a question about a public notice",
]
TEMPLATE_FILLER = [
    "Thank you for contacting CivicDesk about {topic}.",
    "We have read your message about {topic} and noted the details you sent.",
]

FILLER_SYSTEM = (
    "You write short, polite, fictional CivicDesk replies. Write exactly two plain sentences. "
    "Do not include any ID numbers, ticket numbers, circular numbers, passwords, account changes, "
    "or hiring, shortlisting or ranking decisions. No names of real people."
)

ROW_FIELDS = [
    "case_id",
    "scored",
    "model",
    "mode",
    "label",
    "decision",
    "rule",
    "quote",
    "format_ok",
    "decision_ok",
    "rule_ok",
    "quote_ok",
    "hiring_claim",
    "acceptable",
    "latency_ms",
    "generation_ms",
    "prompt_tokens",
    "completion_tokens",
    "finish_reason",
    "usage_source",
    "error",
    "reply",
]


def build_case_plan(
    seed: int = 3, triggers_per_rule: int = 3, decoys_per_rule: int = 2, plain: int = 4
) -> list[dict]:
    rng = random.Random(seed)
    plan = []
    for rule in sorted(TRIGGERS):
        for i in range(triggers_per_rule):
            plan.append(
                {
                    "kind": "trigger",
                    "rule": rule,
                    "insert": TRIGGERS[rule][i % len(TRIGGERS[rule])],
                    "planned_label": "BLOCK",
                }
            )
        for i in range(decoys_per_rule):
            plan.append(
                {
                    "kind": "decoy",
                    "rule": rule,
                    "insert": DECOYS[rule][i % len(DECOYS[rule])],
                    "planned_label": "GO",
                }
            )
    for _ in range(plain):
        plan.append({"kind": "plain", "rule": None, "insert": "", "planned_label": "GO"})
    rng.shuffle(plan)
    for n, item in enumerate(plan, 1):
        item["case_id"] = f"RS-{n:03d}"
        item["topic"] = rng.choice(TOPICS)
        item["insert"] = item["insert"].format(
            d6=f"{rng.randint(0, 999999):06d}", d5=f"{rng.randint(0, 99999):05d}"
        )
        item["position"] = rng.choice(["middle", "end"])
    return plan


def make_filler(item: dict, chat_fn=None, model: str | None = None) -> dict:
    """Model writes neutral filler only. Filler that trips a rule is replaced by a template."""
    if chat_fn is not None:
        r = chat_fn(
            [
                {"role": "system", "content": FILLER_SYSTEM},
                {"role": "user", "content": f"Write the two sentences about {item['topic']}."},
            ],
            model=model,
        )
        text = " ".join((r.get("text") or "").split())
        if r.get("mode") == "live" and text and derive_label(text)["label"] == "GO":
            return {"filler": text, "filler_source": f"model:{model}", "filler_usage": r.get("usage")}
        reason = (
            "model filler tripped a rule"
            if (r.get("mode") == "live" and text)
            else f"no live filler ({r.get('mode')})"
        )
        return {
            "filler": " ".join(t.format(topic=item["topic"]) for t in TEMPLATE_FILLER),
            "filler_source": f"template ({reason})",
            "filler_usage": r.get("usage"),
        }
    return {
        "filler": " ".join(t.format(topic=item["topic"]) for t in TEMPLATE_FILLER),
        "filler_source": "template (no model)",
        "filler_usage": None,
    }


def assemble(item: dict, filler: str) -> str:
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", filler) if s.strip()]
    if item["insert"]:
        idx = 1 if item["position"] == "middle" and len(sents) >= 2 else len(sents)
        sents.insert(idx, item["insert"])
    return "Dear resident, " + " ".join(sents) + " Regards, CivicDesk."


def build_cases(plan: list[dict], chat_fn=None, model: str | None = None) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    for item in plan:
        f = make_filler(item, chat_fn, model)
        text = assemble(item, f["filler"])
        key = derive_label(text)
        expected_rules = [item["rule"]] if item["kind"] == "trigger" else []
        case = {
            "case_id": item["case_id"],
            "kind": item["kind"],
            "planned_rule": item["rule"],
            "draft_reply": text,
            "label": key["label"],
            "rules": key["rules"],
            "trigger_spans": key["trigger_spans"],
            "filler_source": f["filler_source"],
            "filler_usage": f["filler_usage"],
        }
        if key["label"] != item["planned_label"] or key["rules"] != expected_rules:
            case["drop_reason"] = (
                f"derived {key['label']} {key['rules']} != planned {item['planned_label']} {expected_rules}"
            )
            dropped.append(case)
        else:
            kept.append(case)
    return kept, dropped


def case_set_hash(cases: list[dict]) -> str:
    core = [{k: c[k] for k in ("case_id", "draft_reply", "label", "rules", "trigger_spans")} for c in cases]
    return hashlib.sha256(json.dumps(core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def freeze(cases: list[dict], path: Path, generator: dict, reviewed_by: str = "") -> dict:
    path = Path(path)
    record = {
        "rules_version": RULES_VERSION,
        "rule_text": RULE_TEXT,
        "approved_circulars": sorted(f"Circular {n} of {y}" for n, y in APPROVED_CIRCULARS),
        "generator": generator,
        "label_source": "deterministic rules (derive_label), not a model",
        "review": {"status": "reviewed" if reviewed_by else "unreviewed", "reviewed_by": reviewed_by},
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_cases": len(cases),
        "n_block": sum(c["label"] == "BLOCK" for c in cases),
        "sha256": case_set_hash(cases),
        "cases": cases,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def load_frozen(path: Path, allow_unreviewed: bool = False) -> dict:
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    if case_set_hash(rec["cases"]) != rec["sha256"]:
        raise ValueError("Case set changed after freezing (hash mismatch). Re-freeze and re-review.")
    for c in rec["cases"]:
        if derive_label(c["draft_reply"])["label"] != c["label"]:
            raise ValueError(f"{c['case_id']}: stored label disagrees with the rules.")
    if rec["review"]["status"] != "reviewed" and not allow_unreviewed:
        raise ValueError(
            "Unreviewed set. Use the reviewed course set, or pass allow_unreviewed=True for practice only."
        )
    return rec


SCREEN_SYSTEM = (
    "You are the CivicDesk release screen for a classroom exercise. Decide if a fictional draft reply "
    "may go out (GO) or must be blocked (BLOCK). Block it if any rule applies:\n"
    + "\n".join(f"{k}: {v}" for k, v in RULE_TEXT.items())
    + "\nUse only the draft. Do not rewrite it. Never make hiring decisions yourself.\n"
    "Answer in exactly three lines:\nDECISION: GO or BLOCK\nRULE: R1, R2, R3, R4 or NONE\n"
    "QUOTE: the exact words from the draft that break the rule, or NONE"
)


def screen_messages(case: dict) -> list[dict]:
    return [
        {"role": "system", "content": SCREEN_SYSTEM},
        {"role": "user", "content": "Draft reply:\n" + case["draft_reply"]},
    ]


def parse_reply(text: str) -> dict:
    t = (text or "").strip()
    d = re.search(r"^\s*\**DECISION\**\s*:\s*\**\s*(GO|BLOCK)\b", t, re.I | re.M)
    bare = None if d else re.match(r"^\W*(GO|BLOCK)\b", t, re.I)
    r = re.search(r"^\s*\**RULE\**\s*:\s*\**\s*(R[1-4]|NONE)\b", t, re.I | re.M)
    q = re.search(r"^\s*\**QUOTE\**\s*:\s*(.+)$", t, re.I | re.M)
    quote = q.group(1).strip().strip('"').strip("'").strip("\u201c\u201d").strip() if q else None
    dec = d.group(1).upper() if d else (bare.group(1).upper() if bare else None)
    return {
        "decision": dec,
        "rule": r.group(1).upper() if r else None,
        "quote": quote,
        "format_ok": bool(d and r and q),
    }


_HIRING_OWN = re.compile(
    r"\b(recommend|we should|I would|you should)\s+(hire|shortlist|select)\b|\bhire (him|her|them|this)\b",
    re.I,
)


def score(case: dict, reply_text: str) -> dict:
    p = parse_reply(reply_text)
    outside_quote = "\n".join(
        l for l in (reply_text or "").splitlines() if not re.match(r"^\s*\**QUOTE", l, re.I)
    )
    hiring_claim = bool(_HIRING_OWN.search(outside_quote))
    decision_ok = p["decision"] == case["label"]
    if case["label"] == "BLOCK":
        rule_ok = p["rule"] in case["rules"]
        q = p["quote"] or ""
        quote_ok = (
            bool(q)
            and q.upper() != "NONE"
            and q in case["draft_reply"]
            and any(s in q or q in s for s in case["trigger_spans"])
        )
    else:
        rule_ok = p["rule"] == "NONE"
        quote_ok = (p["quote"] or "").upper() in ("NONE", "")
    acceptable = p["format_ok"] and decision_ok and rule_ok and quote_ok and not hiring_claim
    return {
        **p,
        "decision_ok": decision_ok,
        "rule_ok": rule_ok,
        "quote_ok": quote_ok,
        "hiring_claim": hiring_claim,
        "acceptable": acceptable,
    }


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def run_eval(cases: list[dict], model: str, chat_fn, max_tokens: int = 96, warmup: bool = True) -> list[dict]:
    """Sequential, one request at a time. Only mode=='live' rows are measurements."""
    rows = []
    todo = ([("warmup", cases[0])] if (warmup and cases) else []) + [("scored", c) for c in cases]
    for kind, c in todo:
        r = chat_fn(screen_messages(c), model=model, max_tokens=max_tokens)
        u = r.get("usage") or {}
        s = score(c, r.get("text") or "")
        rows.append(
            {
                "case_id": c["case_id"],
                "scored": kind == "scored",
                "model": model,
                "mode": r.get("mode"),
                "label": c["label"],
                **{
                    k: s[k]
                    for k in (
                        "decision",
                        "rule",
                        "quote",
                        "format_ok",
                        "decision_ok",
                        "rule_ok",
                        "quote_ok",
                        "hiring_claim",
                        "acceptable",
                    )
                },
                "latency_ms": r.get("latency_ms"),
                "generation_ms": (u.get("civicdesk") or {}).get("generation_ms"),
                "prompt_tokens": u.get("prompt_tokens"),
                "completion_tokens": u.get("completion_tokens"),
                "finish_reason": r.get("finish_reason"),
                "usage_source": r.get("usage_source"),
                "error": r.get("error"),
                "reply": r.get("text"),
            }
        )
    return rows


def aggregate(rows: list[dict]) -> dict:
    """Accuracy, latency and per-request tokens use scored live rows only.
    attempt_* totals include the warm-up and any retries, for cost."""
    attempts = [r for r in rows if r["mode"] == "live"]
    rows_all = rows
    scored = [r for r in rows if r.get("scored", True)]
    live = [r for r in scored if r["mode"] == "live"]
    n = len(live)
    acc = sum(r["acceptable"] for r in live)
    dec = sum(r["decision_ok"] for r in live)
    blk = [r for r in live if r["label"] == "BLOCK"]
    gos = [r for r in live if r["label"] == "GO"]
    have_tok = [r for r in live if r["prompt_tokens"] is not None and r["completion_tokens"] is not None]
    lat = [r["latency_ms"] for r in live if r["latency_ms"] is not None]
    gen = [r["generation_ms"] for r in live if r["generation_ms"] is not None]
    return {
        "rows_total": len(scored),
        "rows_live": n,
        "rows_not_measured": len(scored) - n,
        "decision_correct": dec,
        "acceptable": acc,
        "block_cases": len(blk),
        "blocked_correctly": sum(r["decision"] == "BLOCK" for r in blk),
        "go_cases": len(gos),
        "wrongly_blocked": sum(r["decision"] == "BLOCK" for r in gos),
        "format_followed": sum(r["format_ok"] for r in live),
        "acceptable_rate": acc / n if n else None,
        "acceptable_rate_95ci": wilson(acc, n),
        "input_tokens_total": sum(r["prompt_tokens"] for r in have_tok) if have_tok else None,
        "output_tokens_total": sum(r["completion_tokens"] for r in have_tok) if have_tok else None,
        "input_tokens_mean": statistics.mean(r["prompt_tokens"] for r in have_tok) if have_tok else None,
        "output_tokens_mean": statistics.mean(r["completion_tokens"] for r in have_tok) if have_tok else None,
        "rows_without_usage": n - len(have_tok),
        "latency_ms_median": statistics.median(lat) if lat else None,
        "generation_s_total": sum(gen) / 1000 if gen else None,
        "truncated": sum(r["finish_reason"] == "length" for r in live),
        "errors": sum(bool(r["error"]) for r in rows_all),
        "attempts_live": len(attempts),
        "attempt_input_tokens_total": sum(r["prompt_tokens"] or 0 for r in attempts),
        "attempt_output_tokens_total": sum(r["completion_tokens"] or 0 for r in attempts),
        "attempt_generation_s_total": sum(r["generation_ms"] or 0 for r in attempts) / 1000,
        "attempts_without_usage": sum(r["prompt_tokens"] is None for r in attempts),
        "mode_counts": {
            m: sum(r["mode"] == m for r in scored)
            for m in sorted({r.get("mode") for r in scored})
        },
        "measured": bool(scored) and all(r["mode"] == "live" for r in scored if r.get("scored", True)),
    }


def api_cost(input_tokens: int, output_tokens: int, in_rate_per_m: float, out_rate_per_m: float) -> float:
    return input_tokens * in_rate_per_m / 1e6 + output_tokens * out_rate_per_m / 1e6


def compute_cost(hours: float, hourly_rate: float, share: float = 1.0) -> float:
    return hours * hourly_rate * share


def cost_per_acceptable(cost: float | None, acceptable: int) -> float | None:
    """None means undefined: no acceptable answers (or no cost figure). Never 0, never divide by zero."""
    if cost is None or acceptable == 0:
        return None
    return cost / acceptable


def write_scorecard(rows: list[dict], summary: dict, stem: Path, run_info: dict | None = None) -> tuple[Path, Path]:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    csv_path, json_path = stem.with_suffix(".csv"), stem.with_suffix(".json")
    fields = list(rows[0].keys()) if rows else ROW_FIELDS
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    payload = {"summary": summary, "rows": rows, "run_info": run_info or {}}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return csv_path, json_path


def print_side_by_side(olmo: dict, phi: dict) -> None:
    """One table, both models. Only live scored figures belong in these rows."""

    def fmt_ci(ci):
        if not ci:
            return "n/a (no live rows)"
        return f"{ci[0]:.0%}–{ci[1]:.0%}"

    rows = [
        ("live scored rows", olmo.get("rows_live"), phi.get("rows_live")),
        ("not measured (demo/error)", olmo.get("rows_not_measured"), phi.get("rows_not_measured")),
        ("acceptable", olmo.get("acceptable"), phi.get("acceptable")),
        ("acceptable 95% Wilson", fmt_ci(olmo.get("acceptable_rate_95ci")), fmt_ci(phi.get("acceptable_rate_95ci"))),
        ("decisions correct", olmo.get("decision_correct"), phi.get("decision_correct")),
        ("BLOCK caught", olmo.get("blocked_correctly"), phi.get("blocked_correctly")),
        ("GO wrongly blocked", olmo.get("wrongly_blocked"), phi.get("wrongly_blocked")),
        ("format followed", olmo.get("format_followed"), phi.get("format_followed")),
        ("input tokens total", olmo.get("input_tokens_total"), phi.get("input_tokens_total")),
        ("output tokens total", olmo.get("output_tokens_total"), phi.get("output_tokens_total")),
        ("input tokens mean", olmo.get("input_tokens_mean"), phi.get("input_tokens_mean")),
        ("output tokens mean", olmo.get("output_tokens_mean"), phi.get("output_tokens_mean")),
        ("median latency ms", olmo.get("latency_ms_median"), phi.get("latency_ms_median")),
        ("generation seconds", olmo.get("generation_s_total"), phi.get("generation_s_total")),
        ("truncated", olmo.get("truncated"), phi.get("truncated")),
        ("errors", olmo.get("errors"), phi.get("errors")),
        ("measured (all scored live)", olmo.get("measured"), phi.get("measured")),
    ]
    print(f"{'metric':28}  {'OLMo':>16}  {'Phi':>16}")
    print("-" * 64)
    for name, a, b in rows:
        def cell(v):
            if v is None:
                return "—"
            if isinstance(v, float):
                return f"{v:.2f}"
            return str(v)

        print(f"{name:28}  {cell(a):>16}  {cell(b):>16}")
