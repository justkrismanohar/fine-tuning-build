"""CivicDesk Day 1 helper.

Backends (pick one in a notebook cell with use_backend):
  demo    — canned replies, no GPU, default
  local   — OLMo/Phi you started with build_llms.py (reads logs/endpoint.json)
  shared  — course browser workspace URL
  custom  — any OpenAI-compatible /v1/chat/completions URL
  live    — alias of local, also used if CIVICDESK_MODE=live

This file does not start the models. T1-01a / build_llms.py does that.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request as urlrequest

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)
ENDPOINT_FILE = LOGS / "endpoint.json"

OLMO_ID = "allenai/OLMo-2-0425-1B-Instruct"
PHI_ID = "microsoft/Phi-4-mini-instruct"

DATA_BAN = [
    "real applicant CVs, names, ID numbers, contact details",
    "Cabinet Minutes or Notes, or any EDMS export",
    "case files, beneficiary, household or income records",
    "health records, LMS submissions, unpublished articles about real people",
    "burgess applications, food-badge or permit files",
    "patrol, radar, interdiction or intelligence notes",
    "passwords, MFA codes, API keys, AD credentials",
    "live GLPI / LMS / GIS / asset-register extracts",
]

# In-memory settings for this kernel. use_backend() writes these.
_settings: dict[str, Any] = {
    "mode": os.environ.get("CIVICDESK_MODE", "demo").strip().lower(),
    "olmo_url": os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"),
    "phi_url": os.environ.get("CIVICDESK_PHI_URL", os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8001/v1")),
    "model": os.environ.get("CIVICDESK_MODEL", OLMO_ID),
    "comparison_model": os.environ.get("CIVICDESK_COMPARE_MODEL", PHI_ID),
    "api_key": os.environ.get("CIVICDESK_API_KEY") or os.environ.get("OPENAI_API_KEY") or "",
    "fallback_to_demo": True,
    "engine": os.environ.get("CIVICDESK_ENGINE", "").strip() or None,
    "backend": os.environ.get("CIVICDESK_MODE", "demo").strip().lower(),
}

TOKENIZER_ENV = "CIVICDESK_TOKENIZER_DIR"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 256
_tok_cache: dict[str, Any] = {}
_show_tokens_explained = False


def print_data_ban() -> None:
    print("DATA BAN - if it came from work, it does not go in a cell.")
    for item in DATA_BAN:
        print(f"  - {item}")
    print("Use CivicDesk fiction only. A planted secret in a prompt is a fail for the exercise.")


def load_requests() -> list[dict]:
    path = DATA / "civicdesk_day1_requests.json"
    return json.loads(path.read_text(encoding="utf-8"))["requests"]


def print_request_menu(requests: list[dict] | None = None) -> None:
    """Seating chart: ministry EOI type → CivicDesk request id."""
    if requests is None:
        requests = load_requests()
    print("Same mechanics for everyone: system constitution + user turn, then send.")
    print("Find your ministry, copy that id into chosen_id.")
    print()
    print(f"{'id':10}  {'cluster':14}  pick if you are")
    print("-" * 72)
    for r in requests:
        who = r.get("pick_if_you_are") or ", ".join(r.get("stands_in_for") or [])
        print(f"{r['id']:10}  {r['cluster']:14}  {who}")
        print(f"{'':10}  {r['title']}")
        print()


def print_request_story(req: dict) -> None:
    """Short EOI narrative for the request just loaded."""
    print("PICK IF YOU ARE")
    print(req.get("pick_if_you_are") or ", ".join(req.get("stands_in_for") or []))
    print()
    print("AT WORK (from the EOI)")
    print(req.get("at_work") or "")
    print()
    print("IN THIS ROOM (CivicDesk fiction)")
    print(req.get("in_this_room") or "")
    print()
    print("WATCH FOR")
    print(req.get("watch_for") or "")


def _load_saved_endpoint() -> dict:
    if not ENDPOINT_FILE.exists():
        return {}
    try:
        return json.loads(ENDPOINT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _colab_track() -> bool:
    return os.environ.get("CIVICDESK_COLAB", "").strip() in {"1", "true", "yes"}


def use_backend(
    name: str,
    *,
    olmo_url: str | None = None,
    phi_url: str | None = None,
    model: str | None = None,
    comparison_model: str | None = None,
    api_key: str | None = None,
    fallback_to_demo: bool = True,
    shared_url: str | None = None,
    engine: str | None = None,
) -> dict:
    """Point the rest of today's notebooks at demo, local vLLM, shared course URL, or a custom URL.

    Call this once at the top of T1-01 (and again if you change your mind).
    """
    name = (name or "demo").strip().lower()
    if name == "live":
        name = "local"
    if _colab_track() and name != "demo":
        print("COLAB TRACK: BACKEND is locked to demo. Live OLMo/Phi are the Docker course.")
        name = "demo"

    def _http(url: str | None) -> str | None:
        if url and str(url).lower().startswith("http"):
            return str(url).rstrip("/")
        return None

    saved = _load_saved_endpoint()
    olmo_from_file = _http((saved.get("olmo") or {}).get("base_url"))
    phi_from_file = _http((saved.get("phi") or {}).get("base_url"))
    olmo_model_from_file = (saved.get("olmo") or {}).get("model")
    phi_model_from_file = (saved.get("phi") or {}).get("model")
    olmo_url = _http(olmo_url)
    phi_url = _http(phi_url)

    if name == "demo":
        _settings["mode"] = "demo"
        _settings["olmo_url"] = "demo"
        _settings["phi_url"] = "demo"
        _settings["engine"] = "demo"
    elif name == "local":
        _settings["mode"] = "live"
        _settings["olmo_url"] = olmo_url or olmo_from_file or "http://127.0.0.1:8000/v1"
        _settings["phi_url"] = phi_url or phi_from_file or "http://127.0.0.1:8001/v1"
        _settings["engine"] = engine or saved.get("engine") or "unknown"
        if olmo_model_from_file:
            _settings["model"] = olmo_model_from_file
        if phi_model_from_file:
            _settings["comparison_model"] = phi_model_from_file
    elif name == "shared":
        url = (shared_url or os.environ.get("COURSE_SHARED_URL") or olmo_url or "").rstrip("/")
        if not url:
            raise ValueError(
                "BACKEND='shared' needs COURSE_SHARED_URL or shared_url=... "
                "(the facilitator URL for the browser workspace)."
            )
        if not url.endswith("/v1"):
            url = url + "/v1"
        _settings["mode"] = "live"
        _settings["olmo_url"] = url
        _settings["phi_url"] = phi_url or url
        _settings["engine"] = engine or "unknown"
    elif name == "custom":
        if not olmo_url:
            raise ValueError("BACKEND='custom' needs olmo_url='http://host:port/v1'")
        _settings["mode"] = "live"
        _settings["olmo_url"] = olmo_url.rstrip("/")
        _settings["phi_url"] = (phi_url or olmo_url).rstrip("/")
        _settings["engine"] = engine or "unknown"
    else:
        raise ValueError("BACKEND must be demo, local, shared, custom, or live")

    if model:
        _settings["model"] = model
    if comparison_model:
        _settings["comparison_model"] = comparison_model
    if api_key is not None:
        _settings["api_key"] = api_key
    _settings["fallback_to_demo"] = fallback_to_demo
    _settings["backend"] = name

    snap = endpoint_config()
    ENDPOINT_FILE.write_text(
        json.dumps(
            {
                "backend": name,
                "mode": snap["mode"],
                "olmo": {"base_url": snap["olmo_url"], "model": snap["model"]},
                "phi": {"base_url": snap["phi_url"], "model": snap["comparison_model"]},
                "fallback_to_demo": fallback_to_demo,
                "engine": _settings.get("engine"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return snap


def endpoint_config() -> dict:
    return {
        "backend": _settings.get("backend") or _settings["mode"],
        "mode": _settings["mode"],
        "olmo_url": _settings["olmo_url"],
        "phi_url": _settings["phi_url"],
        "model": _settings["model"],
        "comparison_model": _settings["comparison_model"],
        "api_key_set": bool(_settings.get("api_key")),
        "fallback_to_demo": _settings["fallback_to_demo"],
        "endpoint_file": str(ENDPOINT_FILE),
        "engine": _settings.get("engine") or (_load_saved_endpoint().get("engine")),
    }


def resolve_model(which: str | None = None) -> str:
    """Hugging Face id for this send. Default is OLMo unless which is 'phi'."""
    choice = (which or "").strip().lower()
    if choice == "phi":
        return _settings["comparison_model"]
    return _settings["model"]


def _url_for_model(model: str) -> str:
    if model == _settings["comparison_model"] or "phi" in model.lower():
        return _settings["phi_url"]
    return _settings["olmo_url"]


def _demo_tag(model: str) -> str:
    return "[Phi-4-mini demo]" if "phi" in (model or "").lower() else "[OLMo demo]"


def _demo_reply(user_text: str, model: str, system_text: str = "") -> str:
    """Canned CivicDesk replies. Used by BACKEND=demo and the Colab track. Not a live model."""
    tag = _demo_tag(model)
    phi = "phi" in (model or "").lower()
    sys_l = (system_text or "").lower()
    if "unrestricted" in sys_l or "no classroom rules" in sys_l:
        return (
            f"{tag} Unrestricted system prompt: I would try to answer even without a handbook "
            "or a register. That is the wrong constitution for CivicDesk. Put the rules back in `role: system`."
        )
    if "always invent" in sys_l:
        return (
            f"{tag} CivicDesk Circular 99 of 2024: attachments may be stored overnight. "
            "That circular is not in the prompt. The system text told me to invent. That is a fail."
        )
    if "finance questions only" in sys_l:
        return (
            f"{tag} Canned text. Demo mode cannot show whether OLMo follows a scope rule. "
            "Switch BACKEND to local or shared to test it."
        )
    t = user_text.lower()
    if "bank to" in t:
        return (
            f"{tag} No live model on this backend, so there is no real continuation to read. "
            "Switch BACKEND to local or shared, or open completed/T1-01_first_call.ipynb "
            "for a recorded live run."
        )
    if "patrol" in t or "cabinet" in t or "landing" in t:
        return (
            f"{tag} I cannot use patrol notes, landing sites or Cabinet text. "
            "CivicDesk has no such records. Stop. A human officer must use an approved operational system."
        )
    if "reset" in t and "password" in t:
        return (
            f"{tag} I will not reset a password or call a directory. "
            "Draft ticket fields: user-stated symptom='password reset requested'; "
            "category='account'; next_step='human identity check'. Human review required."
        )
    if "warranty" in t or "printer" in t:
        return (
            f"{tag} No asset table is in this prompt. I will not invent serial numbers. "
            "Query the CivicDesk register (a database). Human review required if you expected a list."
        )
    if "attachments overnight" in t or "cite the handbook" in t or "circular" in t:
        return (
            f"{tag} No approved handbook paragraph is in this prompt. "
            "I cannot cite. I will not invent a circular number. Stop. (Day 2 is retrieval.)"
        )
    if "criterion c2" in t or "diploma" in t or "missing diploma" in t:
        if phi:
            return (
                f"{tag} Human review required. Library studies is not records management on its face. "
                "Quoted span: 'two-year diploma in library studies'. Do not hire."
            )
        return (
            f"{tag} Label: Human review required. "
            "Quoted span: 'two-year diploma in library studies'. "
            "C2 asks for records management or equivalent; library studies may be equivalent but is not identical. "
            "Do not hire."
        )
    if "public notice" in t or "rule n1" in t:
        return (
            f"{tag} Criterion N1: OK to proceed as draft. "
            "Quoted span: 'No individual cases will be discussed.' "
            "Advisory only. Do not publish. Human review required before any public release."
        )
    return (
        f"{tag} CivicDesk reply: I can draft from the text you sent. "
        "I have no ministry file. If this were a consequential decision, mark Human review required."
    )


def simulate_hosting_check() -> dict:
    """Colab / no-Docker stand-in for build_llms.check(). Does not probe a GPU to start a model."""
    import sys

    info = {
        "track": "colab-demo",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "nvidia_smi": None,
        "vllm_import": False,
        "docker": False,
        "transformers_import": False,
        "note": (
            "Colab demo track: we do not download or serve OLMo/Phi. "
            "Later notebooks use canned [OLMo demo] / [Phi-4-mini demo] replies. "
            "The Docker course is the live-hosting lab."
        ),
    }
    print(json.dumps(info, indent=2))
    return info


def simulate_hosting_skip_serve() -> dict:
    """Write a demo endpoint.json so T1-01 can run without :8000/:8001."""
    payload = {
        "backend": "demo",
        "mode": "demo",
        "engine": "skip-colab",
        "olmo": {"base_url": "demo", "model": OLMO_ID},
        "phi": {"base_url": "demo", "model": PHI_ID},
        "note": "No live door on this track.",
    }
    ENDPOINT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print("wrote", ENDPOINT_FILE)
    return payload


def _chat_body(
    model: str,
    messages: list[dict],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    seed: int | None = None,
) -> dict:
    """JSON body posted to /v1/chat/completions. Defaults match historical T1-01 calls."""
    if temperature is None:
        temperature = DEFAULT_TEMPERATURE
    if not 0 <= float(temperature) <= 2:
        raise ValueError("temperature must be between 0 and 2")
    if max_tokens is None:
        max_tokens = DEFAULT_MAX_TOKENS
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if top_p is not None:
        body["top_p"] = top_p
    if seed is not None:
        body["seed"] = seed
    return body


def _requested(temperature, max_tokens, top_p, seed) -> dict:
    return {
        "temperature": DEFAULT_TEMPERATURE if temperature is None else temperature,
        "max_tokens": DEFAULT_MAX_TOKENS if max_tokens is None else max_tokens,
        "top_p": top_p,
        "seed": seed,
    }


def _engine_from_payload(payload: dict | None, *, canned: bool) -> str:
    if canned:
        return "demo"
    if payload:
        civic = payload.get("civicdesk") or {}
        if payload.get("id") == "hf-civicdesk" or civic.get("engine") == "hf":
            return "hf"
    return _settings.get("engine") or _load_saved_endpoint().get("engine") or "unknown"


def _usage_from(payload: dict | None) -> tuple[dict | None, str]:
    u = payload.get("usage") if isinstance(payload, dict) else None
    if isinstance(u, dict) and isinstance(u.get("prompt_tokens"), int) and isinstance(
        u.get("completion_tokens"), int
    ):
        return u, "server"
    return None, "none (server sent no usage)"


def _applied(payload: dict | None, requested: dict, *, canned: bool) -> dict:
    if canned:
        return {"temperature": None, "note": "canned reply; sampling settings not used"}
    civic = (payload or {}).get("civicdesk") or {}
    if civic or (payload or {}).get("id") == "hf-civicdesk":
        return {
            "temperature": civic.get("temperature"),
            "do_sample": civic.get("do_sample"),
            "top_p": civic.get("top_p"),
            "top_k": civic.get("top_k"),
            "seed": civic.get("seed"),
        }
    return {
        "temperature": requested["temperature"],
        "note": "sent; server did not report what it applied",
    }


def _post_chat(
    url: str,
    model: str,
    messages: list[dict],
    timeout: float,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    seed: int | None = None,
) -> dict:
    body = json.dumps(
        _chat_body(
            model,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            seed=seed,
        )
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = _settings.get("api_key") or ""
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urlrequest.Request(
        url.rstrip("/") + "/chat/completions",
        data=body,
        headers=headers,
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(
    messages: list[dict],
    model: str | None = None,
    timeout: float = 60.0,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    seed: int | None = None,
) -> dict:
    """Send a chat. Demo backend never leaves the laptop. Live posts to the chosen /v1."""
    model = model or _settings["model"]
    t0 = time.perf_counter()
    sys_text = ""
    for m in messages:
        if m.get("role") == "system":
            sys_text = m.get("content") or ""
            break
    user_text = messages[-1]["content"]
    requested = _requested(temperature, max_tokens, top_p, seed)
    if _colab_track():
        _settings["mode"] = "demo"
    if _settings["mode"] != "live":
        return {
            "ok": True,
            "mode": "demo",
            "model": model,
            "text": _demo_reply(user_text, model, sys_text),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "raw": None,
            "url": "demo",
            "requested": requested,
            "applied": _applied(None, requested, canned=True),
            "engine": "demo",
            "canned": True,
            "usage": None,
            "usage_source": "none (demo reply, not a model)",
            "finish_reason": None,
        }

    url = _url_for_model(model)
    try:
        payload = _post_chat(
            url,
            model,
            messages,
            timeout,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            seed=seed,
        )
        text = payload["choices"][0]["message"]["content"]
        usage, usage_source = _usage_from(payload)
        return {
            "ok": True,
            "mode": "live",
            "model": model,
            "text": text,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "raw": payload,
            "url": url,
            "requested": requested,
            "applied": _applied(payload, requested, canned=False),
            "engine": _engine_from_payload(payload, canned=False),
            "canned": False,
            "usage": usage,
            "usage_source": usage_source,
            "finish_reason": payload["choices"][0].get("finish_reason"),
        }
    except Exception as exc:  # noqa: BLE001 — classroom: show the error
        if not _settings["fallback_to_demo"]:
            raise
        return {
            "ok": False,
            "mode": "demo-fallback",
            "model": model,
            "text": _demo_reply(user_text, model, sys_text),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "error": str(exc),
            "url": url,
            "requested": requested,
            "applied": _applied(None, requested, canned=True),
            "engine": "demo",
            "canned": True,
            "usage": None,
            "usage_source": "none (fallback demo reply after an error)",
            "finish_reason": None,
        }


OLMO_SHAPE_REF = {
    "num_hidden_layers": 16,
    "num_attention_heads": 16,
    "hidden_size": 2048,
    "vocab_size": 100352,
}


class TokenizerUnavailable(RuntimeError):
    """Raised with a plain-English fix when OLMo's tokenizer files are not on this machine."""


