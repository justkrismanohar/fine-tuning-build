"""Day 3 fine-tune literacy helper. Inspect rows, compare runs, optional live redactor.

Demo functions stay as labelled stand-ins. Live generation uses civicdesk_lab.chat.
Never treat demo or fallback text as a measured run.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)
SHARED = (HERE.parent / "shared" / "resume_redaction").resolve()
RR_DATA = SHARED / "data"
RR_BASE = SHARED / "baselines"
DEMO = DATA / "demo"

OLMO_HIDDEN = 2048
OLMO_INTERMEDIATE = 8192
OLMO_LAYERS = 16
OLMO_TOTAL = 1_484_916_736
ATTN = ("q_proj", "k_proj", "v_proj", "o_proj")
MLP = ("gate_proj", "up_proj", "down_proj")

_day3_backend = {"choice": "olmo", "model": None}

NOT_SCORED = "not a model answer, not scored"
NOISE_LINE = "A difference of one or two documents out of 40 is within noise."


def _day1():
    for p in (HERE.parent / "day1", Path.cwd() / ".." / "day1", Path("../day1").resolve()):
        p = p.resolve()
        if (p / "civicdesk_lab.py").is_file():
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            import civicdesk_lab as lab  # noqa: WPS433

            return lab
    raise ImportError("civicdesk_lab.py not found (expected ../day1)")


def _rr():
    if str(SHARED) not in sys.path:
        sys.path.insert(0, str(SHARED))
    import redaction_eval as R  # noqa: WPS433

    return R


def set_backend(choice: str = "olmo") -> dict:
    """Switch this kernel: local OLMo (default), local Phi, or demo stand-ins."""
    lab = _day1()
    raw = (choice or "olmo").strip().lower()
    aliases = {
        "demo": "demo",
        "olmo": "olmo",
        "local": "olmo",
        "local-olmo": "olmo",
        "phi": "phi",
        "local-phi": "phi",
    }
    if raw not in aliases:
        raise ValueError('BACKEND must be "olmo", "phi", or "demo"')
    choice = aliases[raw]
    _day3_backend["choice"] = choice
    if choice == "demo":
        cfg = lab.use_backend("demo")
        _day3_backend["model"] = None
        print("BACKEND=demo — labelled stand-ins and run files. Not scored as model performance.")
    else:
        cfg = lab.use_backend("local")
        model = lab.resolve_model(choice)
        _day3_backend["model"] = model
        url = cfg["olmo_url"] if choice == "olmo" else cfg["phi_url"]
        print(f"BACKEND=local  model={choice}")
        print("id:", model)
        print("url:", url)
        print("Needs the Day 1 server on that port. If the call fails, the notebook continues from run files / stand-ins.")
        if choice == "phi":
            print("Phi is :8001. Compose loads OLMo only unless CIVICDESK_LOAD_MODELS includes phi.")
            print("No measured Phi redaction baseline in this pack — Phi is generate-only here.")
    print("mode:", cfg.get("mode"))
    print("GPU / host:", lab.gpu_note())
    return cfg


def active_backend() -> str:
    return _day3_backend.get("choice") or "olmo"


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
    if "attachment" in u or "overnight" in u:
        return "[adapter demo] I have no handbook in this prompt. I will not invent a circular. That is RAG, not an adapter."
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
    print(NOT_SCORED)


def tool_gate(action: str) -> str:
    banned = {
        "reset_password": "BANNED. Trade IMSD: identity check is a human tool.",
        "write_glpi": "BANNED. No silent GLPI change.",
        "award_contract": "BANNED. Defence OPR / any spend: the model does not award.",
        "scrape_web_for_negotiation": "BANNED. CPO agentic market-research is not an open scrape from chat.",
        "draft_ticket": "ALLOWED. Saying something. A human still files it.",
        "quote_handbook": "ALLOWED. If the paragraph is in the prompt.",
        "draft_redacted_copy": "ALLOWED. A draft only. A person releases it.",
        "release_to_panel": "BANNED. Release is a human step.",
        "auto_release_if_pass_checks": "BANNED. PASS CHECKS means no check fired, not that the document is clean.",
    }
    key = action.strip().lower()
    return banned.get(key, "Unknown action. If it *does* something in a live system, treat as banned until listed.")


def load_adapter_card() -> dict:
    report = HERE / "adapters" / "olmo-resume-redact-lora-v1" / "training_report.json"
    if report.is_file():
        return card_from_report(json.loads(report.read_text(encoding="utf-8")))
    path = DATA / "adapter_stub.json"
    return json.loads(path.read_text(encoding="utf-8"))


def card_from_report(rep: dict) -> dict:
    return {
        "notice": "Adapter card from training_report.json. Rollback = stop loading this directory, rerun the benchmark.",
        "name": rep.get("adapter_name") or "olmo-resume-redact-lora-v1",
        "base_model": rep.get("base_model"),
        "base_revision": rep.get("base_revision"),
        "method": f"LoRA rank {rep.get('rank')} alpha {rep.get('alpha')} on {rep.get('targets')}",
        "trainable_count": rep.get("trainable_count"),
        "file_size": rep.get("adapter_file_size"),
        "training_data_version": rep.get("training_data_version"),
        "training_sha256": rep.get("training_sha256"),
        "validation_sha256": rep.get("validation_sha256"),
        "licence_note": "Adapter licence = base licence + every training row. CivicDesk fiction is classroom-only.",
        "rollback": "Stop loading this directory, rerun the benchmark.",
        "does_not_do": [
            "Look up a live register",
            "Retrieve a handbook paragraph unless that text is in the prompt",
            "Hire, grade, award, or reset a password",
        ],
    }


def print_adapter_card() -> None:
    card = load_adapter_card()
    _print_card(card)
    crit = DATA / "adapter_stub_criteria.json"
    if crit.is_file():
        print("--- criteria adapter (headline task) ---")
        _print_card(json.loads(crit.read_text(encoding="utf-8")))


def _print_card(card: dict) -> None:
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


def print_anatomy(model_dir: str = "/models/olmo") -> dict:
    """Print block-0 linear names from config. No GPU. No weights download."""
    path = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models")) / "olmo"
    if model_dir:
        path = Path(model_dir)
    cfg_path = path / "config.json"
    names = list(ATTN) + list(MLP)
    hidden = OLMO_HIDDEN
    layers = OLMO_LAYERS
    source = "classroom OLMo-2 1B figures (config not on this machine)"
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        hidden = int(cfg.get("hidden_size") or hidden)
        layers = int(cfg.get("num_hidden_layers") or layers)
        source = str(cfg_path)
    print("source:", source)
    print("hidden_size:", hidden, "layers:", layers)
    print("block 0 linear names (same in every block):")
    for n in names:
        print(" ", n)
    print("Day 1 spotlight: these names are the projections inside one transformer block — not a new idea.")
    return {"source": source, "hidden_size": hidden, "layers": layers, "linear_names": names}


def lora_param_count(targets, r, config=None) -> int:
    """Count LoRA parameters from dimensions. No model load."""
    hidden = OLMO_HIDDEN
    inter = OLMO_INTERMEDIATE
    layers = OLMO_LAYERS
    if config:
        hidden = int(config.get("hidden_size") or hidden)
        inter = int(config.get("intermediate_size") or inter)
        layers = int(config.get("num_hidden_layers") or layers)
    r = int(r)
    per = 0
    for t in targets:
        if t in ATTN:
            per += r * (hidden + hidden)
        elif t in MLP:
            per += r * (hidden + inter)
        else:
            raise ValueError(f"unknown target {t}")
    total = per * layers
    pct = 100.0 * total / OLMO_TOTAL
    print(f"targets={list(targets)}  r={r}  trainable={total:,}  ({pct:.4f}% of {OLMO_TOTAL:,})")
    return total


def inspect_training_rows(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else RR_DATA / "train_inspect_v1.json"
    if not p.is_file():
        p = RR_DATA / Path(str(path)).name
    blob = json.loads(p.read_text(encoding="utf-8"))
    rows = blob.get("rows") or blob
    print("file:", p)
    print("n:", len(rows))
    if blob.get("note_imbalance"):
        print("NOTE:", blob["note_imbalance"])
    print(f"{'id':8} {'layout':24} {'problem':12} user")
    for row in rows:
        user = row["messages"][1]["content"].replace("\n", " ")[:70]
        print(f"{row['id']:8} {str(row.get('layout')):24} {str(row.get('problem')):12} {user}")
    return rows


def score_hunt(found: dict) -> dict:
    key = json.loads((RR_DATA / "train_issues_key_v1.json").read_text(encoding="utf-8"))
    by = {p["id"]: p for p in key["problems"]}
    n_ok = 0
    print("hunt vs answer key")
    for kind in ("leak", "inconsistent", "canary", "rewrite", "imbalance"):
        gold = by[kind]
        got = found.get(kind)
        ok = got == gold["row_id"]
        n_ok += int(ok)
        mark = "ok" if ok else "miss"
        print(f"  {kind:12} got={got!s:8} want={gold['row_id']!s:8} {mark}  {gold['reason']}")
    print(f"score {n_ok} out of 5")
    return {"score": n_ok, "total": 5}


def adapter_run_path() -> Path:
    measured = RR_BASE / "olmo_adapter_v1.json"
    if measured.is_file():
        return measured
    return DEMO / "olmo_adapter_demo_v1.json"


def baseline_run_path() -> Path:
    return RR_BASE / "olmo_baseline_v1.json"


def _run_path(name: str) -> Path:
    for p in (RR_BASE / f"{name}.json", DEMO / f"{name}.json", Path(name)):
        if p.is_file():
            return p
    raise FileNotFoundError(name)


def _score_run(run: dict, bench: dict):
    R = _rr()
    rows = R.evaluate(bench, run["outputs"], run.get("latency_s"))
    table = R.summary_table(bench, rows)
    rule = R.check_rule(rows, run.get("latency_s"), R.EXAMPLE_RULE)
    return rows, table, rule


def compare_runs(base_path, adapter_path) -> dict:
    R = _rr()
    bench = R.load_benchmark()

    def _load(path):
        p = Path(path)
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
        return json.loads(_run_path(str(path)).read_text(encoding="utf-8"))

    base = _load(base_path)
    ad = _load(adapter_path)

    for label, run in (("base", base), ("adapter", ad)):
        if run.get("fixture_sha256") != bench["sha256"]:
            raise ValueError(f"{label} run is not this benchmark (sha256 mismatch)")
        if run.get("prompt_version") != "redact-prompt-v1":
            raise ValueError(f"{label} run prompt_version is not redact-prompt-v1")
        gen = str(run.get("generation") or "")
        if "256" not in gen:
            raise ValueError(f"{label} run decoding settings do not match (need max_tokens 256)")
    if not base.get("measured") or not ad.get("measured"):
        print("One or both files are not a measured run. Shown for literacy only.", NOT_SCORED)

    b_rows, b_tab, b_rule = _score_run(base, bench)
    a_rows, a_tab, a_rule = _score_run(ad, bench)
    by_id = {d["id"]: d for d in bench["docs"]}

    def hold(row):
        return str(row["decision"]).upper().startswith("HOLD")

    print("=== base ===")
    print(json.dumps(b_tab, indent=2))
    print("rule meets:" , "meets" if b_rule["meets_rule"] else "does not meet")
    print("=== adapter ===")
    print(json.dumps(a_tab, indent=2))
    print("rule meets:", "meets" if a_rule["meets_rule"] else "does not meet")

    fixed, broken = [], []
    for br, ar in zip(b_rows, a_rows):
        doc = by_id[br["id"]]
        layout = doc.get("category")
        if hold(br) and (not hold(ar)) and br.get("leaked") and not ar.get("leaked"):
            fixed.append({"id": br["id"], "layout": layout, "changed": "HOLD with leaks -> PASS CHECKS, leaks gone"})
        gained = (ar.get("over_redacted") and not br.get("over_redacted")) or (
            ar.get("unrelated_edit") and not br.get("unrelated_edit")
        )
        if (not hold(br) and hold(ar)) or gained:
            bits = []
            if not hold(br) and hold(ar):
                bits.append("PASS CHECKS -> HOLD")
            if ar.get("over_redacted") and not br.get("over_redacted"):
                bits.append("gained over-redaction")
            if ar.get("unrelated_edit") and not br.get("unrelated_edit"):
                bits.append("gained altered text")
            broken.append({"id": br["id"], "layout": layout, "changed": "; ".join(bits)})

    print("=== fixed ===")
    for row in fixed:
        print(f"  {row['id']}  {row['layout']}  {row['changed']}")
    if not fixed:
        print("  (none)")
    print("=== broken ===")
    for row in broken:
        print(f"  {row['id']}  {row['layout']}  {row['changed']}")
    if not broken:
        print("  (none)")
    print(NOISE_LINE)
    return {
        "base_rule": "meets" if b_rule["meets_rule"] else "does not meet",
        "adapter_rule": "meets" if a_rule["meets_rule"] else "does not meet",
        "docs_fixed": [x["id"] for x in fixed],
        "docs_broken": [x["id"] for x in broken],
        "base_table": b_tab,
        "adapter_table": a_tab,
    }


def load_redactor(adapter_dir=None):
    """Live redact(text, use_adapter). Raises if no GPU/weights; notebook then uses run files."""
    lab = _day1()
    R = _rr()
    choice = active_backend()
    if choice == "demo":
        raise RuntimeError("BACKEND=demo: no live redactor. Read the run files.")

    def redact(text: str, use_adapter: bool = False) -> str:
        if use_adapter:
            served = os.environ.get("CIVICDESK_ADAPTER_SERVED_NAME", "olmo-redact-lora")
            model = served
        else:
            model = _day3_backend.get("model") or lab.resolve_model("olmo" if choice != "phi" else "phi")
        msgs = [{"role": "system", "content": R.SYSTEM_PROMPT}, {"role": "user", "content": text}]
        res = lab.chat(msgs, model=model, timeout=20)
        if res.get("mode") != "live":
            raise RuntimeError(f"live redactor unavailable: {res.get('error') or res.get('mode')}")
        return res["text"]

    return redact


def docs_from_runs(doc_ids: list[str], base_run: str = "olmo_baseline_v1", adapter_run: str | None = None) -> None:
    """Print two-or-three documents from run files when live is down."""
    R = _rr()
    bench = R.load_benchmark()
    by = {d["id"]: d for d in bench["docs"]}
    base = json.loads(_run_path(base_run).read_text(encoding="utf-8"))
    ad_name = adapter_run
    if ad_name is None:
        if (RR_BASE / "olmo_adapter_v1.json").is_file():
            ad_name = str(RR_BASE / "olmo_adapter_v1.json")
        else:
            ad_name = str(DEMO / "olmo_adapter_demo_v1.json")
    ad = json.loads(Path(ad_name).read_text(encoding="utf-8") if Path(ad_name).is_file() else _run_path(ad_name).read_text(encoding="utf-8"))
    label = "from the run files"
    if not ad.get("measured"):
        label = "from the run files (demo adapter file; " + NOT_SCORED + ")"
    print(label)
    for did in doc_ids:
        doc = by[did]
        print("=" * 60, did, doc.get("category"))
        for tag, out in (("base", base["outputs"][did]), ("adapter", ad["outputs"][did])):
            sc = R.score_doc(doc, out)
            fired = R.release_checks(out, doc.get("form"))
            decision, reasons = R.route(fired, out, doc)
            print(f"--- {tag} ---")
            print(out[:500])
            print("score leaked:", sc["leaked"], "over_redacted:", sc["over_redacted"], "unrelated_edit:", sc["unrelated_edit"])
            print("route:", decision, reasons)


def load_gold_pairs() -> str:
    for p in (
        HERE.parent / "day1" / "logs" / "T1-05_gold_pairs.json",
        HERE.parent / "day1" / "completed" / "T1-05_gold_pairs_example.md",
        Path("../day1/completed/T1-05_gold_pairs_example.md"),
    ):
        if p.is_file():
            print("gold pairs from", p)
            return p.read_text(encoding="utf-8")
    return "(no gold pairs file found)"


def target_token_count() -> dict | None:
    R = _rr()
    clean = json.loads((RR_DATA / "train_clean_v1.json").read_text(encoding="utf-8"))
    texts = {row["id"]: row["target"] for row in clean["rows"]}
    counted = R.count_tokens(texts)
    if counted is None:
        words = {k: len(v.split()) for k, v in texts.items()}
        print("Day 1 tokenizer not on this machine. Word counts of training targets:")
        print("  n", len(words), "mean", round(sum(words.values()) / len(words), 1))
        return {"unit": "words", **{k: words[k] for k in list(words)[:5]}}
    print("Day 1 tokenizer count of training targets:")
    print("  n", len(counted), "mean", round(sum(counted.values()) / len(counted), 1))
    return counted


def _tasks():
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    from heldout import eval_tasks as E  # noqa: WPS433
    from heldout.cases import MINUTES, RESUMES, TICKETS

    return E, RESUMES, TICKETS, MINUTES


def inspect_criteria_rows(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else HERE / "data" / "criteria" / "train_v1.json"
    blob = json.loads(p.read_text(encoding="utf-8"))
    rows = blob.get("rows") or blob
    labels = {}
    hr = {}
    print("file:", p)
    print("n:", blob.get("n", len(rows)), "sha256:", blob.get("sha256"))
    print("labels:", blob.get("labels"))
    print("human_review subtypes:", blob.get("hr_subtypes"))
    print(f"{'id':10} {'result':16} {'subtype':22} criterion")
    for row in rows[:24]:
        tgt = row.get("target_obj") or json.loads(row["target"])
        labels[tgt["result"]] = labels.get(tgt["result"], 0) + 1
        if tgt["result"] == "human_review":
            hr[row.get("hr_subtype") or ""] = hr.get(row.get("hr_subtype") or "", 0) + 1
        user = row["messages"][1]["content"].split("Criterion:\n", 1)[-1][:48]
        print(f"{row['id']:10} {tgt['result']:16} {str(row.get('hr_subtype') or ''):22} {user}")
    if len(rows) > 24:
        print(f"... {len(rows) - 24} more")
    return rows


def inspect_ticket_rows(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else HERE / "data" / "tickets" / "train_v1.json"
    blob = json.loads(p.read_text(encoding="utf-8"))
    rows = blob.get("rows") or blob
    print("file:", p)
    print("n:", blob.get("n"), "security_share:", blob.get("security_share"), "injection_share:", blob.get("injection_share"))
    print(f"{'id':10} {'cat':22} {'inj':5} user")
    for row in rows[:16]:
        tgt = row.get("target_obj") or json.loads(row["target"])
        inj = "yes" if row.get("injected") else ""
        user = row["messages"][1]["content"].replace("\n", " ")[:52]
        print(f"{row['id']:10} {tgt['category']:22} {inj:5} {user}")
    if len(rows) > 16:
        print(f"... {len(rows) - 16} more")
    return rows


def show_failure(case_id: str = "R2-criteria") -> dict:
    """Print one teaching failure. Live pre-flight output wins; else the labelled CPU card."""
    E, RESUMES, TICKETS, MINUTES = _tasks()
    cards = {c["id"]: c for c in E.load_failure_cards().get("cards") or []}
    live_path = LOGS / "preflight_latest.json"
    live = json.loads(live_path.read_text(encoding="utf-8")) if live_path.is_file() else None
    card = cards.get(case_id)
    if card is None:
        raise KeyError(f"unknown failure card {case_id}; try R2-criteria, T1, M1")
    raw = card["raw"]
    source = card.get("source") or E.load_failure_cards().get("notice")
    if live and live.get("measured"):
        outs = live.get("outputs") or {}
        if case_id == "R2-criteria":
            raw = (outs.get("criteria_multi") or {}).get("R2") or raw
            source = "this session pre-flight (measured)"
        elif case_id in (outs.get("tickets") or {}):
            raw = outs["tickets"][case_id]
            source = "this session pre-flight (measured)"
        elif case_id in (outs.get("minutes") or {}):
            raw = outs["minutes"][case_id]
            source = "this session pre-flight (measured)"
    print("source:", source)
    print("scenario:", card["scenario"])
    print("--- input ---")
    print(card["input"])
    print("--- gold ---")
    print(card["gold"])
    print("--- raw output ---")
    print(raw)
    print("--- why ---")
    print(card["why_one_line"])
    print("--- cue ---")
    print(card["cue"])
    return {"id": case_id, "raw": raw, "source": source}


def _chat(system: str, user: str, max_tokens: int) -> dict:
    lab = _day1()
    choice = active_backend()
    if choice == "demo":
        return {"mode": "demo", "text": "", "error": "BACKEND=demo"}
    model = _day3_backend.get("model") or lab.resolve_model(choice)
    res = lab.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        timeout=60,
    )
    return res


def run_preflight(tasks: list[str] | None = None) -> dict:
    """Call the live base model on the frozen held-out set. Never reuse brief numbers."""
    E, RESUMES, TICKETS, MINUTES = _tasks()
    wanted = tasks or ["criteria", "tickets", "redaction", "minutes"]
    choice = active_backend()
    record = E.new_run_record(choice, measured=False)
    record["outputs"]["criteria_multi"] = {}
    if choice == "demo":
        print("BACKEND=demo — no live pre-flight. Showing labelled CPU cards is not this machine's baseline.")
        print("Set BACKEND='olmo' (or 'phi') with the Day 1 server up, then re-run.")
        path = LOGS / "preflight_latest.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", path)
        return record

    def take(kind, **payload):
        call = E.build_call(kind, **payload)
        res = _chat(call["system"], call["user"], call["max_tokens"])
        if res.get("mode") != "live":
            return None, res
        return res.get("text") or "", res

    live_ok = True
    if "criteria" in wanted:
        for item in E.criterion_items():
            text, res = take("criteria_one", item=item)
            if text is None:
                live_ok = False
                record["error"] = res.get("error") or res.get("mode")
                break
            record["outputs"]["criteria"][item["id"]] = text
        if live_ok:
            r2 = next(r for r in RESUMES if r["id"] == "R2")
            text, res = take("criteria_multi", resume=r2)
            if text is not None:
                record["outputs"]["criteria_multi"]["R2"] = text
    if live_ok and "tickets" in wanted:
        for case in TICKETS:
            text, res = take("ticket", case=case)
            if text is None:
                live_ok = False
                record["error"] = res.get("error") or res.get("mode")
                break
            record["outputs"]["tickets"][case["id"]] = text
    if live_ok and "redaction" in wanted:
        for doc in RESUMES:
            text, res = take("redaction", doc=doc)
            if text is None:
                live_ok = False
                record["error"] = res.get("error") or res.get("mode")
                break
            record["outputs"]["redaction"][doc["id"]] = text
    if live_ok and "minutes" in wanted:
        for case in MINUTES:
            text, res = take("minutes", case=case)
            if text is None:
                live_ok = False
                record["error"] = res.get("error") or res.get("mode")
                break
            record["outputs"]["minutes"][case["id"]] = text

    record["measured"] = live_ok and not record.get("error")
    scored = E.score_run(record) if record["measured"] else None
    record["metrics"] = {
        k: scored[k]
        for k in ("criteria_metrics", "ticket_metrics", "minutes_metrics", "redaction_metrics", "tripwires")
        if scored and scored.get(k) is not None
    } if scored else {}
    LOGS.mkdir(exist_ok=True)
    latest = LOGS / "preflight_latest.json"
    dated = LOGS / f"preflight_{record['date']}.json"
    latest.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    dated.write_text(latest.read_text(encoding="utf-8"), encoding="utf-8")
    print("saved", latest)
    print("measured:", record["measured"], "backend:", choice)
    if not record["measured"]:
        print("Live pre-flight did not finish:", record.get("error"))
        print("Use the labelled CPU cards for teaching. Do not paste the brief's percentages as this run.")
        return record
    print_preflight_metrics(record)
    return record


def print_preflight_metrics(record: dict | None = None) -> dict:
    E, *_ = _tasks()
    if record is None:
        path = LOGS / "preflight_latest.json"
        if not path.is_file():
            print("No preflight_latest.json. Run run_preflight() first.")
            return {}
        record = json.loads(path.read_text(encoding="utf-8"))
    if not record.get("measured"):
        print("This file is not a measured run for this machine.", NOT_SCORED)
        return record
    scored = E.score_run(record)
    for name, key in (
        ("criteria (one per call)", "criteria_metrics"),
        ("tickets", "ticket_metrics"),
        ("redaction stress (7 CVs)", "redaction_metrics"),
        ("minutes", "minutes_metrics"),
    ):
        m = scored.get(key)
        if not m:
            continue
        print(f"=== {name} ===")
        print(json.dumps(m, indent=2))
        if key == "criteria_metrics":
            E.print_confusion(m["confusion"])
    tw = scored["tripwires"]
    print("=== tripwires (this run only) ===")
    print(json.dumps(tw["tripped"], indent=2))
    for n in tw["notices"]:
        print("NOTICE:", n)
    return scored


def compare_criteria(base_record: dict, other_rows: list[dict], other_label: str = "other") -> dict:
    E, *_ = _tasks()
    base_scored = E.score_run(base_record) if "outputs" in base_record else base_record
    base_m = base_scored.get("criteria_metrics") or E.criteria_metrics(base_scored.get("criteria_rows") or [])
    other_m = E.criteria_metrics(other_rows)
    print("=== base ===")
    print(json.dumps(base_m, indent=2))
    E.print_confusion(base_m["confusion"])
    print(f"=== {other_label} ===")
    print(json.dumps(other_m, indent=2))
    E.print_confusion(other_m["confusion"])
    print("human_review recall: base", base_m.get("human_review_recall"), other_label, other_m.get("human_review_recall"))
    print(
        "human_review → does_not_meet (harmful): base",
        base_m.get("human_review_to_does_not_meet"),
        other_label,
        other_m.get("human_review_to_does_not_meet"),
    )
    return {"base": base_m, other_label: other_m}


def floor_from_preflight(record: dict | None = None) -> list[dict]:
    E, *_ = _tasks()
    if record is None:
        path = LOGS / "preflight_latest.json"
        if not path.is_file():
            print("No measured pre-flight. Floor needs base outputs.")
            return []
        record = json.loads(path.read_text(encoding="utf-8"))
    if not record.get("measured"):
        print("No measured base outputs.", NOT_SCORED)
        return []
    scored = E.score_run(record)
    floored = E.apply_evidence_floor(scored["criteria_rows"])
    print("Rule floor: if evidence is not a résumé substring, force human_review.")
    print(json.dumps(E.criteria_metrics(floored), indent=2))
    return floored


def regex_redaction_floor(text: str) -> str:
    """Emails and phones only — the simplest comparison, not a redactor."""
    import re

    out = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    out = re.sub(r"(?:\+1\s*)?(?:868[\s.-]*)?555[\s.-]*\d{4}", "[PHONE]", out)
    return out


def print_redaction_floor(doc_id: str = "R2") -> None:
    E, RESUMES, *_ = _tasks()
    doc = next(r for r in RESUMES if r["id"] == doc_id)
    floored = regex_redaction_floor(doc["text"])
    sc = E.score_redaction(doc, floored)
    print("regex floor on", doc_id, "(emails and 868-555 phones only)")
    print(floored)
    print("leaked spans:", sc["n_leaked"], "of", sc["n_spans"], "keep lost:", sc["keep_lost"])


def still_wrong_criteria(record: dict | None = None, n: int = 3) -> list[dict]:
    E, *_ = _tasks()
    if record is None:
        path = LOGS / "preflight_latest.json"
        if not path.is_file():
            print("No pre-flight file.")
            return []
        record = json.loads(path.read_text(encoding="utf-8"))
    if not record.get("measured"):
        print("No measured rows. List three cases from the teaching cards instead.")
        return []
    scored = E.score_run(record)
    wrong = [r for r in scored["criteria_rows"] if not r["correct"]]
    print(f"{len(wrong)} incorrect of {len(scored['criteria_rows'])}")
    for row in wrong[:n]:
        print(f"  {row['id']}  gold={row['gold']} pred={row['pred']} harmful={row['harmful']}")
        print(f"    evidence={row['evidence'][:80]!r}")
    return wrong[:n]


def policy_line() -> None:
    print("AI assists. HR validates. Authorized officers decide.")
    print("A better human_review rate makes the human's queue more accurate. It does not remove the human.")

