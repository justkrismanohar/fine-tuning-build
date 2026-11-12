"""Tiny OpenAI-compatible server using Hugging Face transformers.

Used by: python build_llms.py serve --engine hf
Not the classroom default (that is vLLM). Fine for a from-scratch smoke test
when vLLM is not installed. CPU will be slow.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load(model_id: str):
    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )
    if not torch.cuda.is_available():
        model = model.to("cpu")
    model.eval()
    return tok, model


def generate(tok, model, messages: list[dict], max_tokens: int = 256) -> str:
    if hasattr(tok, "apply_chat_template"):
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        text = "\n".join(m.get("content", "") for m in messages) + "\n"
    inputs = tok(text, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    new_tokens = out[0, inputs["input_ids"].shape[-1] :]
    return tok.decode(new_tokens, skip_special_tokens=True)


def make_handler(model_id: str, tok, model):
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
                self._send(200, {"ok": True, "model": model_id})
                return
            self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._send(404, {"error": "not found"})
                return
            messages = body.get("messages") or []
            max_tokens = int(body.get("max_tokens") or 256)
            text = generate(tok, model, messages, max_tokens=max_tokens)
            self._send(
                200,
                {
                    "id": "hf-civicdesk",
                    "object": "chat.completion",
                    "model": body.get("model") or model_id,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                },
            )

    return H


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="0.0.0.0")
    args = p.parse_args()
    print("loading", args.model)
    tok, model = load(args.model)
    print("serving on", args.host, args.port)
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(args.model, tok, model))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