def tokenizer_source() -> str:
    """First match wins: $CIVICDESK_TOKENIZER_DIR, $CIVICDESK_MODELS_DIR/olmo, then HF cache (offline)."""
    env = os.environ.get(TOKENIZER_ENV, "").strip()
    if env:
        return env
    models_dir = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models"))
    olmo = models_dir / "olmo"
    if (olmo / "tokenizer.json").is_file() or (olmo / "tokenizer_config.json").is_file():
        return str(olmo)
    try:
        from huggingface_hub import try_to_load_from_cache

        cached = try_to_load_from_cache(OLMO_ID, "tokenizer.json")
        if cached and Path(cached).is_file():
            return str(Path(cached).parent)
    except Exception:
        pass
    return str(olmo)


def _looked_in_message(source: str) -> str:
    return (
        f"OLMo tokenizer files were not found at {source}. "
        "Ask the facilitator (the course image bakes them into /models/olmo). "
        "Meanwhile open completed/T1-02_tokens_and_transformer.ipynb."
    )


def load_tokenizer():
    """AutoTokenizer from local files only. Cached per kernel. Never loads weights."""
    source = tokenizer_source()
    cached = _tok_cache.get(source)
    if cached:
        return cached["tok"]

    env_forced = bool(os.environ.get(TOKENIZER_ENV, "").strip())
    tok_json = Path(source) / "tokenizer.json"
    try:
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(source, local_files_only=True)
        _tok_cache[source] = {"tok": tok, "backend": "transformers", "source": source}
        return tok
    except Exception:
        pass

    if tok_json.is_file():
        try:
            from tokenizers import Tokenizer as FastTokenizer

            tok = FastTokenizer.from_file(str(tok_json))
            _tok_cache[source] = {"tok": tok, "backend": "tokenizers-only", "source": source}
            return tok
        except Exception:
            pass

    if env_forced:
        raise TokenizerUnavailable(_looked_in_message(source))

    try:
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(OLMO_ID, local_files_only=True)
        _tok_cache[source] = {
            "tok": tok,
            "backend": "transformers",
            "source": getattr(tok, "name_or_path", None) or f"Hugging Face cache ({OLMO_ID})",
        }
        return tok
    except Exception as exc:
        raise TokenizerUnavailable(_looked_in_message(source)) from exc


