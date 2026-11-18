"""Live Day 3 LoRA training and in-process base-vs-adapter comparison.

Learners call TrainSession / load_adapter / compare_live. They do not write training loops.
Base vs adapter uses PeftModel.disable_adapter() on the same weights — not the :8000 server.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
LOGS = HERE / "logs"
ADAPTERS = HERE / "adapters"
SHARED = (HERE.parent / "shared" / "resume_redaction").resolve()
RR_DATA = SHARED / "data"
RR_BASE = SHARED / "baselines"

OLMO_ID = "allenai/OLMo-2-0425-1B-Instruct"
OLMO_REV = "48d788eca847d4d7548f375ad03d3c9312f6139e"
DEFAULT_MODEL_DIR = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models")) / "olmo"

TASK_PATHS = {
    "criteria": {
        "train": DATA / "criteria" / "train_v1.json",
        "val": DATA / "criteria" / "val_v1.json",
        "prebuilt": ADAPTERS / "olmo-criteria-lora-v1",
    },
    "tickets": {
        "train": DATA / "tickets" / "train_v1.json",
        "val": DATA / "tickets" / "val_v1.json",
        "prebuilt": ADAPTERS / "olmo-tickets-lora-v1",
    },
    "redact": {
        "train": RR_DATA / "train_clean_v1.json",
        "val": RR_DATA / "val_v1.json",
        "prebuilt": ADAPTERS / "olmo-resume-redact-lora-v1",
    },
}

_SESSIONS: dict[str, "TrainSession"] = {}
_LOADED: dict[str, Any] = {}


def _tasks():
    import sys

    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    from heldout import eval_tasks as E
    from heldout.cases import MINUTES, RESUMES, TICKETS

    return E, RESUMES, TICKETS, MINUTES


def _gpu_free_gb() -> float | None:
    try:
        import torch

        if not torch.cuda.is_available():
            return None
        free, total = torch.cuda.mem_get_info()
        return free / (1024**3)
    except Exception:
        return None


def print_gpu_memory() -> None:
    free = _gpu_free_gb()
    if free is None:
        print("GPU memory: no CUDA device visible.")
        return
    print(f"GPU memory free: {free:.2f} GB")
    if free < 4.0:
        print("WARNING: less than 4 GB free. The Day 1 server may already hold OLMo on this GPU.")


def _resolve_model_dir() -> Path:
    for p in (
        DEFAULT_MODEL_DIR,
        Path("/models/olmo"),
        HERE.parent / "day1" / "models" / "olmo",
    ):
        if (p / "config.json").is_file():
            return p
    return DEFAULT_MODEL_DIR


def _load_rows(path: Path) -> tuple[list[dict], str]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    rows = blob.get("rows") or blob
    sha = blob.get("sha256") or ""
    return rows, sha


def _row_texts(row: dict) -> tuple[list[dict], str]:
    """Return (messages without target, target string)."""
    if "messages" in row and "target" in row:
        msgs = list(row["messages"])
        return msgs, row["target"] if isinstance(row["target"], str) else json.dumps(row["target"])
    # redaction format: system + user résumé, target is redacted text
    if "messages" in row and "target" not in row and row.get("target_text"):
        return list(row["messages"]), row["target_text"]
    raise ValueError(f"unrecognised row shape: {row.get('id')}")


def _encode_supervised(tok, messages: list[dict], target: str, max_len: int):
    import torch

    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    full = prompt + target + (tok.eos_token or "")
    prompt_ids = tok(prompt, add_special_tokens=False)["input_ids"]
    full_ids = tok(full, add_special_tokens=False, truncation=True, max_length=max_len)["input_ids"]
    labels = list(full_ids)
    cut = min(len(prompt_ids), len(labels))
    for i in range(cut):
        labels[i] = -100
    return {
        "input_ids": torch.tensor([full_ids]),
        "labels": torch.tensor([labels]),
        "attention_mask": torch.tensor([[1] * len(full_ids)]),
    }


class TrainSession:
    """Stateful LoRA training. Rerunning step() continues; it never restarts the session."""

    def __init__(
        self,
        task: str = "criteria",
        targets: list[str] | None = None,
        rank: int = 8,
        alpha: int = 16,
        lr: float = 2e-4,
        micro_batch: int = 1,
        grad_accum: int = 4,
        max_len: int = 768,
        seed: int = 0,
        dropout: float = 0.05,
    ):
        if task not in TASK_PATHS:
            raise ValueError(f'task must be one of {sorted(TASK_PATHS)}')
        key = f"{task}:{','.join(targets or ['q_proj', 'v_proj'])}:r{rank}:s{seed}"
        existing = _SESSIONS.get(key)
        if existing is not None:
            print(f"Reusing existing TrainSession for {task} (already at update {existing.n_updates}).")
            self.__dict__ = existing.__dict__
            return

        try:
            import torch
            from peft import LoraConfig, TaskType, get_peft_model
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                f"Cannot train: missing dependency ({exc}). "
                "Install peft/transformers/torch in the course image, or use BACKEND=demo + RECORDED runs."
            ) from exc

        if not torch.cuda.is_available():
            raise RuntimeError(
                "No GPU. TrainSession needs CUDA. "
                "Section 6 will skip; Section 7 can load a RECORDED run or a prebuilt adapter on GPU later."
            )

        print_gpu_memory()
        free = _gpu_free_gb()
        if free is not None and free < 3.5:
            print("WARNING: Day 1 server may already hold a copy of OLMo on this GPU.")

        self.task = task
        self.targets = list(targets or ["q_proj", "v_proj"])
        self.rank = int(rank)
        self.alpha = int(alpha)
        self.lr = float(lr)
        self.micro_batch = int(micro_batch)
        self.grad_accum = int(grad_accum)
        self.max_len = int(max_len)
        self.seed = int(seed)
        self.dropout = float(dropout)
        self.n_updates = 0
        self.history_rows: list[dict] = []
        self.model_dir = _resolve_model_dir()
        paths = TASK_PATHS[task]
        self.train_rows, self.train_sha = _load_rows(paths["train"])
        self.val_rows, self.val_sha = _load_rows(paths["val"])
        self.train_path = paths["train"]
        self.val_path = paths["val"]

        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)

        if torch.cuda.is_bf16_supported():
            self.dtype = torch.bfloat16
            self.precision = "bf16"
        else:
            self.dtype = torch.float16
            self.precision = "fp16"
        print(f"precision chosen: {self.precision} (bf16_supported={torch.cuda.is_bf16_supported()})")

        print("loading tokenizer + base from", self.model_dir)
        self.tok = AutoTokenizer.from_pretrained(str(self.model_dir), trust_remote_code=True)
        if self.tok.pad_token_id is None:
            self.tok.pad_token = self.tok.eos_token
        try:
            base = AutoModelForCausalLM.from_pretrained(
                str(self.model_dir), dtype=self.dtype, device_map="auto", low_cpu_mem_usage=True
            )
        except TypeError:
            base = AutoModelForCausalLM.from_pretrained(
                str(self.model_dir), torch_dtype=self.dtype, device_map="auto", low_cpu_mem_usage=True
            )
        base.train()
        lora = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.rank,
            lora_alpha=self.alpha,
            lora_dropout=self.dropout,
            target_modules=self.targets,
            bias="none",
        )
        self.model = get_peft_model(base, lora)
        self.optimizer = torch.optim.AdamW(
            [p for p in self.model.parameters() if p.requires_grad], lr=self.lr
        )
        self._data_i = 0
        self._probe_name, self._probe_param = self._pick_probe()
        self._encoded_train = [self._encode(r) for r in self.train_rows]
        self._encoded_val = [self._encode(r) for r in self.val_rows]
        self.started = time.time()
        self.gpu_name = torch.cuda.get_device_name(0)
        _SESSIONS[key] = self
        print(f"TrainSession ready: task={task} rows={len(self.train_rows)} val={len(self.val_rows)}")

    def _encode(self, row: dict):
        msgs, target = _row_texts(row)
        return _encode_supervised(self.tok, msgs, target, self.max_len)

    def _pick_probe(self):
        for name, p in self.model.named_parameters():
            if p.requires_grad and "lora_A" in name:
                return name, p
        for name, p in self.model.named_parameters():
            if p.requires_grad:
                return name, p
        return None, None

    def summary(self) -> dict:
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        print("=== TrainSession summary ===")
        print("base:", OLMO_ID, "revision", OLMO_REV)
        print("path:", self.model_dir)
        print("precision:", self.precision)
        print("GPU:", self.gpu_name)
        print(f"trainable: {trainable:,} / {total:,}")
        try:
            self.model.print_trainable_parameters()
        except Exception:
            pass
        print("T1-11 estimate for q_proj,v_proj r=8: 1,048,576")
        print("dataset:", self.train_path)
        print("train sha256:", self.train_sha)
        print("val sha256:", self.val_sha)
        print(
            f"hyper: targets={self.targets} rank={self.rank} alpha={self.alpha} "
            f"lr={self.lr} micro_batch={self.micro_batch} grad_accum={self.grad_accum} max_len={self.max_len}"
        )
        print("updates so far:", self.n_updates)
        return {
            "trainable": trainable,
            "total": total,
            "precision": self.precision,
            "train_sha": self.train_sha,
            "n_updates": self.n_updates,
        }

    def show_example(self, i: int = 0) -> None:
        row = self.train_rows[i % len(self.train_rows)]
        msgs, target = _row_texts(row)
        enc = self._encoded_train[i % len(self._encoded_train)]
        ids = enc["input_ids"][0].tolist()
        labels = enc["labels"][0].tolist()
        answer_start = next((j for j, lab in enumerate(labels) if lab != -100), len(labels))
        print(f"example {row.get('id')} (index {i})")
        print("--- prompt (loss masked) ---")
        print(self.tok.decode(ids[:answer_start], skip_special_tokens=False)[:800])
        print("--- answer starts here (loss counted) ---")
        print(self.tok.decode([t for t in ids[answer_start:] if t >= 0], skip_special_tokens=False)[:400])
        print(f"prompt tokens: {answer_start}  answer tokens: {len(ids) - answer_start}")
        print("gold target:", target[:200])

    def step(self, n: int = 1) -> list[dict]:
        import torch

        self.model.train()
        out = []
        for _ in range(int(n)):
            self.optimizer.zero_grad(set_to_none=True)
            t0 = time.perf_counter()
            if self._probe_param is not None:
                before = self._probe_param.detach().float().norm().item()
            else:
                before = 0.0
            losses = []
            for micro in range(self.grad_accum):
                batch = self._encoded_train[self._data_i % len(self._encoded_train)]
                self._data_i += 1
                batch = {k: v.to(self.model.device) for k, v in batch.items()}
                loss = self.model(**batch).loss / self.grad_accum
                loss.backward()
                losses.append(float(loss.detach()) * self.grad_accum)
            torch.nn.utils.clip_grad_norm_(
                [p for p in self.model.parameters() if p.requires_grad], 1.0
            )
            self.optimizer.step()
            self.n_updates += 1
            after = self._probe_param.detach().float().norm().item() if self._probe_param is not None else 0.0
            delta = abs(after - before)
            elapsed = time.perf_counter() - t0
            peak = torch.cuda.max_memory_allocated() / (1024**2)
            row = {
                "update": self.n_updates,
                "train_loss": round(sum(losses) / len(losses), 4),
                "weight_change": round(delta, 6),
                "probe": self._probe_name,
                "micro_batches": self.grad_accum,
                "elapsed_s": round(elapsed, 2),
                "peak_mem_mb": round(peak, 1),
            }
            self.history_rows.append(row)
            out.append(row)
            print(
                f"update {row['update']}: train_loss={row['train_loss']}  "
                f"weight_change({row['probe']})={row['weight_change']}  "
                f"micro_batches={row['micro_batches']}  "
                f"{row['elapsed_s']}s  peak_mem={row['peak_mem_mb']}MB"
            )
        return out

    def validate(self) -> float:
        import torch

        self.model.eval()
        total = 0.0
        with torch.no_grad():
            for batch in self._encoded_val:
                batch = {k: v.to(self.model.device) for k, v in batch.items()}
                total += float(self.model(**batch).loss.detach())
        val = total / max(len(self._encoded_val), 1)
        print(f"validation loss: {val:.4f}  (no weight updates; not the same as task accuracy)")
        self.last_val_loss = val
        return val

    def history(self) -> None:
        if not self.history_rows:
            print("No updates yet. Run session.step(1) first.")
            return
        print(f"{'update':>8}  {'train_loss':>12}  {'weight_change':>14}")
        for row in self.history_rows:
            print(f"{row['update']:8d}  {row['train_loss']:12.4f}  {row['weight_change']:14.6f}")
        try:
            import matplotlib.pyplot as plt

            xs = [r["update"] for r in self.history_rows]
            ys = [r["train_loss"] for r in self.history_rows]
            plt.figure(figsize=(5, 3))
            plt.plot(xs, ys, marker="o")
            plt.xlabel("update")
            plt.ylabel("train loss")
            plt.title(f"{self.task} LoRA — losses can go up as well as down")
            plt.tight_layout()
            plt.show()
        except Exception as exc:
            print("(plot skipped:", exc, ")")

    def save(self, out_dir: str | Path) -> Path:
        out = Path(out_dir)
        if not out.is_absolute():
            out = HERE / out
        out.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(str(out))
        self.tok.save_pretrained(str(out))
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        last_train = self.history_rows[-1]["train_loss"] if self.history_rows else None
        report = {
            "status": "trained",
            "measured": True,
            "adapter_name": out.name,
            "task": self.task,
            "base_model": OLMO_ID,
            "base_revision": OLMO_REV,
            "base_path": str(self.model_dir),
            "rank": self.rank,
            "alpha": self.alpha,
            "targets": self.targets,
            "lr": self.lr,
            "micro_batch": self.micro_batch,
            "grad_accum": self.grad_accum,
            "max_len": self.max_len,
            "seed": self.seed,
            "precision": self.precision,
            "trainable_count": trainable,
            "n_updates": self.n_updates,
            "last_train_loss": last_train,
            "last_val_loss": getattr(self, "last_val_loss", None),
            "training_data_version": self.train_path.name,
            "training_sha256": self.train_sha,
            "validation_sha256": self.val_sha,
            "gpu": self.gpu_name,
            "wall_s": round(time.time() - self.started, 1),
            "date": date.today().isoformat(),
            "history": self.history_rows,
        }
        (out / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        last = {"adapter": str(out.relative_to(HERE)).replace("\\", "/"), "task": self.task, "date": report["date"]}
        LOGS.mkdir(exist_ok=True)
        (LOGS / "last_adapter.json").write_text(json.dumps(last, indent=2), encoding="utf-8")
        print("saved adapter to", out)
        for p in sorted(out.iterdir()):
            print(" ", p.name, f"({p.stat().st_size} bytes)" if p.is_file() else "")
        print("wrote", LOGS / "last_adapter.json")
        print("Files: adapter_config.json + weights = the LoRA; training_report.json = what was measured.")
        return out


def resolve_adapter_path(path_or_prebuilt: str, task: str) -> Path:
    raw = (path_or_prebuilt or "prebuilt").strip()
    if raw.lower() in {"prebuilt", "instructor", "baked"}:
        path = TASK_PATHS[task]["prebuilt"]
    else:
        path = Path(raw)
        if not path.is_absolute():
            path = HERE / path
    return path


def load_adapter(path_or_prebuilt: str = "prebuilt", task: str = "criteria"):
    """Load base once and apply adapter. Prints which adapter and its training_report."""
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(f"Cannot load adapter: {exc}") from exc

    path = resolve_adapter_path(path_or_prebuilt, task)
    print_gpu_memory()
    if not path.is_dir():
        raise FileNotFoundError(
            f"No adapter at {path}. Train in T1-11 (session.save) or bake the prebuilt folder on a GPU."
        )
    report_path = path / "training_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    print("loading adapter from", path)
    print("which:", "prebuilt" if "olmo-" in path.name and "my_" not in path.name else "learner run")
    if report:
        print("--- training_report.json ---")
        for k in (
            "status",
            "measured",
            "task",
            "base_model",
            "base_revision",
            "rank",
            "targets",
            "n_updates",
            "last_train_loss",
            "last_val_loss",
            "gpu",
            "date",
        ):
            if k in report:
                print(f"  {k}: {report[k]}")

    cache_key = str(path.resolve())
    if cache_key in _LOADED:
        print("reusing in-memory model for", path.name)
        return _LOADED[cache_key]

    if not torch.cuda.is_available():
        raise RuntimeError("load_adapter needs a GPU for OLMo-1B. Use a RECORDED run on CPU demos.")

    model_dir = _resolve_model_dir()
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    tok = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
    try:
        base = AutoModelForCausalLM.from_pretrained(
            str(model_dir), dtype=dtype, device_map="auto", low_cpu_mem_usage=True
        )
    except TypeError:
        base = AutoModelForCausalLM.from_pretrained(
            str(model_dir), torch_dtype=dtype, device_map="auto", low_cpu_mem_usage=True
        )
    model = PeftModel.from_pretrained(base, str(path))
    model.eval()
    bundle = {"model": model, "tok": tok, "path": path, "report": report, "task": task}
    _LOADED[cache_key] = bundle
    return bundle


def _generate(bundle: dict, system: str, user: str, max_tokens: int) -> str:
    import torch

    tok = bundle["tok"]
    model = bundle["model"]
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            pad_token_id=tok.pad_token_id or tok.eos_token_id,
        )
    new = out[0, inputs["input_ids"].shape[-1] :]
    return tok.decode(new, skip_special_tokens=True)


def _heldout_cases(task: str, case_ids: list[str] | None):
    E, RESUMES, TICKETS, MINUTES = _tasks()
    if task == "criteria":
        items = E.criterion_items()
        if case_ids:
            want = set(case_ids)
            items = [i for i in items if i["id"] in want]
        return [("criteria_one", i["id"], E.build_call("criteria_one", item=i), i) for i in items]
    if task == "tickets":
        cases = TICKETS
        if case_ids:
            want = set(case_ids)
            cases = [c for c in cases if c["id"] in want]
        return [("ticket", c["id"], E.build_call("ticket", case=c), c) for c in cases]
    if task == "redact":
        # 7-CV stress slice from heldout; full 40-doc uses redaction_eval separately
        docs = RESUMES
        if case_ids:
            want = set(case_ids)
            docs = [d for d in docs if d["id"] in want]
        return [("redaction", d["id"], E.build_call("redaction", doc=d), d) for d in docs]
    if task == "minutes":
        cases = MINUTES
        if case_ids:
            want = set(case_ids)
            cases = [c for c in cases if c["id"] in want]
        return [("minutes", c["id"], E.build_call("minutes", case=c), c) for c in cases]
    raise ValueError(task)


def compare_live(bundle: dict, task: str, case_ids: list[str] | None = None) -> dict:
    """Run each held-out case twice on the same weights: disable_adapter (base) vs adapter on."""
    E, *_ = _tasks()
    model = bundle["model"]
    cases = _heldout_cases(task, case_ids)
    print("LIVE, this session")
    print(f"adapter: {bundle['path']}")
    print(f"cases: {len(cases)}  task: {task}")
    rows = []
    for kind, cid, call, meta in cases:
        system, user, max_tokens = call["system"], call["user"], call["max_tokens"]
        with model.disable_adapter():
            base_text = _generate(bundle, system, user, max_tokens)
        ad_text = _generate(bundle, system, user, max_tokens)
        gold = None
        if task == "criteria":
            gold = meta["gold"]
            base_sc = E.score_one_criterion(meta, base_text)
            ad_sc = E.score_one_criterion(meta, ad_text)
        elif task == "tickets":
            gold = meta["gold"]
            base_sc = E.score_ticket(meta, base_text)
            ad_sc = E.score_ticket(meta, ad_text)
        elif task == "redact":
            gold = "(redacted résumé)"
            base_sc = E.score_redaction(meta, base_text)
            ad_sc = E.score_redaction(meta, ad_text)
        else:
            gold = meta.get("gold_actions")
            base_sc = E.score_minutes(meta, base_text)
            ad_sc = E.score_minutes(meta, ad_text)
        print("=" * 60, cid)
        print("gold:", gold)
        print("--- base (disable_adapter) ---")
        print(base_text[:500])
        print("--- adapter ---")
        print(ad_text[:500])
        print("scores: base", {k: base_sc.get(k) for k in list(base_sc) if k != "raw"})
        print("        adapter", {k: ad_sc.get(k) for k in list(ad_sc) if k != "raw"})
        rows.append(
            {
                "id": cid,
                "gold": gold,
                "base": base_text,
                "adapter": ad_text,
                "base_score": {k: v for k, v in base_sc.items() if k != "raw"},
                "adapter_score": {k: v for k, v in ad_sc.items() if k != "raw"},
            }
        )
    result = {
        "label": "LIVE, this session",
        "task": task,
        "adapter": str(bundle["path"]),
        "date": date.today().isoformat(),
        "rows": rows,
    }
    LOGS.mkdir(exist_ok=True)
    out = LOGS / f"live_{task}_compare.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved", out)
    return result


def load_recorded(task: str) -> dict:
    path = LOGS / "recorded" / f"{task}_compare_v1.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"No recorded run at {path}. Instructor bake on a T4 writes this file (Part B2)."
        )
    blob = json.loads(path.read_text(encoding="utf-8"))
    when = blob.get("date") or "unknown date"
    gpu = blob.get("gpu") or "unknown GPU"
    print(f"RECORDED run from {when} on {gpu}, not this session.")
    return blob


def criteria_scoreboard(compare: dict) -> dict:
    """Three-row board: base, base+floor, adapter."""
    E, *_ = _tasks()
    base_rows = []
    ad_rows = []
    by_item = {i["id"]: i for i in E.criterion_items()}
    for row in compare["rows"]:
        item = by_item[row["id"]]
        base_rows.append(E.score_one_criterion(item, row["base"]))
        ad_rows.append(E.score_one_criterion(item, row["adapter"]))
    floor_rows = E.apply_evidence_floor(base_rows)
    ad_floor = E.apply_evidence_floor(ad_rows)

    def pack(rows, name):
        m = E.criteria_metrics(rows)
        silence_bad = sum(1 for r in rows if r["harmful"])
        meets_bad_ev = sum(
            1
            for r in rows
            if r.get("pred") == "meets" and not r.get("evidence_verbatim")
        )
        return {
            "row": name,
            "json_valid_rate": m["json_valid_rate"],
            "label_agreement": m["accuracy"],
            "silence_to_does_not_meet": silence_bad,
            "meets_evidence_not_in_resume": meets_bad_ev,
        }

    board = [
        pack(base_rows, "base"),
        pack(floor_rows, "base + evidence floor"),
        pack(ad_rows, "adapter"),
        pack(ad_floor, "adapter + evidence floor"),
    ]
    print("=== criteria scoreboard (18 items from 7 résumés — direction, not proof) ===")
    print(
        f"{'row':28} {'json_ok':>8} {'agree':>8} {'silence→DNM':>12} {'meets!ev':>10}"
    )
    for b in board:
        print(
            f"{b['row']:28} {b['json_valid_rate']:8.2%} {b['label_agreement']:8.2%} "
            f"{b['silence_to_does_not_meet']:12d} {b['meets_evidence_not_in_resume']:10d}"
        )
    print("json_ok = share of valid JSON. agree = label matches gold.")
    print("silence→DNM = human_review gold predicted does_not_meet (harmful).")
    print("meets!ev = predicted meets but evidence is not a résumé substring.")
    return {"board": board, "label": compare.get("label")}


def ticket_scoreboard(compare: dict) -> dict:
    E, *_ = _tasks()
    from heldout.cases import TICKETS

    by = {t["id"]: t for t in TICKETS}
    base_rows = [E.score_ticket(by[r["id"]], r["base"]) for r in compare["rows"]]
    ad_rows = [E.score_ticket(by[r["id"]], r["adapter"]) for r in compare["rows"]]

    def pack(rows, name):
        m = E.ticket_metrics(rows)
        inj = [r for r in rows if r.get("injected")]
        inj_obey = sum(
            1
            for r in inj
            if r["pred"]["category"] == "other" or r["pred"]["action"] == "self_help_article"
        )
        return {
            "row": name,
            "json_valid_rate": m["json_valid_rate"],
            "category_accuracy": m["category_accuracy"],
            "security_escalated": f"{m['security_escalated_count']}/{m['security_gold']}",
            "injection_obeyed_bad": inj_obey,
            "metrics": m,
        }

    board = [pack(base_rows, "base"), pack(ad_rows, "adapter")]
    print("=== tickets scoreboard ===")
    for b in board:
        print(
            f"{b['row']}: json_ok={b['json_valid_rate']:.2%}  "
            f"category={b['category_accuracy']:.2%}  "
            f"security_escalated={b['security_escalated']}  "
            f"injection_obeyed_bad_instruction={b['injection_obeyed_bad']}"
        )
    return {"board": board, "label": compare.get("label")}
