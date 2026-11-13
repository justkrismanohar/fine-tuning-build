"""T1-02 helper checks. No GPU. Tokenizer tests skip if files are not on this machine."""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

DAY1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DAY1))

import civicdesk_lab as lab  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "ENDPOINT_FILE", tmp_path / "endpoint.json")
    original = dict(lab._settings)
    lab.use_backend("demo")
    yield
    lab._settings.clear()
    lab._settings.update(original)
    lab._tok_cache.clear()


MSGS = [
    {"role": "system", "content": "CivicDesk classroom. One short sentence."},
    {"role": "user", "content": "Should a missing diploma be Human review required?"},
]


def test_chat_body_defaults_match_historical():
    body = lab._chat_body("allenai/OLMo-2-0425-1B-Instruct", MSGS)
    assert body == {
        "model": "allenai/OLMo-2-0425-1B-Instruct",
        "messages": MSGS,
        "temperature": 0.0,
        "max_tokens": 256,
    }


def test_chat_body_sampling_and_bounds():
    body = lab._chat_body("m", MSGS, temperature=0.9, max_tokens=60, top_p=0.95, seed=7)
    assert body["temperature"] == 0.9
    assert body["max_tokens"] == 60
    assert body["top_p"] == 0.95
    assert body["seed"] == 7
    with pytest.raises(ValueError):
        lab._chat_body("m", MSGS, temperature=2.5)


def test_demo_chat_is_canned():
    lab.use_backend("demo")
    r = lab.chat(MSGS, temperature=0.9, max_tokens=60)
    assert r["canned"] is True
    assert r["mode"] == "demo"
    assert r["engine"] == "demo"
    assert r["applied"]["temperature"] is None
    assert r["requested"]["temperature"] == 0.9


def test_finance_demo_is_not_a_perfect_refusal():
    lab.use_backend("demo")
    r = lab.chat(
        [
            {
                "role": "system",
                "content": "If a request is about anything else, reply exactly: Out of scope: finance questions only.",
            },
            {"role": "user", "content": "I've got my fishing rod, so I'm heading to the river bank to"},
        ]
    )
    assert "Canned text" in r["text"]
    assert "cannot show whether OLMo follows" in r["text"]


def test_demo_fallback_on_dead_custom():
    lab.use_backend("custom", olmo_url="http://127.0.0.1:9/v1")
    r = lab.chat(MSGS, temperature=0.9)
    assert r["mode"] == "demo-fallback"
    assert r["canned"] is True
    assert r.get("error")


def test_custom_backend_posts_temperature():
    recorded = {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            recorded["body"] = json.loads(self.rfile.read(n).decode("utf-8"))
            payload = json.dumps(
                {
                    "id": "test",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    httpd = HTTPServer(("127.0.0.1", 0), H)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        lab.use_backend("custom", olmo_url=f"http://127.0.0.1:{port}/v1", fallback_to_demo=False)
        r = lab.chat(MSGS, temperature=0.9, max_tokens=60)
        assert r["ok"]
        assert recorded["body"]["temperature"] == 0.9
        assert recorded["body"]["max_tokens"] == 60
    finally:
        httpd.shutdown()


def test_empty_tokenizer_dir_raises_plain_message(tmp_path, monkeypatch):
    monkeypatch.setenv("CIVICDESK_TOKENIZER_DIR", str(tmp_path))
    lab._tok_cache.clear()
    with pytest.raises(lab.TokenizerUnavailable) as exc:
        lab.load_tokenizer()
    assert str(tmp_path) in str(exc.value)
    assert "completed/T1-02" in str(exc.value)


def test_snapshot_download_only_in_optional_helper():
    src = (DAY1 / "civicdesk_lab.py").read_text(encoding="utf-8")
    start = src.index("def fetch_tokenizer_files")
    assert "snapshot_download" not in src[:start]
    assert "snapshot_download" in src[start:]
    assert "AutoModel" not in src
    assert "model.safetensors" not in src[:start]


def test_notebook_does_not_promise_ids():
    nb = json.loads((DAY1 / "T1-02_tokens_and_transformer.ipynb").read_text(encoding="utf-8"))
    blob = "".join("".join(c.get("source") or []) for c in nb["cells"] if c.get("cell_type") == "markdown")
    low = blob.lower()
    assert "always one token" not in low
    assert "always the same id" not in low
    assert "identical or correct" not in low
    assert "gives different output" not in low
    assert "naive_tokens" not in "".join(
        "".join(c.get("source") or []) for c in nb["cells"] if c.get("cell_type") == "code"
    )


def test_positional_chat_still_works():
    r = lab.chat(MSGS, lab.OLMO_ID)
    assert r["canned"] is True
    assert r["ok"] is True


@pytest.mark.skipif(
    not (Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models")) / "olmo" / "tokenizer.json").is_file()
    and not os.environ.get("CIVICDESK_TOKENIZER_DIR"),
    reason="OLMo tokenizer files not on this machine",
)
def test_roundtrip_and_find_bank():
    money = "I need to deposit my check, so I’m going to the bank to"
    river = "I’ve got my fishing rod, so I’m heading to the river bank to"
    assert lab.roundtrip(money)["identical"]
    assert lab.roundtrip(river)["identical"]
    for text in (money, river):
        rows = lab.find_token(text, "bank")
        assert rows
        assert all("bank" in (r["text"] or "") for r in rows)
    a = lab.chat_tokens(
        [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": money},
        ]
    )
    assert a["difference"] == a["count"] - a["content_sum"]
    assert lab.count_tokens(money) == 15
    assert lab.count_tokens(river) == 16