def _backend() -> str:
    source = tokenizer_source()
    load_tokenizer()
    return _tok_cache[source]["backend"]


def _is_fast_only(tok) -> bool:
    return type(tok).__name__ == "Tokenizer" and not hasattr(tok, "apply_chat_template")


def tokenizer_info() -> dict:
    tok = load_tokenizer()
    source = _tok_cache[tokenizer_source()]["source"]
    backend = _tok_cache[tokenizer_source()]["backend"]
    cfg_path = Path(tokenizer_source()) / "config.json"
    window = None
    if cfg_path.is_file():
        try:
            window = json.loads(cfg_path.read_text(encoding="utf-8")).get("max_position_embeddings")
        except json.JSONDecodeError:
            window = None
    tok_json = Path(tokenizer_source()) / "tokenizer.json"
    sha = None
    if tok_json.is_file():
        sha = hashlib.sha256(tok_json.read_bytes()).hexdigest()[:12]
    try:
        import transformers

        tf_ver = transformers.__version__
    except Exception:
        tf_ver = None
    vocab = len(tok) if hasattr(tok, "__len__") else None
    if vocab is None and hasattr(tok, "get_vocab"):
        vocab = len(tok.get_vocab())
    return {
        "source": source,
        "backend": backend,
        "tokenizer_class": type(tok).__name__,
        "vocab_size": vocab,
        "tokenizer_sha256": sha,
        "context_window": window,
        "transformers": tf_ver,
        "weights_loaded": False,
    }


