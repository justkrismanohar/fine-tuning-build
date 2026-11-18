"""Shared resume-redaction evaluation (Day 1 T1-05 baseline, Day 3 reuse).

Scores outputs against the synthetic answer key, runs the release checks, applies the per-document
stop rule, summarises, saves runs, and (for live runs) calls the existing chat backend through
civicdesk_lab. Stdlib only; civicdesk_lab and transformers are imported lazily.
"""
from __future__ import annotations

import difflib
import json
import math
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "data" / "teaching_set_v1.json"
BENCH_PATH = HERE / "data" / "resume_redaction_test_v1.json"
REPLAY_PATH = HERE / "data" / "illustrative_outputs_teaching_v1.json"
BASELINE_DIR = HERE / "baselines"
PROMPT_VERSION = "redact-prompt-v1"
PLACEHOLDER_RE = re.compile(r"\[(PERSON|EMAIL|PHONE|ADDRESS|DOB|ID)\]")

# --- release checks (deliberately simple; each has false positives and false negatives) -------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b")
ID_RE = re.compile(r"\b[A-Z]{2}-ID-\d{4}-\d{3,}\b")


def load_fixture(path: Path = FIXTURE_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_benchmark(path: Path = BENCH_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_replay(path: Path = REPLAY_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_run(run: dict, name: str) -> Path:
    """Save a run (synthetic text only). Never point this at real documents: it stores outputs verbatim."""
    BASELINE_DIR.mkdir(exist_ok=True)
    p = BASELINE_DIR / f"{name}.json"
    p.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def load_run(name: str) -> dict:
    return json.loads((BASELINE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def release_checks(output: str, form: dict | None) -> list[str]:
    """Return the names of checks that fired on a redacted output. Empty list is NOT proof of safety."""
    fired = []
    if output is None or not output.strip():
        return ["empty_output"]
    if EMAIL_RE.search(output):
        fired.append("email_pattern")
    if PHONE_RE.search(output):
        fired.append("phone_pattern")
    if ID_RE.search(output):
        fired.append("id_pattern")
    if form:
        low = output.lower()
        if form.get("email") and form["email"].lower() in low:
            fired.append("known_email")
        if form.get("phone") and _digits(form["phone"])[-7:] in _digits(output):
            fired.append("known_phone")
        if form.get("name"):
            parts = [p for p in re.split(r"[\s-]+", form["name"]) if len(p) >= 4]
            hits = [p for p in parts if re.search(rf"\b{re.escape(p)}\b", output)]
            if hits:
                fired.append("known_name_part:" + "/".join(hits))
    return fired


def score_doc(doc: dict, output: str | None) -> dict:
    """Compare one output with the answer key. Needs the key, so this is evaluation, not a live check."""
    out = output or ""
    missed = [s for s in doc["spans"] if s["text"] in out]
    lost_keep = [k for k in doc["keep"] if k not in out]
    n_ph_expected = len(PLACEHOLDER_RE.findall(doc["expected"]))
    n_ph_output = len(PLACEHOLDER_RE.findall(out))
    # unrelated edits: diff against the expected redaction, ignoring placeholder tokens
    a = PLACEHOLDER_RE.sub("§", doc["expected"]).split()
    b = PLACEHOLDER_RE.sub("§", out).split()
    edits = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        exp, got = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if any(m["text"] in got for m in missed) and "\u00a7" in exp:
            kind = "leak"
        elif got.count("\u00a7") > exp.count("\u00a7"):
            kind = "over_redaction"
        elif tag == "delete" and i2 == len(a):
            kind = "truncation"
        else:
            kind = "unrelated_edit"
        edits.append({"kind": kind, "expected": exp, "got": got})
    kinds = {e["kind"] for e in edits}
    return {
        "id": doc["id"],
        "spans_total": len(doc["spans"]),
        "spans_missed": [{"type": s["type"], "text": s["text"]} for s in missed],
        "leaked": bool(missed),
        "keep_lost": lost_keep,
        "extra_placeholders": max(0, n_ph_output - n_ph_expected),
        "over_redacted": n_ph_output > n_ph_expected or "over_redaction" in kinds,
        "truncated": "truncation" in kinds,
        "unrelated_edit": "unrelated_edit" in kinds,
        "edits": edits,
        "empty": not out.strip(),
        "acceptable": not (missed or lost_keep or edits or not out.strip()),
    }


def route(fired: list[str], output: str | None, doc: dict, latency_s: float | None = None,
          timeout_s: float = 30.0) -> tuple[str, list[str]]:
    """Per-document stop rule. Uses only what is available at run time (no answer key)."""
    reasons = list(fired)
    out = output or ""
    if not out.strip():
        reasons.append("empty_output")
    elif len(out) < 0.6 * len(doc["text"]):
        reasons.append("output_much_shorter_than_input (possible truncation)")
    if latency_s is not None and latency_s > timeout_s:
        reasons.append("timeout")
    return ("HOLD for authorised review" if reasons else "pass checks (not proof of safety)"), reasons


def evaluate(fixture: dict, outputs: dict[str, str], latencies: dict[str, float] | None = None) -> list[dict]:
    rows = []
    for doc in fixture["docs"]:
        out = outputs.get(doc["id"])
        sc = score_doc(doc, out)
        fired = release_checks(out, doc.get("form"))
        decision, reasons = route(fired, out, doc, (latencies or {}).get(doc["id"]))
        sc.update({"checks_fired": fired, "decision": decision, "reasons": reasons})
        rows.append(sc)
    return rows


def summary_table(fixture: dict, rows: list[dict]) -> dict:
    types: dict[str, dict[str, int]] = {}
    for doc, r in zip(fixture["docs"], rows):
        if r["empty"]:
            continue  # empty or failed outputs are reported as not scored, never as "nothing leaked"
        missed_texts = {(m["type"], m["text"]) for m in r["spans_missed"]}
        for s in doc["spans"]:
            t = types.setdefault(s["type"], {"total": 0, "missed": 0})
            t["total"] += 1
            t["missed"] += (s["type"], s["text"]) in missed_texts
    docs_with_pii = [r for r in rows if r["spans_total"] > 0 and not r["empty"]]
    held = [r for r in rows if r["decision"].startswith("HOLD")]
    leaked = [r for r in rows if r["leaked"]]
    total = sum(t["total"] for t in types.values())
    missed = sum(t["missed"] for t in types.values())
    return {
        "docs_not_scored (empty or failed)": [r["id"] for r in rows if r["empty"]],
        "spans_total": total,
        "spans_missed": missed,
        "span_recall": round((total - missed) / total, 3) if total else None,
        "recall_by_type": {k: f"{v['total'] - v['missed']}/{v['total']}" for k, v in sorted(types.items())},
        "docs_with_pii": len(docs_with_pii),
        "docs_leaked": len(leaked),
        "doc_leak_rate": f"{len(leaked)}/{len(docs_with_pii)}",
        "docs_over_redacted": [r["id"] for r in rows if r["over_redacted"]],
        "docs_truncated_or_empty": [r["id"] for r in rows if r["truncated"] or r["empty"]],
        "docs_with_unrelated_edits": [r["id"] for r in rows if r["unrelated_edit"]],
        "acceptable_as_is": [r["id"] for r in rows if r["acceptable"]],
        "held": [r["id"] for r in held],
        "silent_leaks (leaked but passed checks)": [r["id"] for r in leaked if not r["decision"].startswith("HOLD")],
        "false_holds (held, output was acceptable)": [r["id"] for r in held if r["acceptable"]],
        "note": "Span recall counts text that was cut off as removed. Read it beside truncation.",
    }


EXAMPLE_RULE = {
    "label": "EXAMPLE classroom acceptance rule, fixed before any run. Not a standard and not release permission.",
    "max_docs_with_contact_or_id_leak": 0,   # residual EMAIL, PHONE, ID or DOB in any document
    "max_docs_with_any_leak": 2,             # out of the documents that contain PII
    "max_docs_over_redacted_or_altered": 4,  # out of all documents
    "max_docs_empty_failed_or_truncated": 0,
    "max_p95_latency_s": 20.0,               # course GPU; replace with your own budget
}


def p95(values: list[float]) -> float | None:
    v = sorted(x for x in values if x is not None)
    if not v:
        return None
    return v[min(len(v) - 1, math.ceil(0.95 * len(v)) - 1)]


def check_rule(rows: list[dict], latencies: dict[str, float] | None, rule: dict = EXAMPLE_RULE) -> dict:
    """Apply a predeclared rule to one scored run. Returns each criterion with its value and verdict."""
    hard = {"EMAIL", "PHONE", "ID", "DOB"}
    contact = sum(any(m["type"] in hard for m in r["spans_missed"]) for r in rows if not r["empty"])
    anyleak = sum(r["leaked"] for r in rows if not r["empty"])
    altered = sum(r["over_redacted"] or r["unrelated_edit"] for r in rows)
    broken = sum(r["empty"] or r["truncated"] for r in rows)
    lat = p95(list((latencies or {}).values()))
    crit = [
        ("docs with residual email/phone/ID/DOB", contact, contact <= rule["max_docs_with_contact_or_id_leak"]),
        ("docs with any leaked span", anyleak, anyleak <= rule["max_docs_with_any_leak"]),
        ("docs over-redacted or altered", altered, altered <= rule["max_docs_over_redacted_or_altered"]),
        ("docs empty, failed or truncated", broken, broken <= rule["max_docs_empty_failed_or_truncated"]),
        ("p95 latency (s)", lat, lat is not None and lat <= rule["max_p95_latency_s"]),
    ]
    return {"rule": rule["label"], "criteria": crit, "meets_rule": all(c[2] for c in crit)}


def upper_bound_95(failures: int, n: int) -> float:
    """One-sided exact (Clopper-Pearson) 95% upper bound on a failure rate.
    Valid only if the n items are a random sample from the population you care about."""
    if n <= 0:
        raise ValueError("n must be positive")
    if failures >= n:
        return 1.0
    if failures == 0:
        return 1 - 0.05 ** (1 / n)

    def cdf(p: float) -> float:
        return sum(math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(failures + 1))

    lo, hi = failures / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) > 0.05:
            lo = mid
        else:
            hi = mid
    return hi


def cost_per_acceptable(rows: list[dict], *, compute_cost_per_doc: float,
                        review_minutes_per_hold: float, reviewer_cost_per_hour: float) -> dict:
    """Scoped cost per acceptable answer for ONE run: (compute + review time on held docs) / docs
    acceptable as-is. Every input is the caller's own figure; nothing here is a measured price.
    Leaves out engineering, data preparation, audits and the cost of a leak that got through."""
    n = len(rows)
    holds = sum(r["decision"].startswith("HOLD") for r in rows)
    ok = sum(r["acceptable"] for r in rows)
    total = n * compute_cost_per_doc + holds * review_minutes_per_hold / 60 * reviewer_cost_per_hour
    return {"docs": n, "held": holds, "acceptable_as_is": ok, "run_cost": round(total, 2),
            "cost_per_acceptable": round(total / ok, 2) if ok else None,
            "scope": "compute + review of held docs only; excludes build, audit and leak costs"}


# --- optional live run through the existing backend -----------------------------------------
SYSTEM_PROMPT = (
    "You redact personal data from CVs. Replace each of these with its placeholder: "
    "names of private individuals [PERSON], email addresses including spelled-out ones [EMAIL], "
    "phone numbers [PHONE], home addresses [ADDRESS], dates of birth [DOB], ID numbers [ID]. "
    "Keep employer and institution names, job titles, dates of employment, qualifications, skills "
    "and reference numbers exactly as written. Change nothing else. Return only the redacted text."
)


def run_live(
    fixture: dict,
    which: str = "olmo",
    timeout_s: float = 30.0,
    adapter_dir: str | None = None,
    served_name: str | None = None,
) -> dict:
    """Send each synthetic doc to the backend chosen in T1-01. Only 'live' replies count as measured.

    civicdesk_lab.chat() falls back to canned demo text on errors; those replies are recorded as
    errors (empty output), never scored as model behaviour.
    """
    import civicdesk_lab as lab  # lazy on purpose: replay mode needs no backend
    import os

    if served_name or which in {"olmo-adapter", "adapter"}:
        model = served_name or os.environ.get("CIVICDESK_ADAPTER_SERVED_NAME", "olmo-redact-lora")
    else:
        model = lab.resolve_model(which)
    outputs, latencies, notes, usage = {}, {}, {}, {}
    for doc in fixture["docs"]:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": doc["text"]}]
        try:
            res = lab.chat(msgs, model=model, timeout=timeout_s)
        except Exception as exc:  # fallback_to_demo=False raises
            res = {"ok": False, "mode": "error", "text": "", "latency_ms": int(timeout_s * 1000), "error": str(exc)}
        if res.get("mode") != "live":
            outputs[doc["id"]] = ""
            notes[doc["id"]] = f"not measured: mode={res.get('mode')} {res.get('error', '')}".strip()
        else:
            outputs[doc["id"]] = res["text"]
            notes[doc["id"]] = "live"
            raw = res.get("raw") or {}
            if isinstance(raw, dict) and raw.get("usage"):
                usage[doc["id"]] = raw["usage"]  # present once the server returns usage (T1-03 spec)
        latencies[doc["id"]] = round(res.get("latency_ms", 0) / 1000, 2)
    pack = {
        "model": model,
        "backend": lab.endpoint_config()["backend"],
        "prompt_version": PROMPT_VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "benchmark_version": fixture.get("benchmark_version") or fixture.get("fixture_version"),
        "generation": "temperature 0, max_tokens 256 (civicdesk_lab defaults)",
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "usage_from_server": usage,
        "fixture_sha256": fixture["sha256"],
        "outputs": outputs,
        "latency_s": latencies,
        "notes": notes,
        "measured": all(v == "live" for v in notes.values()),
    }
    if adapter_dir or which in {"olmo-adapter", "adapter"} or served_name:
        pack["adapter_name"] = model
        pack["adapter_dir"] = adapter_dir
        pack["base_revision"] = os.environ.get("CIVICDESK_OLMO_REVISION")
        pack["training_data_version"] = "train-clean-v1"
        if adapter_dir:
            import hashlib
            from pathlib import Path

            weights = Path(adapter_dir) / "adapter_model.safetensors"
            if weights.is_file():
                pack["adapter_sha256"] = hashlib.sha256(weights.read_bytes()).hexdigest()
            report = Path(adapter_dir) / "training_report.json"
            if report.is_file():
                rep = json.loads(report.read_text(encoding="utf-8"))
                pack["training_file_sha256"] = rep.get("training_sha256")
                pack["base_revision"] = pack["base_revision"] or rep.get("base_revision")
    return pack


def count_tokens(texts: dict[str, str], model_dir: str | None = None) -> dict[str, int] | None:
    """Count tokens with the OLMo tokenizer from the folder already in the image (no weights loaded).
    The course server returns no usage figures, so this is how tokens are measured. Returns None if
    transformers or the folder is unavailable."""
    try:
        from transformers import AutoTokenizer
    except Exception:
        return None
    import os

    path = model_dir or os.environ.get(
        "CIVICDESK_TOKENIZER_DIR", os.path.join(os.environ.get("CIVICDESK_MODELS_DIR", "/models"), "olmo"))
    try:
        tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
    except Exception:
        return None
    return {k: len(tok.encode(v or "", add_special_tokens=False)) for k, v in texts.items()}
