"""Optional hosted-API comparison for T1-03. Fictional CivicDesk data only.

Keys come from an environment variable or a masked getpass prompt, live only in this
process, and are never printed, saved, logged or written to notebook output.
"""

from __future__ import annotations

import getpass
import json
import os
import time
import urllib.error
import urllib.request

# Checked against each provider's own docs on 2026-11-12. Re-check before class.
PROVIDERS = {
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "alt_key_env": "GOOGLE_API_KEY",
        "default_model": "gemini-3.5-flash-lite",
        "model_kind": "proprietary (Google Gemini)",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-20b",
        "model_kind": "open-weight model hosted by Groq",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "google/gemma-4-26b-a4b-it:free",
        "model_kind": "open-weight model; the serving provider is chosen by OpenRouter unless pinned",
    },
}

_KEYS: dict[str, str] = {}


def set_key(provider: str) -> str:
    """Read the key from the environment, else ask with a masked prompt. Returns a status line only."""
    p = PROVIDERS[provider]
    k = ""
    if provider == "google":
        k = os.environ.get("GOOGLE_API_KEY", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    else:
        k = os.environ.get(p["key_env"], "").strip()
    if not k:
        k = getpass.getpass(f"Paste your {provider} key (hidden, not saved): ").strip()
    if not k:
        return f"{provider}: no key set, remote comparison skipped"
    _KEYS[provider] = k
    env = p.get("alt_key_env") or p["key_env"]
    return f"{provider}: key set for this session only ({env} or hidden prompt)"


def forget_keys() -> None:
    _KEYS.clear()


def _redact(text: str) -> str:
    for k in _KEYS.values():
        if k:
            text = text.replace(k, "[key removed]")
    return text


def remote_chat(
    provider: str,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 96,
    extra_body: dict | None = None,
    timeout: float = 60.0,
    model_param: str | None = None,
) -> dict:
    """Same return shape as civicdesk_lab.chat. mode is 'live' only for a real provider reply."""
    p = PROVIDERS[provider]
    model = model_param or model or p["default_model"]
    t0 = time.perf_counter()
    if provider not in _KEYS:
        return {
            "ok": False,
            "mode": "skipped",
            "model": model,
            "text": "",
            "latency_ms": 0,
            "usage": None,
            "usage_source": "none (no key)",
            "finish_reason": None,
            "error": "no key set",
            "provider": provider,
        }
    body = {"model": model, "messages": messages, "max_tokens": int(max_tokens), "temperature": 0}
    if extra_body:
        body.update(extra_body)
    req = urllib.request.Request(
        p["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "civicdesk-t103/1.0",
            "Authorization": "Bearer " + _KEYS[provider],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
        ch = payload["choices"][0]
        u = payload.get("usage") if isinstance(payload.get("usage"), dict) else None
        ok_usage = bool(u and isinstance(u.get("prompt_tokens"), int) and isinstance(u.get("completion_tokens"), int))
        return {
            "ok": True,
            "mode": "live",
            "model": payload.get("model") or model,
            "requested_model": model,
            "text": (ch.get("message") or {}).get("content") or "",
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "usage": u if ok_usage else None,
            "usage_raw": u,
            "usage_source": f"provider ({provider})" if ok_usage else "none (provider sent no usage)",
            "finish_reason": ch.get("finish_reason"),
            "error": None,
            "provider": provider,
        }
    except urllib.error.HTTPError as e:
        detail = _redact(e.read().decode(errors="ignore")[:300])
        return {
            "ok": False,
            "mode": "error",
            "model": model,
            "text": "",
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "usage": None,
            "usage_source": "none (error)",
            "finish_reason": None,
            "error": f"HTTP {e.code}: {detail}",
            "provider": provider,
        }
    except Exception as e:
        return {
            "ok": False,
            "mode": "error",
            "model": model,
            "text": "",
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "usage": None,
            "usage_source": "none (error)",
            "finish_reason": None,
            "error": _redact(f"{type(e).__name__}: {e}"),
            "provider": provider,
        }


def make_chat_fn(provider: str, model: str | None = None, extra_body: dict | None = None, pause_s: float = 0.0):
    """Adapter for civicdesk_eval.run_eval. pause_s spaces requests out to stay under free-tier limits."""

    def fn(messages, model=model, max_tokens=96):
        r = remote_chat(provider, messages, model=model, max_tokens=max_tokens, extra_body=extra_body)
        if pause_s:
            time.sleep(pause_s)
        return r

    return fn