def token_ids(text: str) -> list[int]:
    tok = load_tokenizer()
    if _is_fast_only(tok):
        return tok.encode(text).ids
    return tok.encode(text, add_special_tokens=False)


def tokenize(text: str) -> list[dict]:
    tok = load_tokenizer()
    ids = token_ids(text)
    rows = []
    for pos, tid in enumerate(ids):
        if _is_fast_only(tok):
            piece = tok.id_to_token(tid)
            decoded = tok.decode([tid])
        else:
            piece = tok.convert_ids_to_tokens(tid)
            decoded = tok.decode([tid])
        rows.append({"pos": pos, "id": int(tid), "piece": piece, "text": decoded})
    return rows


def count_tokens(text: str) -> int:
    return len(token_ids(text))


def show_tokens(text: str, tok=None, max_rows: int | None = None) -> None:
    """Print pos | id | decoded piece. Leading space shown as ␠, newline as ↵."""
    global _show_tokens_explained
    if tok is None:
        try:
            rows = tokenize(text)
        except TokenizerUnavailable as exc:
            print(exc)
            print("stand-in tokenizer, not OLMo's; IDs not available")
            for piece in naive_tokens(text):
                print(f"  {piece!r}")
            return
    else:
        ids = tok.encode(text, add_special_tokens=False)
        rows = []
        for pos, tid in enumerate(ids):
            rows.append(
                {
                    "pos": pos,
                    "id": int(tid),
                    "piece": tok.convert_ids_to_tokens(tid) if hasattr(tok, "convert_ids_to_tokens") else "",
                    "text": tok.decode([tid]),
                }
            )
    if not _show_tokens_explained:
        print("Display: a leading space is ␠; a newline is ↵. In raw pieces, Ġ means a space.")
        _show_tokens_explained = True
    shown = rows if max_rows is None else rows[:max_rows]
    print(f"{'pos':>4}  {'id':>8}  display")
    for r in shown:
        disp = (r["text"] or "").replace("\n", "↵")
        if disp.startswith(" "):
            disp = "␠" + disp[1:]
        print(f"{r['pos']:4d}  {r['id']:8d}  {disp}")
    if max_rows is not None and len(rows) > max_rows:
        print(f"  … {len(rows) - max_rows} more")


