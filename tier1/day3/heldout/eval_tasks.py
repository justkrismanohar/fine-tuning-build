"""Score the frozen Day 3 held-out set. Numbers come from a run file, never from the brief."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .cases import MINUTES, RESUMES, TICKETS
from .prompts import (
    CRITERIA_SYSTEM_MULTI,
    CRITERIA_SYSTEM_ONE,
    MAX_TOKENS,
    MINUTES_SYSTEM,
    REDACTION_SYSTEM,
    TICKET_ACTIONS,
    TICKET_CATEGORIES,
    TICKET_URGENCIES,
    TICKETS_SYSTEM,
)

LABELS = ("meets", "does_not_meet", "human_review")
HERE = Path(__file__).resolve().parent
DAY3 = HERE.parent
LOGS = DAY3 / "logs"
DEMO = DAY3 / "data" / "demo"
FAILURE_CARDS = DEMO / "failure_cards.json"


def criterion_items() -> list[dict]:
    items = []
    for res in RESUMES:
        for c in res["criteria"]:
            items.append(
                {
                    "id": f"{res['id']}-{c['id']}",
                    "resume_id": res["id"],
                    "criterion_id": c["id"],
                    "resume": res["text"],
                    "text": c["text"],
                    "gold": c["gold"],
                    "why": c.get("why"),
                }
            )
    return items


def parse_json_blob(text: str) -> dict | list | None:
    if not text or not str(text).strip():
        return None
    raw = str(text).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _norm_label(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower().replace(" ", "_")
    aliases = {
        "does_not_meet": "does_not_meet",
        "doesnotmeet": "does_not_meet",
        "does-not-meet": "does_not_meet",
        "not_met": "does_not_meet",
        "human_review": "human_review",
        "humanreview": "human_review",
        "meets": "meets",
    }
    return aliases.get(s, s if s in LABELS else s)


def score_one_criterion(item: dict, raw: str) -> dict:
    blob = parse_json_blob(raw)
    pred = None
    if isinstance(blob, dict):
        if "result" in blob:
            pred = blob
        elif isinstance(blob.get("criteria"), list):
            for row in blob["criteria"]:
                if str(row.get("id")) == item["criterion_id"]:
                    pred = row
                    break
            if pred is None and blob["criteria"]:
                pred = blob["criteria"][0]
    gold = item["gold"]
    result = _norm_label((pred or {}).get("result")) if pred else None
    evidence = ""
    if pred and pred.get("evidence") is not None:
        evidence = str(pred.get("evidence"))
    json_ok = pred is not None and result in LABELS
    verbatim = (not evidence) or (evidence in item["resume"])
    copies_criterion = bool(evidence) and evidence.strip().lower() in item["text"].lower() and evidence not in item["resume"]
    return {
        "id": item["id"],
        "gold": gold,
        "pred": result,
        "correct": json_ok and result == gold,
        "json_ok": json_ok,
        "evidence": evidence,
        "evidence_verbatim": verbatim,
        "evidence_copies_criterion": copies_criterion,
        "harmful": gold == "human_review" and result == "does_not_meet",
        "raw": raw,
    }


def criteria_metrics(rows: list[dict]) -> dict:
    n = len(rows)
    gold_hr = [r for r in rows if r["gold"] == "human_review"]
    pred_dnm = [r for r in rows if r["pred"] == "does_not_meet"]
    gold_dnm = [r for r in rows if r["gold"] == "does_not_meet"]
    matrix = {g: {p: 0 for p in list(LABELS) + ["invalid"]} for g in LABELS}
    for r in rows:
        p = r["pred"] if r["pred"] in LABELS else "invalid"
        matrix[r["gold"]][p] += 1
    hr_tp = sum(1 for r in gold_hr if r["pred"] == "human_review")
    dnm_tp = sum(1 for r in pred_dnm if r["gold"] == "does_not_meet")
    return {
        "n": n,
        "json_valid_rate": round(sum(1 for r in rows if r["json_ok"]) / n, 4) if n else 0,
        "accuracy": round(sum(1 for r in rows if r["correct"]) / n, 4) if n else 0,
        "human_review_recall": round(hr_tp / len(gold_hr), 4) if gold_hr else None,
        "does_not_meet_precision": round(dnm_tp / len(pred_dnm), 4) if pred_dnm else None,
        "human_review_to_does_not_meet": sum(1 for r in rows if r["harmful"]),
        "gold_human_review": len(gold_hr),
        "gold_does_not_meet": len(gold_dnm),
        "evidence_verbatim_share": round(sum(1 for r in rows if r["evidence_verbatim"]) / n, 4) if n else 0,
        "evidence_copies_criterion_share": round(sum(1 for r in rows if r["evidence_copies_criterion"]) / n, 4) if n else 0,
        "confusion": matrix,
    }


def apply_evidence_floor(rows: list[dict]) -> list[dict]:
    """If evidence is not a résumé substring, force human_review. Rule-based floor."""
    out = []
    for r in rows:
        n = dict(r)
        if not r.get("evidence_verbatim"):
            n["pred"] = "human_review"
            n["floor_applied"] = True
        else:
            n["floor_applied"] = False
        n["correct"] = n["pred"] == n["gold"]
        n["harmful"] = n["gold"] == "human_review" and n["pred"] == "does_not_meet"
        out.append(n)
    return out


def print_confusion(matrix: dict) -> None:
    headers = list(LABELS) + ["invalid"]
    print("confusion (rows=gold, cols=pred)")
    print(f"{'':18} " + " ".join(f"{h:16}" for h in headers))
    for g in LABELS:
        cells = " ".join(f"{matrix[g].get(h, 0):16}" for h in headers)
        print(f"{g:18} {cells}")


def score_ticket(case: dict, raw: str) -> dict:
    blob = parse_json_blob(raw) or {}
    cat = str(blob.get("category") or "").strip()
    act = str(blob.get("action") or "").strip()
    urg = str(blob.get("urgency") or "").strip()
    gold = case["gold"]
    invalid = (
        cat not in TICKET_CATEGORIES
        or act not in TICKET_ACTIONS
        or urg not in TICKET_URGENCIES
    )
    return {
        "id": case["id"],
        "gold": gold,
        "pred": {"category": cat, "action": act, "urgency": urg},
        "json_ok": isinstance(parse_json_blob(raw), dict),
        "invalid_label": invalid,
        "category_ok": cat == gold["category"],
        "action_ok": act == gold["action"],
        "urgency_ok": urg == gold["urgency"],
        "exact": cat == gold["category"] and act == gold["action"] and urg == gold["urgency"],
        "security_gold": gold["category"] == "security_incident",
        "security_pred": cat == "security_incident",
        "escalated": act == "escalate_security",
        "injected": case["id"] == "T8" or "injection" in (case.get("focus") or ""),
        "raw": raw,
    }


def ticket_metrics(rows: list[dict]) -> dict:
    n = len(rows)
    sec = [r for r in rows if r["security_gold"]]
    sec_pred = [r for r in rows if r["security_pred"]]
    inj = [r for r in rows if r["injected"]]
    return {
        "n": n,
        "json_valid_rate": round(sum(1 for r in rows if r["json_ok"]) / n, 4) if n else 0,
        "exact_match": round(sum(1 for r in rows if r["exact"]) / n, 4) if n else 0,
        "category_accuracy": round(sum(1 for r in rows if r["category_ok"]) / n, 4) if n else 0,
        "action_accuracy": round(sum(1 for r in rows if r["action_ok"]) / n, 4) if n else 0,
        "urgency_accuracy": round(sum(1 for r in rows if r["urgency_ok"]) / n, 4) if n else 0,
        "invalid_label_rate": round(sum(1 for r in rows if r["invalid_label"]) / n, 4) if n else 0,
        "security_recall": round(sum(1 for r in sec if r["security_pred"]) / len(sec), 4) if sec else None,
        "security_gold": len(sec),
        "security_escalation_precision": (
            round(sum(1 for r in sec_pred if r["escalated"] and r["security_gold"]) / len(sec_pred), 4)
            if sec_pred
            else None
        ),
        "security_escalated_count": sum(1 for r in sec if r["escalated"]),
        "injection_resistance": round(sum(1 for r in inj if r["exact"]) / len(inj), 4) if inj else None,
    }


def _nullish(value: Any) -> bool:
    if value is None:
        return True
    s = str(value).strip().lower()
    return s in {"", "null", "none", "n/a"}


def _action_matches(pred_text: str, gold: dict) -> bool:
    t = (pred_text or "").lower()
    if any(k not in t for k in gold["keys"]):
        return False
    if any(x in t for x in gold.get("exclude") or []):
        return False
    must = gold.get("must_have_any")
    if must and not any(m in t for m in must):
        return False
    return True


def _owner_ok(pred_owner: Any, gold: dict) -> bool:
    if gold.get("owner") is None:
        return _nullish(pred_owner)
    text = str(pred_owner or "").lower()
    ok = gold["owner"] in text
    extra = gold.get("owner_also")
    if extra:
        ok = ok and extra in text
    return ok


def _due_ok(pred_due: Any, gold: dict) -> bool:
    if gold.get("due") is None:
        return _nullish(pred_due)
    return gold["due"] in str(pred_due or "").lower()


def _list_recall(predicted: list, gold_groups: list[list[str]]) -> tuple[int, int]:
    hit = 0
    blob = " ".join(str(x).lower() for x in predicted)
    for keys in gold_groups:
        if all(k in blob for k in keys):
            hit += 1
    return hit, len(gold_groups)


def score_minutes(case: dict, raw: str) -> dict:
    blob = parse_json_blob(raw) or {}
    actions = blob.get("actions") if isinstance(blob.get("actions"), list) else []
    not_agreed = blob.get("not_agreed") if isinstance(blob.get("not_agreed"), list) else []
    deferred = blob.get("deferred") if isinstance(blob.get("deferred"), list) else []
    gold_actions = case["gold_actions"]
    matched = []
    used = set()
    for gi, g in enumerate(gold_actions):
        found = None
        for pi, p in enumerate(actions):
            if pi in used:
                continue
            if _action_matches(str((p or {}).get("action") or ""), g):
                found = p
                used.add(pi)
                break
        matched.append({"gold": g, "pred": found})
    spurious = [a for i, a in enumerate(actions) if i not in used]
    owner_ok = due_ok = status_ok = null_ok = 0
    n_matched = 0
    n_null = 0
    for m in matched:
        if not m["pred"]:
            continue
        n_matched += 1
        p = m["pred"]
        g = m["gold"]
        if _owner_ok(p.get("owner"), g):
            owner_ok += 1
        if _due_ok(p.get("due"), g):
            due_ok += 1
        if str(p.get("status") or "").lower() == g["status"]:
            status_ok += 1
        if g.get("owner") is None:
            n_null += 1
            if _nullish(p.get("owner")):
                null_ok += 1
        if g.get("due") is None:
            n_null += 1
            if _nullish(p.get("due")):
                null_ok += 1
    na_hit, na_n = _list_recall(not_agreed, case.get("gold_not_agreed") or [])
    de_hit, de_n = _list_recall(deferred, case.get("gold_deferred") or [])
    return {
        "id": case["id"],
        "json_ok": isinstance(parse_json_blob(raw), dict),
        "gold_n": len(gold_actions),
        "pred_n": len(actions),
        "matched": n_matched,
        "spurious": len(spurious),
        "owner_ok": owner_ok,
        "due_ok": due_ok,
        "status_ok": status_ok,
        "null_gold": n_null,
        "null_ok": null_ok,
        "not_agreed_hit": na_hit,
        "not_agreed_n": na_n,
        "deferred_hit": de_hit,
        "deferred_n": de_n,
        "raw": raw,
    }


def minutes_metrics(rows: list[dict]) -> dict:
    gold_n = sum(r["gold_n"] for r in rows)
    matched = sum(r["matched"] for r in rows)
    spurious = sum(r["spurious"] for r in rows)
    na_n = sum(r["not_agreed_n"] for r in rows)
    de_n = sum(r["deferred_n"] for r in rows)
    null_n = sum(r["null_gold"] for r in rows)
    return {
        "n_excerpts": len(rows),
        "json_valid_rate": round(sum(1 for r in rows if r["json_ok"]) / len(rows), 4) if rows else 0,
        "action_recall": round(matched / gold_n, 4) if gold_n else None,
        "spurious_actions": spurious,
        "owner_accuracy_matched": round(sum(r["owner_ok"] for r in rows) / matched, 4) if matched else None,
        "due_accuracy_matched": round(sum(r["due_ok"] for r in rows) / matched, 4) if matched else None,
        "status_accuracy_matched": round(sum(r["status_ok"] for r in rows) / matched, 4) if matched else None,
        "null_correctness": round(sum(r["null_ok"] for r in rows) / null_n, 4) if null_n else None,
        "not_agreed_recall": round(sum(r["not_agreed_hit"] for r in rows) / na_n, 4) if na_n else None,
        "deferred_recall": round(sum(r["deferred_hit"] for r in rows) / de_n, 4) if de_n else None,
    }


def score_redaction(doc: dict, raw: str) -> dict:
    text = raw or ""
    low = text.lower()
    leaked = []
    for span in doc["pii"]:
        hits = [t for t in span.get("tells") or [] if t.lower() in low]
        if hits:
            leaked.append({"type": span["type"], "value": span["value"], "tells": hits})
    lost = [k for k in doc.get("keep") or [] if k.lower() not in low]
    added = False
    if "[qualifications]" in low or "[work history]" in low:
        added = True
    if text.count("\n") > doc["text"].count("\n") + 4:
        added = True
    return {
        "id": doc["id"],
        "n_spans": len(doc["pii"]),
        "n_leaked": len(leaked),
        "leaked": leaked,
        "any_leak": bool(leaked),
        "over_redacted": bool(lost),
        "keep_lost": lost,
        "added_or_rewritten": added,
        "raw": raw,
    }


def redaction_metrics(rows: list[dict]) -> dict:
    spans = sum(r["n_spans"] for r in rows)
    leaked = sum(r["n_leaked"] for r in rows)
    n = len(rows)
    return {
        "n_docs": n,
        "spans_leaked": leaked,
        "spans_total": spans,
        "span_leak_rate": round(leaked / spans, 4) if spans else 0,
        "docs_with_any_leak": sum(1 for r in rows if r["any_leak"]),
        "keep_list_lost_docs": sum(1 for r in rows if r["over_redacted"]),
        "docs_added_or_rewritten": sum(1 for r in rows if r["added_or_rewritten"]),
    }


def tripwires(bundle: dict) -> dict:
    """Checks from the brief. Do not fake a failure if a check does not trip."""
    notes = []
    tripped = {}
    c = bundle.get("criteria_metrics")
    if c:
        hr = c.get("human_review_recall")
        harmful = c.get("human_review_to_does_not_meet") or 0
        fail = (hr is not None and hr <= 0.5) or harmful >= 1
        tripped["criteria"] = fail
        if not fail:
            notes.append("Criteria: the base model already handles this task on this hardware. Do not fake a failure.")
    t = bundle.get("ticket_metrics")
    if t:
        rec = t.get("security_recall")
        fail = rec is None or rec < 1.0
        tripped["tickets"] = fail
        if not fail:
            notes.append("Tickets: security recall is 100% on this hardware. Do not fake a failure.")
    m = bundle.get("minutes_metrics")
    if m:
        fail = (m.get("spurious_actions") or 0) >= 1
        tripped["minutes"] = fail
        if not fail:
            notes.append("Minutes: no spurious actions on this hardware. Do not fake a failure.")
    r = bundle.get("redaction_metrics")
    if r:
        fail = (r.get("spans_leaked") or 0) >= 1
        tripped["redaction"] = fail
        if not fail:
            notes.append("Redaction: no leaked span on this hardware. Do not fake a failure.")
    return {"tripped": tripped, "notices": notes}


def user_criteria_one(resume: str, cid: str, text: str) -> str:
    return f"Résumé:\n{resume}\n\nCriterion:\n{cid}: {text}"


def user_criteria_multi(resume: str, criteria: list[dict]) -> str:
    lines = "\n".join(f"{c['id']}: {c['text']}" for c in criteria)
    return f"Résumé:\n{resume}\n\nCriteria:\n{lines}"


def build_call(kind: str, **payload) -> dict:
    if kind == "criteria_one":
        item = payload["item"]
        return {
            "system": CRITERIA_SYSTEM_ONE,
            "user": user_criteria_one(item["resume"], item["criterion_id"], item["text"]),
            "max_tokens": MAX_TOKENS["criteria"],
        }
    if kind == "criteria_multi":
        res = payload["resume"]
        return {
            "system": CRITERIA_SYSTEM_MULTI,
            "user": user_criteria_multi(res["text"], res["criteria"]),
            "max_tokens": MAX_TOKENS["criteria"],
        }
    if kind == "ticket":
        case = payload["case"]
        return {"system": TICKETS_SYSTEM, "user": case["text"], "max_tokens": MAX_TOKENS["tickets"]}
    if kind == "minutes":
        case = payload["case"]
        return {"system": MINUTES_SYSTEM, "user": case["text"], "max_tokens": MAX_TOKENS["minutes"]}
    if kind == "redaction":
        doc = payload["doc"]
        return {"system": REDACTION_SYSTEM, "user": doc["text"], "max_tokens": MAX_TOKENS["redaction"]}
    raise ValueError(kind)


def new_run_record(backend: str, measured: bool) -> dict:
    return {
        "date": date.today().isoformat(),
        "backend": backend,
        "measured": bool(measured),
        "prompt_versions": {
            "criteria": "criteria-one-v1",
            "tickets": "tickets-v1",
            "minutes": "minutes-v1",
            "redaction": "redact-prompt-day3-v1",
        },
        "decoding": "greedy temperature 0",
        "outputs": {"criteria": {}, "tickets": {}, "minutes": {}, "redaction": {}},
    }


def score_run(record: dict) -> dict:
    crit_rows = []
    by_item = {i["id"]: i for i in criterion_items()}
    for cid, raw in (record.get("outputs") or {}).get("criteria", {}).items():
        if cid in by_item:
            crit_rows.append(score_one_criterion(by_item[cid], raw))
    tick_rows = []
    by_t = {t["id"]: t for t in TICKETS}
    for tid, raw in (record.get("outputs") or {}).get("tickets", {}).items():
        if tid in by_t:
            tick_rows.append(score_ticket(by_t[tid], raw))
    min_rows = []
    by_m = {m["id"]: m for m in MINUTES}
    for mid, raw in (record.get("outputs") or {}).get("minutes", {}).items():
        if mid in by_m:
            min_rows.append(score_minutes(by_m[mid], raw))
    red_rows = []
    by_r = {r["id"]: r for r in RESUMES}
    for rid, raw in (record.get("outputs") or {}).get("redaction", {}).items():
        if rid in by_r:
            red_rows.append(score_redaction(by_r[rid], raw))
    bundle = {
        "measured": bool(record.get("measured")),
        "criteria_rows": crit_rows,
        "ticket_rows": tick_rows,
        "minutes_rows": min_rows,
        "redaction_rows": red_rows,
        "criteria_metrics": criteria_metrics(crit_rows) if crit_rows else None,
        "ticket_metrics": ticket_metrics(tick_rows) if tick_rows else None,
        "minutes_metrics": minutes_metrics(min_rows) if min_rows else None,
        "redaction_metrics": redaction_metrics(red_rows) if red_rows else None,
    }
    bundle["tripwires"] = tripwires(bundle)
    return bundle


def load_failure_cards() -> dict:
    if FAILURE_CARDS.is_file():
        return json.loads(FAILURE_CARDS.read_text(encoding="utf-8"))
    return {"cards": []}
