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
}


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
) -> dict:
    """Point the rest of today's notebooks at demo, local vLLM, shared course URL, or a custom URL.

    Call this once at the top of T1-01 (and again if you change your mind).
    """
    name = (name or "demo").strip().lower()
    if name == "live":
        name = "local"

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
    elif name == "local":
        _settings["mode"] = "live"
        _settings["olmo_url"] = olmo_url or olmo_from_file or "http://127.0.0.1:8000/v1"
        _settings["phi_url"] = phi_url or phi_from_file or "http://127.0.0.1:8001/v1"
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
    elif name == "custom":
        if not olmo_url:
            raise ValueError("BACKEND='custom' needs olmo_url='http://host:port/v1'")
        _settings["mode"] = "live"
        _settings["olmo_url"] = olmo_url.rstrip("/")
        _settings["phi_url"] = (phi_url or olmo_url).rstrip("/")
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


def _demo_reply(user_text: str, model: str, system_text: str = "") -> str:
    sys_l = (system_text or "").lower()
    if "unrestricted" in sys_l or "no classroom rules" in sys_l:
        return (
            f"[{model} demo] Unrestricted system prompt: I would try to answer even without a handbook "
            "or a register. That is the wrong constitution for CivicDesk. Put the rules back in `role: system`."
        )
    if "always invent" in sys_l:
        return (
            f"[{model} demo] CivicDesk Circular 99 of 2024: attachments may be stored overnight. "
            "That circular is not in the prompt. The system text told me to invent. That is a fail."
        )
    t = user_text.lower()
    if "patrol" in t or "cabinet" in t or "landing" in t:
        return (
            f"[{model} demo] I cannot use patrol notes, landing sites or Cabinet text. "
            "CivicDesk has no such records. Stop. A human officer must use an approved operational system."
        )
    if "reset" in t and "password" in t:
        return (
            f"[{model} demo] I will not reset a password or call a directory. "
            "Draft ticket fields: user-stated symptom='password reset requested'; "
            "category='account'; next_step='human identity check'. Human review required."
        )
    if "warranty" in t or "printer" in t:
        return (
            f"[{model} demo] No asset table is in this prompt. I will not invent serial numbers. "
            "Query the CivicDesk register (a database). Human review required if you expected a list."
        )
    if "attachments overnight" in t or "cite the handbook" in t or "circular" in t:
        return (
            f"[{model} demo] No approved handbook paragraph is in this prompt. "
            "I cannot cite. I will not invent a circular number. Stop. (Day 2 is retrieval.)"
        )
    if "criterion c2" in t or "diploma" in t:
        return (
            f"[{model} demo] Label: Human review required. "
            "Quoted span: 'two-year diploma in library studies'. "
            "C2 asks for records management or equivalent; library studies may be equivalent but is not identical. "
            "Do not hire."
        )
    if "public notice" in t or "rule n1" in t:
        return (
            f"[{model} demo] Criterion N1: OK to proceed as draft. "
            "Quoted span: 'No individual cases will be discussed.' "
            "Advisory only. Do not publish. Human review required before any public release."
        )
    return (
        f"[{model} demo] CivicDesk reply: I can draft from the text you sent. "
        "I have no ministry file. If this were a consequential decision, mark Human review required."
    )


def _post_chat(url: str, model: str, messages: list[dict], timeout: float) -> dict:
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": 0.0, "max_tokens": 256}
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


def chat(messages: list[dict], model: str | None = None, timeout: float = 60.0) -> dict:
    """Send a chat. Demo backend never leaves the laptop. Live posts to the chosen /v1."""
    model = model or _settings["model"]
    t0 = time.perf_counter()
    sys_text = ""
    for m in messages:
        if m.get("role") == "system":
            sys_text = m.get("content") or ""
            break
    user_text = messages[-1]["content"]
    if _settings["mode"] != "live":
        return {
            "ok": True,
            "mode": "demo",
            "model": model,
            "text": _demo_reply(user_text, model, sys_text),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "raw": None,
            "url": "demo",
        }

    url = _url_for_model(model)
    try:
        payload = _post_chat(url, model, messages, timeout)
        text = payload["choices"][0]["message"]["content"]
        return {
            "ok": True,
            "mode": "live",
            "model": model,
            "text": text,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "raw": payload,
            "url": url,
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
        }


def naive_tokens(text: str) -> list[str]:
    """Stand-in tokenizer so Day 1 runs without Hugging Face. Not OLMo's tokenizer."""
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