def roundtrip(text: str) -> dict:
    tok = load_tokenizer()
    ids = token_ids(text)
    decoded = tok.decode(ids) if not _is_fast_only(tok) else tok.decode(ids)
    return {"decoded": decoded, "identical": decoded == text}


def find_token(text: str, word: str) -> list[dict]:
    """Rows whose decoded text, stripped, equals word; else rows overlapping the word's span."""
    rows = tokenize(text)
    hits = [r for r in rows if (r["text"] or "").strip() == word]
    if hits:
        return hits
    start = text.find(word)
    if start < 0:
        return []
    end = start + len(word)
    cursor = 0
    overlapped = []
    for r in rows:
        piece = r["text"] or ""
        span_end = cursor + len(piece)
        if cursor < end and span_end > start:
            overlapped.append(r)
        cursor = span_end
    return overlapped


def _ids_unbroken(needle: list[int], hay: list[int]) -> bool:
    n = len(needle)
    if n == 0:
        return True
    for i in range(len(hay) - n + 1):
        if hay[i : i + n] == needle:
            return True
    return False


def chat_tokens(messages: list[dict], add_generation_prompt: bool = True) -> dict:
    tok = load_tokenizer()
    if _is_fast_only(tok):
        cfg = Path(tokenizer_source()) / "tokenizer_config.json"
        template = json.loads(cfg.read_text(encoding="utf-8")).get("chat_template") if cfg.is_file() else None
        if not template:
            raise TokenizerUnavailable("chat template missing; install transformers for chat_tokens")
        import jinja2

        bos = getattr(tok, "bos_token", None) or "<|endoftext|>"
        env = jinja2.Environment()
        rendered = env.from_string(template).render(
            messages=messages,
            bos_token=bos,
            add_generation_prompt=add_generation_prompt,
        )
        ids = tok.encode(rendered).ids
    else:
        rendered = tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=add_generation_prompt
        )
        ids = tok(rendered, add_special_tokens=False)["input_ids"]
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], list):
            ids = ids[0]
    ids = [int(i) for i in ids]
    per = []
    for m in messages:
        content = m.get("content") or ""
        own = token_ids(content)
        per.append(
            {
                "role": m.get("role"),
                "content_tokens": len(own),
                "appears_unbroken": _ids_unbroken(own, ids),
            }
        )
    content_sum = sum(p["content_tokens"] for p in per)
    return {
        "rendered": rendered,
        "ids": ids,
        "count": len(ids),
        "per_message": per,
        "content_sum": content_sum,
        "difference": len(ids) - content_sum,
    }


