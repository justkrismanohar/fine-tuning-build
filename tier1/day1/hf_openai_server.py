"""Tiny OpenAI-compatible server using Hugging Face transformers.

Used by: python build_llms.py serve --engine hf
Also used by the course container (docker-entrypoint) for OLMo/Phi on CPU.

Token counts come from the IDs passed to generate, not from re-tokenizing decoded text.
Temperature > 0 turns sampling on (T1-02). Temperature 0 / omitted stays greedy (T1-03).
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

COUNTING_CONVENTION = (
    "prompt_tokens = length of the exact input_ids passed to generate (chat template applied by this "
    "model's tokenizer, system text, role markers and generation prompt included, batch size 1, no padding). "
    "completion_tokens = newly generated token IDs after the prompt, up to and including the first EOS id; "
    "anything after it is not counted."
)
_GEN_LOCK = threading.Lock()


def _from_pretrained(model_id: str, dtype, trust_remote_code: bool, **extra):
    """dtype= is transformers 4.51+; older wheels still want torch_dtype=."""
    kwargs = dict(trust_remote_code=trust_remote_code, **extra)
    try:
        return AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype, **kwargs)
    except TypeError:
        return AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype, **kwargs)


def load(model_id: str):
    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    dtype = torch.float16 if torch.cuda.is_available() else getattr(
        torch, os.environ.get("CIVICDESK_CPU_DTYPE", "float32")
    )
    extra = {
        "device_map": "auto" if torch.cuda.is_available() else None,
        "low_cpu_mem_usage": True,
    }
    # Phi-4-mini's Hub modeling_phi3.py imports LossKwargs from transformers.utils.
    # That name was removed in transformers 4.54+. The in-library Phi3 class loads
    # the same /models/phi weights. Try that first; keep remote code as fallback.
    try:
        model = _from_pretrained(model_id, dtype, trust_remote_code=False, **extra)
        print("loaded in-library architecture (trust_remote_code=False)")
    except Exception as exc:
        print("in-library load failed:", type(exc).__name__, exc)
        print("retrying with trust_remote_code=True")
        model = _from_pretrained(model_id, dtype, trust_remote_code=True, **extra)
    if not torch.cuda.is_available():
        model = model.to("cpu")
    model.eval()
    return tok, model


def _eos_ids(tok, model) -> set[int]:
    ids: set[int] = set()
    gc = getattr(model, "generation_config", None)
    e = getattr(gc, "eos_token_id", None) if gc is not None else None
    for v in e if isinstance(e, (list, tuple)) else [e]:
        if v is not None:
            ids.add(int(v))
    if tok.eos_token_id is not None:
        ids.add(int(tok.eos_token_id))
    return ids


def _revision(path: str) -> str:
    f = Path(path) / "CIVICDESK_REVISION.txt"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else "unknown (not pinned)"


def _encode_prompt(tok, messages: list[dict]):
    """Tokenize the chat once. Batch size stays 1: no padding, so no pad tokens are counted.
    If anyone later batches requests, count each row with its attention mask and padding side,
    not the padded tensor width.
    """
    if hasattr(tok, "apply_chat_template"):
        try:
            enc = tok.apply_chat_template(
                messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
            )
            if isinstance(enc, dict) or hasattr(enc, "keys"):
                return {k: enc[k] for k in enc}
        except TypeError:
            pass
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return tok(text, return_tensors="pt", add_special_tokens=False)
    text = "\n".join(m.get("content", "") for m in messages) + "\n"
    return tok(text, return_tensors="pt", add_special_tokens=False)


def generate(
    tok,
    model,
    messages: list[dict],
    max_tokens: int = 256,
    temperature: float | None = None,
    top_p: float | None = None,
    seed: int | None = None,
):
    enc = _encode_prompt(tok, messages)
    inputs = {k: v.to(model.device) for k, v in enc.items()}
    prompt_len = int(inputs["input_ids"].shape[-1])
    eos = _eos_ids(tok, model)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    do_sample = temperature is not None and float(temperature) > 0
    gen_kwargs: dict = {
        "max_new_tokens": max_tokens,
        "do_sample": do_sample,
        "pad_token_id": pad,
        "eos_token_id": sorted(eos) if eos else tok.eos_token_id,
    }
    if do_sample:
        gen_kwargs["temperature"] = float(temperature)
        gen_kwargs["top_p"] = top_p if top_p is not None else 1.0
        gen_kwargs["top_k"] = 0
    if seed is not None:
        torch.manual_seed(int(seed))
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(int(seed))
    with _GEN_LOCK, torch.no_grad():
        t0 = time.perf_counter()
        out = model.generate(**inputs, **gen_kwargs)
        gen_ms = (time.perf_counter() - t0) * 1000
    new = out[0, prompt_len:].tolist()
    stop_at = next((i for i, t in enumerate(new) if t in eos), None)
    counted = new[: stop_at + 1] if stop_at is not None else new
    finish = "stop" if stop_at is not None else ("length" if len(new) >= max_tokens else "stop")
    decoded = tok.decode(counted, skip_special_tokens=True)
    info = {
        "engine": "hf",
        "do_sample": do_sample,
        "temperature": float(temperature) if do_sample else None,
        "top_p": (top_p if top_p is not None else 1.0) if do_sample else None,
        "top_k": 0 if do_sample else None,
        "seed": int(seed) if seed is not None else None,
        "max_tokens": int(max_tokens),
        "generation_ms": round(gen_ms, 1),
        "eos_included": stop_at is not None,
        "decoding": (
            f"temperature={temperature}, do_sample=True"
            if do_sample
            else "greedy (do_sample=False); temperature ignored"
        ),
        "counting_convention": COUNTING_CONVENTION,
    }
    usage = {
        "prompt_tokens": prompt_len,
        "completion_tokens": len(counted),
        "total_tokens": prompt_len + len(counted),
    }
    return decoded, info, usage, finish


def _opt_float(body: dict, key: str):
    if key not in body or body[key] is None:
        return None
    try:
        return float(body[key])
    except (TypeError, ValueError):
        return "bad"


def _opt_int(body: dict, key: str):
    if key not in body or body[key] is None:
        return None
    try:
        return int(body[key])
    except (TypeError, ValueError):
        return "bad"


def make_handler(model_id: str, tok, model):
    meta = {
        "model_path": model_id,
        "revision": _revision(model_id),
        "device": str(model.device),
        "dtype": str(next(model.parameters()).dtype),
        "decoding": "greedy (do_sample=False); temperature ignored unless temperature > 0",
        "counting_convention": COUNTING_CONVENTION,
        "engine": "hf",
    }

    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(self.address_string(), "-", fmt % args)

        def _send(self, code: int, payload: dict):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path.rstrip("/").endswith("/models") or self.path.endswith("/v1/models"):
                self._send(200, {"data": [{"id": model_id, "object": "model"}]})
                return
            if self.path.rstrip("/").endswith("/health"):
                self._send(200, {"ok": True, "model": model_id, "civicdesk": meta})
                return
            self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._send(404, {"error": "not found"})
                return
            try:
                max_tokens = int(body.get("max_tokens") or 256)
            except (TypeError, ValueError):
                self._send(400, {"error": "malformed max_tokens"})
                return
            temperature = _opt_float(body, "temperature")
            top_p = _opt_float(body, "top_p")
            seed = _opt_int(body, "seed")
            if temperature == "bad":
                self._send(400, {"error": "malformed temperature"})
                return
            if top_p == "bad":
                self._send(400, {"error": "malformed top_p"})
                return
            if seed == "bad":
                self._send(400, {"error": "malformed seed"})
                return
            text, info, usage, finish = generate(
                tok,
                model,
                body.get("messages") or [],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                seed=seed,
            )
            usage_civic = {**meta, **{k: info[k] for k in ("generation_ms", "eos_included", "decoding")}}
            usage = {**usage, "civicdesk": usage_civic}
            self._send(
                200,
                {
                    "id": "hf-civicdesk",
                    "object": "chat.completion",
                    "model": body.get("model") or model_id,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": text},
                            "finish_reason": finish,
                        }
                    ],
                    "usage": usage,
                    "civicdesk": info,
                },
            )

    return H


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--adapter", default="", help="optional LoRA directory; omit for the Day 1 base path")
    p.add_argument("--served-name", default="", help="id returned by /v1/models when an adapter is loaded")
    args = p.parse_args()
    print("loading", args.model)
    tok, model = load(args.model)
    served = args.served_name or args.model
    if args.adapter:
        from peft import PeftModel

        print("applying adapter", args.adapter, "as", served)
        model = PeftModel.from_pretrained(model, args.adapter)
        model.eval()
    print("serving on", args.host, args.port)
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(served, tok, model))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