def fetch_tokenizer_files(dest: str | Path) -> Path:
    """Optional laptop helper. Never fetches model.safetensors. Not used by required cells."""
    from huggingface_hub import snapshot_download

    dest = Path(dest)
    snapshot_download(
        OLMO_ID,
        local_dir=str(dest),
        allow_patterns=["tokenizer*", "vocab.json", "merges.txt", "special_tokens_map.json", "config.json"],
    )
    return dest


def _shape_from_config(cfg: dict, source: str) -> dict:
    return {
        "num_hidden_layers": int(cfg.get("num_hidden_layers", OLMO_SHAPE_REF["num_hidden_layers"])),
        "num_attention_heads": int(cfg.get("num_attention_heads", OLMO_SHAPE_REF["num_attention_heads"])),
        "hidden_size": int(cfg.get("hidden_size", OLMO_SHAPE_REF["hidden_size"])),
        "vocab_size": int(cfg.get("vocab_size", OLMO_SHAPE_REF["vocab_size"])),
        "source": source,
    }


def model_shape() -> dict:
    """Read OLMo config.json only. Does not load weights or download."""
    models_dir = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models"))
    local_cfg = models_dir / "olmo" / "config.json"
    if local_cfg.is_file():
        cfg = json.loads(local_cfg.read_text(encoding="utf-8"))
        return _shape_from_config(cfg, str(local_cfg))
    try:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(OLMO_ID, "config.json", local_files_only=True)
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
        return _shape_from_config(cfg, path)
    except Exception:
        out = dict(OLMO_SHAPE_REF)
        out["source"] = (
            "reference values for OLMo-2-0425-1B-Instruct "
            "(config not found on this machine)"
        )
        return out


def naive_tokens(text: str) -> list[str]:
    """Word splitter kept for backward compatibility. T1-02 now uses OLMo's tokenizer (see tokenize)."""
    out: list[str] = []
    buf = ""
    for ch in text:
        if ch.isalnum() or ch in "'’-":
            buf += ch
        else:
            if buf:
                out.append(buf.lower())
                buf = ""
            if not ch.isspace():
                out.append(ch)
    if buf:
        out.append(buf.lower())
    return out


def print_trials(trials: list[dict]) -> None:
    """Print the comparison pad from T1-01."""
    if not trials:
        print("(no trials yet)")
        return
    for i, t in enumerate(trials, 1):
        print("=" * 60)
        print(f"{i}. {t.get('label', '')}  |  model={t.get('model')}  |  mode={t.get('mode')}")
        print("system:", (t.get("system") or "")[:180])
        print("user:  ", (t.get("user") or "")[:180])
        print("reply: ", (t.get("reply") or "")[:400])
        if t.get("note"):
            print("note:  ", t["note"])


def save_log(name: str, record: dict) -> Path:
    record = dict(record)
    record["saved_at"] = datetime.now(timezone.utc).isoformat()
    path = LOGS / f"{name}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def gpu_note() -> str:
    try:
        import subprocess

        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return "nvidia-smi ran but returned nothing. Use the shared endpoint or BACKEND='demo'."
    except Exception:
        return "No local NVIDIA GPU visible. Options: BACKEND='demo', BACKEND='shared', or WSL2/Docker for vLLM."
