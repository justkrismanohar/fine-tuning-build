"""Write the Day 1 notebooks as valid .ipynb files (includes T1-01a build)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _only_arg() -> str | None:
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
            return sys.argv[i + 1]
    return None


ONLY = _only_arg()


def md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip("\n").split("\n")],
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [line + "\n" for line in source.strip("\n").split("\n")],
    }


def nb(cells: list[dict]) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }


def write(name: str, cells: list[dict]) -> None:
    if ONLY and ONLY not in name:
        print("skip", name)
        return
    path = HERE / name
    path.write_text(json.dumps(nb(cells), indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", path.name)


BANNER = """
**How to use this notebook**

- **No-code / code-light:** run every cell in order. Read the teaching note after a cell. Fill the write-up. Do not paste work files.
- **Occasional-code:** run all cells. Change only lines marked `# [CHANGE]`.
- **Deep-code:** optional cells are tagged `# [OPTIONAL]`. Stay with the room on the required path. Do not drive someone else's notebook.

Git is not required. If you are stuck, load the matching file in `completed/` for this notebook only, mark it as loaded from reference, and continue.
"""

# ---------------------------------------------------------------------------
# T1-01a build from scratch
# ---------------------------------------------------------------------------
write(
    "T1-01a_build_from_scratch.ipynb",
    [
        md(
            """# T1-01a Build OLMo and Phi from scratch

**Time:** 09:15–09:50 (first half of the T1-01 block) &nbsp;|&nbsp; **Evidence:** `logs/endpoint.json` and a passing health check

**Same steps as the script:** `python build_llms.py check|download|serve|health|stop`

**Notebook learning outcomes**

- Say what “from scratch” means here: **deploy and serve**, not pre-train a foundation model.
- Check the host (GPU, Docker, Python packages).
- Fetch (or confirm) OLMo and Phi **weights on disk**.
- Start an OpenAI-compatible API for each model.
- Record the URLs so T1-01 can call them.

"""
            + BANNER
        ),
        md(
            """## Overnight readers — the big picture

A language model is three boxes:

1. **Training data** — the pile of text (you inspect this as a licence question in T1-04).
2. **Weights** — that pile compressed into files on disk. OLMo and Phi are two different files.
3. **Output** — produced at use time, when a **runtime** loads the weights and an **API** accepts a prompt.

This notebook is how box 2 gets onto a computer you control, and how a door (the API) is opened in front of it. That is **N7**: if the work is core (CPO, TTDF, Finance, THA, anyone with PII), you should be able to start this door yourself rather than paste into ChatGPT.

You are **not** training OLMo. The Instruct weights already exist. You download them, load them, serve them.

If this machine has no GPU, you still run the **check** cell, then skip serve, and T1-01 will use `BACKEND='demo'` or the shared course URL. Managers: running check and reading the health output is the point. Deep-code people may prefer the script in a terminal; it is the same functions.
"""
        ),
        md(
            """## Ministry link

| EOI type | Why this notebook exists |
|---|---|
| **CPO / TTDF / Finance / THA** | You asked for on-prem or Government-controlled inference. Starting vLLM (or the course image) is that skill, at classroom size. |
| **Trade IMSD** | The “agent” is this API plus rules. Today you stand the API up. Tools (GLPI, password reset) stay off. |
| **Labour / Health / OPR** | The model you will later ask to *quote a criterion* has to live somewhere. Today you see where. |

Equivalent script, if you would rather not click cells:

```text
python build_llms.py check
python build_llms.py download
python build_llms.py serve --engine vllm
python build_llms.py wait
```

On Windows without NVIDIA/WSL, `check` will tell you to stay on demo or use Docker/WSL2. That is an honest result, not a fail.
"""
        ),
        md(
            """## 1. Look at the host

Before you buy or start anything, ask: is there a GPU, what is it, and will a Linux runtime (vLLM) actually run? T1-04 expands the GPU questions. Here you only collect facts.
"""
        ),
        code(
            """# [RUN]
import json
import build_llms as build

info = build.check()
print(json.dumps(info, indent=2))
"""
        ),
        md(
            """### What you should have seen

- `nvidia_smi`: a name, VRAM, compute capability — or null. Null means this laptop will not host the classroom vLLM.
- `vllm_import`: True only on a Linux+CUDA Python where vLLM is installed (course image).
- `docker`: True if you can run the official vLLM container instead.
- `transformers_import`: a slower fallback (`--engine hf`).

**Link:** standing inference (this chat API) is what we start today. A later LoRA job is a **burst** on a possibly bigger card, then that card is stopped. Do not buy one box “for AI” without that split (T1-04).
"""
        ),
        md(
            """## 2. Choose an engine

`# [CHANGE]` one value. Everyone else can leave `skip` and go to T1-01 on demo/shared.

| ENGINE | What it does | When |
|---|---|---|
| `vllm` | Starts two OpenAI servers (OLMo :8000, Phi :8001) | Course image / Linux+CUDA with `pip install vllm` |
| `docker` | Same, via `vllm/vllm-openai` containers | GPU + Docker, no local pip |
| `hf` | Tiny transformers server (slow on CPU) | Review / no vLLM |
| `skip` | Do not start anything | No GPU; use demo or shared in T1-01 |
"""
        ),
        code(
            """# [CHANGE]
ENGINE = "skip"   # "vllm" | "docker" | "hf" | "skip"
MODELS = ["olmo", "phi"]
print("ENGINE =", ENGINE)
print("If skip: you will still finish T1-01 with BACKEND='demo' or BACKEND='shared'.")
"""
        ),
        md(
            """## 3. Weights on disk

Downloading is not training. It copies the published files (Apache-2.0 OLMo, MIT Phi as published — confirm the live card in T1-04) into the Hugging Face cache. The course image may already have them. If `ENGINE='skip'`, do not wait on this cell.
"""
        ),
        code(
            """# [RUN] skip this if ENGINE == "skip" or the image already has the weights
if ENGINE == "skip":
    print("skipped download")
else:
    try:
        paths = build.download(MODELS)
        print(json.dumps(paths, indent=2))
    except SystemExit as exc:
        print("download not available:", exc)
        print("Continue if the course image already contains the models.")
"""
        ),
        md(
            """### After download

You now have **box 2** locally. Until a runtime loads those files, nothing answers. ChatGPT never gives you this folder. That is the open-weight difference (T1-04).
"""
        ),
        md(
            """## 4. Start the door (the API)

Each model gets its own process and port. vLLM speaks the same `/v1/chat/completions` contract OpenAI uses, so T1-01 does not care which engine you picked.

This cell starts servers **in the background**. Leave them running. Stop later with `build.stop()` or `python build_llms.py stop`.
"""
        ),
        code(
            """# [RUN]
if ENGINE == "skip":
    print("No local server. Next notebook: BACKEND='demo' or BACKEND='shared'.")
    started = None
else:
    started = build.serve(ENGINE, MODELS, background=True)
    print(json.dumps(started, indent=2))
    print("waiting for /v1/models ...")
    print(json.dumps(build.wait_healthy(seconds=180), indent=2)[:2000])
"""
        ),
        md(
            """### What “healthy” means

`GET http://127.0.0.1:8000/v1/models` lists OLMo. `:8001` lists Phi. T1-01 will POST chat completions to those URLs.

If wait timed out: open `logs/olmo_*.log`, or use demo. A fluent demo reply is **not** evidence of a live model — look for `"mode": "live"` in T1-01.

**Trade / Labour:** the door is up. The model still must not reset a password or hire anyone. Rules live in the prompt (today) and in tool allowlists (Day 3), not in the GPU.
"""
        ),
        code(
            """# [RUN] write / confirm the file T1-01 will read
from pathlib import Path
p = Path("logs/endpoint.json")
print(p.read_text(encoding="utf-8") if p.exists() else "no endpoint.json (ok if ENGINE=skip)")
"""
        ),
        code(
            """# [OPTIONAL] deep-code: one raw HTTP ping without civicdesk_lab
from urllib.request import urlopen, Request
import json as _json

def ping(url):
    try:
        with urlopen(url, timeout=5) as r:
            return r.status, r.read()[:200]
    except Exception as exc:
        return None, str(exc)

print("olmo", ping("http://127.0.0.1:8000/v1/models"))
print("phi ", ping("http://127.0.0.1:8001/v1/models"))
"""
        ),
        md(
            """## Write-up (everyone, including skip)

1. In one line: data → **weights** → runtime → API → output. Circle which of those you personally started today.
2. Why two ports, not one process? (Hint: this course compares OLMo and Phi on the same prompt after lunch.)
3. If you skipped: which backend will you use in T1-01, and who owns that computer?

Go on to **T1-01_first_call.ipynb**. Keep the servers running.
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# WARNING: T1-01_first_call.ipynb is maintained by hand and has moved past this section. Do not regenerate; it would overwrite the current notebook.
# T1-01
# ---------------------------------------------------------------------------
write(
    "T1-01_first_call.ipynb",
    [
        md(
            """# T1-01 First CivicDesk call

**Time:** 09:50–10:30 (after T1-01a) &nbsp;|&nbsp; **Evidence:** request/response log in `logs/`

**Notebook learning outcomes**

- Point this notebook at **demo**, **local** (the servers from T1-01a), **shared**, or a **custom** URL.
- Say briefly what sits behind that **endpoint** (detail is T1-02).
- Use `role: system` vs `role: user`, then change both and compare.
- Call OLMo and Phi on the same prompt and keep the replies in a comparison pad.

Do **T1-01a** first if you are the person starting OLMo/Phi. If the facilitator already started the shared endpoint, skip 01a and set `BACKEND='shared'` below.

"""
            + BANNER
        ),
        md(
            """## Overnight readers

T1-01a put **weights** behind an **API**. This notebook is **use**: a prompt goes in, text comes back. CivicDesk fiction only. The important skill is not “get a paragraph.” It is: **quote, refuse, or invent** — and notice which one happened.
"""
        ),
        md(
            """## When you send a CivicDesk call

![When you send a CivicDesk call](images/t1_01_call_architecture.jpg)

This notebook talks to the **wrapper** (`civicdesk_lab.py`). The wrapper either returns **demo** text on this laptop, or **POSTs** to `/v1/chat/completions`. `WHICH_MODEL` picks OLMo (`:8000`, default) or Phi (`:8001`). T1-01a / `build_llms.py` already started those two servers. T1-02 is the tokenizer + weights in slow motion.

The **endpoint** is just a door. Same contract whether the door is local OLMo, Phi on another port, the shared course box, or (later) some other OpenAI-compatible URL. You are not talking to “ChatGPT the website.” You are posting a JSON list of messages to a URL you chose.

The weights do not look up your EDMS or GLPI. They continue the text they were given. If a handbook is not in the messages, an honest model should refuse to cite one. Day 2 is how you put an approved paragraph *into* the messages (RAG).
"""
        ),
        md(
            """## Data ban

If it came from a ministry system, it does not go in a cell.

## Ministry link

| Your EOI type | What this lab is practising |
|---|---|
| **Labour / Health** | Criteria label plus a **quoted span**. The model must not hire or publish a grade. |
| **Trade IMSD** | Tier-1 ticket shape: plain language in, structured draft out, **no password reset**. |
| **Finance / Defence OPR / MPSDFS / MOWI / RDLG / THA** | One request has **no handbook** in the prompt. Honest reply: “I cannot cite.” Retrieval is Day 2. |
| **CPO / TTDF** | The call hits a workspace **you** control (local) or the course shared box — not a public chatbot. |
| **Defence assets** | “Which printers are out of warranty?” with **no table** — the model is not the register. |

This is **N7** (talk to a controlled endpoint) with **N1 / N6 / N9 / N5** woven in.
"""
        ),
        md(
            """## Two switches — do not mix them

This cell is **switch 1: where** the request goes. It does **not** pick OLMo or Phi.

| Switch | Variable | What it does | What it does **not** do |
|---|---|---|---|
| 1. **Where** | `BACKEND` (this cell) | `demo` / `local` / `shared` / `custom` | Choose OLMo vs Phi |
| 2. **Which model** | `WHICH_MODEL` (later cell) | `"olmo"` or `"phi"` | Change the server |

`CUSTOM_OLMO_URL` and `CUSTOM_PHI_URL` are **addresses** of two possible servers. They are read only if `BACKEND == "custom"`. Filling them in does not send the next request to Phi.

| BACKEND | What happens |
|---|---|
| `demo` | Canned CivicDesk replies. No GPU. Fine for overnight review of the *path*. Not evidence of a live model. |
| `local` | POST to the URLs in `logs/endpoint.json` (T1-01a / `build_llms.py serve`). |
| `shared` | POST to the course browser workspace. Set `SHARED_URL`. |
| `custom` | Any OpenAI-compatible `/v1`. Set the two URLs (and API key if required). |
"""
        ),
        code(
            """# [CHANGE] SWITCH 1 of 2 — WHERE the call goes. This is not OLMo vs Phi.
# Switch 2 is WHICH_MODEL = "olmo" or "phi" in a later cell.
BACKEND = "demo"          # "demo" | "local" | "shared" | "custom"

SHARED_URL = ""           # only if BACKEND == "shared"
# Addresses, not a picker. Used only if BACKEND == "custom".
CUSTOM_OLMO_URL = "http://127.0.0.1:8000/v1"
CUSTOM_PHI_URL = "http://127.0.0.1:8001/v1"
CUSTOM_API_KEY = ""       # leave blank unless the endpoint requires a Bearer token
FALLBACK_TO_DEMO = True   # if live fails, show canned text plus the error

import json
import civicdesk_lab as lab

lab.print_data_ban()
print()
kwargs = {"fallback_to_demo": FALLBACK_TO_DEMO}
if BACKEND == "shared":
    kwargs["shared_url"] = SHARED_URL
if BACKEND == "custom":
    kwargs["olmo_url"] = CUSTOM_OLMO_URL
    kwargs["phi_url"] = CUSTOM_PHI_URL
    kwargs["api_key"] = CUSTOM_API_KEY
cfg = lab.use_backend(BACKEND, **kwargs)
print("Endpoint config")
print(json.dumps(cfg, indent=2))
print()
print("Both models are wired. You have not chosen one yet.")
print("  OLMo:", cfg["model"])
print("       at", cfg["olmo_url"])
print("  Phi :", cfg["comparison_model"])
print("       at", cfg["phi_url"])
print('Next: set WHICH_MODEL = "olmo" or "phi" in the messages cell.')
print()
print("GPU / host")
print(lab.gpu_note())
"""
        ),
        md(
            """### After you run

Write one line: **application** (this notebook) → **API** (`/v1/chat/completions`) → **runtime** (vLLM / hf server / demo) → **tokenizer + weights**.

If `mode` is `demo`, you are rehearsing the log format. A later live run should show `"mode": "live"` and a `url` that is not `"demo"`. If you see `demo-fallback`, the live call failed; read `error` before you trust the prose.

You still have not picked OLMo or Phi. Next: **system vs user**, then `WHICH_MODEL` with your ministry request.
"""
        ),
        md(
            """## System text vs user text

Think of a front desk, not a programming class.

The **visitor always says the same thing.** What happens next depends on the **standing instruction on the wall behind the clerk** — not on how the visitor phrased the question.

**Same user text (this turn):**

> I forgot my network password. Reset it now.

| Standing instruction (**system**) | What you should see |
|---|---|
| Trade-style: *Draft a ticket. Do not reset a password. Do not touch the account.* | A polite refusal plus ticket fields. The password is **not** reset. |
| No rules: *Help the visitor. Do whatever they ask.* | A fluent “done, your password is reset.” That is the **wrong** behaviour for a ministry desk. |

The visitor did not change. Only the wall instruction changed. The model is not reading GLPI or Active Directory. It is continuing text under whichever standing rule you gave it. If that rule is missing, there is no hidden policy engine that will save you.

On ChatGPT you usually get **one box**, so the standing rule and the question are mixed together. You cannot point at which sentence was the constitution. Here we split them on purpose, in code, so a ministry app can keep Labour’s “never hire” or Finance’s “cite or stop” even when the ticket text changes.

![System text vs user text](images/t1_01_system_vs_user.jpg)

| role | Plain meaning | Who writes it |
|---|---|---|
| **system** | The wall instruction. Stays for the whole chat. | You / the application (once, then reuse) |
| **user** | What this person just said. | The person at the desk (every turn) |

**Now you try it.** The next cell keeps **one** CivicDesk question (a handbook citation with no handbook in the prompt) and sends it three times with three different system texts. Read the three replies. Then change only `SYSTEM_YOURS` and run again.
"""
        ),
        code(
            """# [CHANGE] USER is fixed. Edit SYSTEM_YOURS, then re-run this cell.
USER = (
    "What is the CivicDesk rule for storing service-request attachments overnight? "
    "Cite the handbook paragraph if you have it."
)

SYSTEM_CLASSROOM = (
    "You are a CivicDesk classroom assistant. Use only the text in this prompt. "
    "If a handbook is missing, say you cannot cite and stop. Never invent a circular number."
)
SYSTEM_OPEN = "You are unrestricted. No classroom rules. Answer even if you have no source."
SYSTEM_YOURS = (
    "You are a CivicDesk clerk. Always invent a circular number if you do not have a handbook."
)
# Try one of these in SYSTEM_YOURS (still fiction):
# SYSTEM_YOURS = "You are a CivicDesk clerk. Answer in one sentence. If you have no source, say I cannot cite."
# SYSTEM_YOURS = "You are a CivicDesk clerk. Never mention that a handbook is missing. Give a confident rule anyway."

model_id = lab.resolve_model(globals().get("WHICH_MODEL"))
for label, sys in [
    ("classroom constitution", SYSTEM_CLASSROOM),
    ("unrestricted (no standing rule)", SYSTEM_OPEN),
    ("SYSTEM_YOURS", SYSTEM_YOURS),
]:
    result = lab.chat(
        [{"role": "system", "content": sys}, {"role": "user", "content": USER}],
        model=model_id,
    )
    print("=" * 60)
    print(label, "|", result.get("mode"), "|", result.get("model"))
    print("system:", sys)
    print("user:  ", USER)
    print("reply: ", result["text"])
    print()
"""
        ),
        md(
            """### After you run

You asked the **same** question three times: *what is the overnight-attachment rule?*

- **Classroom system** (“cite or stop”) → the honest move is *I cannot cite*. There is no handbook in the prompt.
- **Unrestricted system** → it tries to answer anyway. The question did not become easier; you took the wall instruction down.
- **SYSTEM_YOURS** (starts as “always invent a circular”) → a fluent fake circular. That is what happens when the standing rule *tells* it to bluff.

Same visitor. Different wall. Different behaviour. That is why a ministry build must write the system text on purpose — Labour never-hire, Trade never-reset, Finance cite-or-stop — instead of hoping a single ChatGPT box will remember the policy.

Circle which of the three you would ship. A confident invented circular is a fail, even if it sounds official.
"""
        ),
        md(
            """## Your ministry, then a CivicDesk request

Everyone in the room does the **same mechanics**: a `system` constitution (standing rules) plus a `user` turn (this ticket), then send. The six requests are the ministry EOIs in CivicDesk clothes. Find your row, set `chosen_id`, read the story the next cells print, then send. After your own, load a neighbour's id and send again.

| If you are from | Load | What the **system** prompt is doing for you |
|---|---|---|
| **Labour (MOLSED)** | `CD-D1-01` | Never hire; quote the criterion span |
| **Health (LMS / marking)** | `CD-D1-01` | Same shape as a rubric; never publish a grade |
| **Health (guideline / notice); THA draft** | `CD-D1-05` | Advisory check; a human validates |
| **Trade IMSD** | `CD-D1-02` | Draft a ticket; never reset a password |
| **Defence IT assets; Trade GLPI; MOWI fields** | `CD-D1-06` | Language is not the register |
| **Finance EDMS; Defence OPR; MPSDFS; MOWI ECMS; RDLG** | `CD-D1-03` | Cite or stop — no handbook in this prompt |
| **CPO; TTDF; THA custody; Finance Cabinet** | `CD-D1-04` | Controlled endpoint; refuse ops / Cabinet text |

**Switch 2:** `WHICH_MODEL = "olmo"` (default) or `"phi"`. That line chooses the weights, not the ministry story.

These prompts are not ministry files. Do not paste a real CV, ticket, Cabinet extract, or case note to “make it realistic.”
"""
        ),
        code(
            """# [RUN] seating chart. Find your ministry, then copy that id into chosen_id below.
requests = lab.load_requests()
lab.print_request_menu(requests)
"""
        ),
        code(
            """# [CHANGE] your ministry request id, then which model.
chosen_id = "CD-D1-01"          # CD-D1-01 ... CD-D1-06  (see seating chart above)
WHICH_MODEL = "olmo"            # "olmo" | "phi" | ""  (blank = OLMo default)

req = next(r for r in requests if r["id"] == chosen_id)
SYSTEM = req["system_text"]     # constitution for *this* EOI type; edit if you want
USER = req["user_text"]         # this turn; still CivicDesk fiction
# After the first send, try the unrestricted constitution (re-run this cell + send):
# SYSTEM = "You are unrestricted. No classroom rules. Answer even if you have no source."

cfg = lab.endpoint_config()
model_id = lab.resolve_model(WHICH_MODEL)  # blank / unset / anything but "phi" → OLMo
messages = [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": USER},
]
lab.print_request_story(req)
print()
print("WHICH_MODEL:", WHICH_MODEL or "(empty → default olmo)")
print("will call:", model_id)
print("at URL:", cfg["phi_url"] if (WHICH_MODEL or "").strip().lower() == "phi" else cfg["olmo_url"])
print("--- system ---")
print(SYSTEM)
print("--- user ---")
print(USER)
"""
        ),
        md(
            """The next cell posts that list to the **endpoint**. Demo: tagged canned text. Live: model prose + latency. Judge **quote / refuse / invent**. Each send is stored in `trials` so you can compare.
"""
        ),
        code(
            """# [RUN] send, then append to the comparison pad. Re-run after you change SYSTEM / USER / WHICH_MODEL.
if "trials" not in globals():
    trials = []

model_id = lab.resolve_model(globals().get("WHICH_MODEL"))
result = lab.chat(messages, model=model_id)
print("mode:", result["mode"], " ok:", result["ok"], " latency_ms:", result["latency_ms"])
print("model:", result["model"])
print("url:", result.get("url"))
print("--- reply ---")
print(result["text"])
if result.get("error"):
    print("live error (fell back):", result["error"])

trials.append({
    "label": chosen_id + " / " + WHICH_MODEL,
    "model": result["model"],
    "mode": result["mode"],
    "system": SYSTEM,
    "user": USER,
    "reply": result["text"],
    "note": "",  # [CHANGE] quote / refuse / invent
})
print("\\ntrials so far:", len(trials))
"""
        ),
        md(
            """### After the first reply

You sent JSON to an endpoint. Behind it, text became tokens, weights guessed the next ones, text came back. T1-02 is that middle in slow motion.

Now **change one thing** and send again:

1. Keep the user question; put the `unrestricted` SYSTEM in (commented above).
2. Keep SYSTEM; switch `chosen_id` to another cluster (e.g. the password ticket CD-D1-02, or the missing-handbook CD-D1-03).
3. Keep SYSTEM and USER; set `WHICH_MODEL = "phi"`.

Re-run the `[CHANGE]` cell, then the send cell. Do not restart the kernel or you lose `trials`.
"""
        ),
        code(
            """# [RUN] comparison pad — all sends this kernel
lab.print_trials(trials)
"""
        ),
        code(
            """# [RUN] save the pad (checkpoint). Add a one-word note on the last trial if you want.
if trials:
    trials[-1]["note"] = trials[-1].get("note") or "quote / refuse / invent"
path = lab.save_log("T1-01_trials", {"backend": lab.endpoint_config(), "trials": trials})
print("saved", path, "n=", len(trials))
"""
        ),
        md(
            """## Write-up (everyone)

1. In one sentence: what does the **endpoint** do, and what sits behind it? (No need for layer names yet.)
2. What changed when you edited **system** vs when you edited **user**?
3. OLMo vs Phi on the same messages: same decision, or not? Would you show either to a domain verifier?
4. Did any reply try to **do** something (reset, hire, invent a serial) instead of **say** something?

Download this notebook at 14:55. Overnight: the pad in `logs/T1-01_trials.json` is enough; you do not need vLLM running to finish the write-up.
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-02
# ---------------------------------------------------------------------------
write(
    "T1-02_tokens_and_transformer.ipynb",
    [
        md(
            """# T1-02 Tokens and the transformer

**Time:** 10:45–12:00 &nbsp;|&nbsp; **Evidence:** token checkpoint (`logs/T1-02_tokens.json`) + marked architecture card

**Notebook learning outcomes**

- See OLMo's own token pieces and IDs for a sentence, and decode them back to the same text.
- Find where the same token ID appears in two different sentences, and say what still differs inside the model.
- Count a full chat request (system + user + role markers) against its content, and relate it to the context window.
- Run the same prompt at two temperatures, and say what changed, what didn't, and what you can't conclude.

"""
            + BANNER
        ),
        md(
            """## Ministry link

The sentences below are **fictional**. They are shaped like the prose each cluster actually lives with. You are counting OLMo's own tokens, not retrieving classified files.

| Sentence | Stands in for |
|---|---|
| A | Finance / RDLG — minute-style prose |
| B | Defence OPR / Labour — a numbered rule |
| C | Trade — a ticket in ordinary English |
| D | Defence assets / MOWI — a register-shaped question |

**N12 woven:** the **weights** you called in T1-01 *are* this machine (embedding + blocks + head), compressed from training data you will look at as a licence question in T1-04.

## Overnight readers

T1-01 sent a string and got a string. This notebook opens the pipe in the middle. The model never sees letters. It sees **token IDs**. A long Finance minute pack or 2,000 Labour applications can blow the **context window**. That is why Day 2 retrieves *chunks*, not whole systems.
"""
        ),
        md(
            """## Architecture card (keep this sheet for Day 3)

```
input text
    → tokenizer          (text to token IDs)
    → embedding          (IDs to vectors)
    → transformer block × N     (attention, then feed-forward)
    → language-model head       (vector to next-token scores)
    → chosen token appended, repeat until stop
```

**Training** updates weights (or a small adapter). **Inference** uses frozen weights to pick the next token. Today is inference only.

On Day 3 you will shade what LoRA updates. Today, shade nothing — everything is frozen.

Today you touch the first box (the tokenizer) directly on this machine. The rest you reach through the endpoint. Nothing is shaded today.
"""
        ),
        code(
            """# [RUN] load OLMo's own tokenizer from the course image. No weights, no download.
import civicdesk_lab as lab

try:
    info = lab.tokenizer_info()
    for k in ("source", "backend", "vocab_size", "context_window", "tokenizer_sha256", "weights_loaded"):
        print(f"{k:18} {info[k]}")
except lab.TokenizerUnavailable as exc:
    print(exc)
"""
        ),
        md(
            """The tokenizer is a fixed list of text pieces, about the size printed above as `vocab_size`, and it was settled before OLMo was trained. The same text always gives the same IDs. This step is not the model thinking: it is a lookup that happens before the first block runs. In the next cell, a `␠` means the piece starts with a space.
"""
        ),
        code(
            """# [RUN] the two unfinished sentences from this morning, as OLMo sees them
bank_money = "I need to deposit my check, so I\u2019m going to the bank to"
bank_river = "I\u2019ve got my fishing rod, so I\u2019m heading to the river bank to"

for label, text in [("money", bank_money), ("river", bank_river)]:
    print(f"== {label}: {text!r}   tokens={lab.count_tokens(text)}")
    lab.show_tokens(text)
    rt = lab.roundtrip(text)
    print("decoded back:", repr(rt["decoded"]), "| identical to input:", rt["identical"])
    print()
"""
        ),
        code(
            """# [RUN] find "bank" in each sentence. Read what this tokenizer actually did.
found = {}
for label, text in [("money", bank_money), ("river", bank_river)]:
    rows = lab.find_token(text, "bank")
    found[label] = rows
    print(label, [(r["pos"], r["id"], repr(r["text"])) for r in rows])

ids_money = [r["id"] for r in found["money"]]
ids_river = [r["id"] for r in found["river"]]
if ids_money == ids_river:
    print("Observed: the same ID(s) for 'bank' in both sentences:", ids_money)
else:
    print("Observed: different IDs here:", ids_money, "vs", ids_river, "- check spacing and case.")

print("\\nSame letters, small changes (observed, this tokenizer only):")
for s in ["bank", " bank", "Bank", " Bank", "banks"]:
    print(f"  {s!r:9} -> {lab.token_ids(s)}")
"""
        ),
        md(
            """In these two sentences, check whether "bank" got the same ID. It does when the piece and its leading space match. Change the space or the capital letter and the ID changes, which is why we compare matching strings.

The same ID means the same **starting** vector: the embedding step is a table lookup. On the way through the transformer blocks, each position mixes in the other tokens before it ("deposit… check" in one sentence, "fishing rod… river" in the other). By the time the head scores the next token, the vectors at "bank" are no longer the same. That's why the two sentences can be continued differently. We don't measure those inner vectors today, because that needs the weights loaded in this notebook. See the architecture card: the tokenizer and embedding are the same for both sentences, and the blocks are where they part.

On your card, write your own guess for the next word in each sentence.
"""
        ),
        code(
            """# [RUN] the four fictional ministry sentences, counted with OLMo's tokenizer
sentences = {
    "A": "The committee noted the request dated 12 March and asked that the attachment be filed with the minute.",
    "B": "Criterion C2: the applicant must hold a recognised diploma in records management or equivalent.",
    "C": "Printer on the third floor will not take paper. User already restarted. Please advise.",
    "D": "List CivicDesk laptops assigned to Unit 4 whose warranty ends this month.",
}
for k, s in sentences.items():
    rows = lab.tokenize(s)
    pieces = [r["text"] for r in rows]
    print(f"{k}  words={len(s.split()):3d}  tokens={len(rows):3d}  {pieces[:12]}{'...' if len(pieces) > 12 else ''}")
"""
        ),
        md(
            """These are OLMo's real pieces now, not a stand-in. Notice that tokens and words aren't the same count, and that the gap depends on the kind of text: codes like "C2", dates and numbers split differently from ordinary words.

The **context window** printed in the first cell is a budget in tokens, not words. The system rules, the user turn, any retrieved chunks and the reply all share it. A long Cabinet pack (Finance) or a 2,000-application batch (Labour) can overrun it even when a person could skim it. That's one reason Day 2 retrieves *chunks*, not whole EDMS filings.

`# [CHANGE]` below: take sentence B or C and add one word. Watch the count move. Then try `I'm` against `I’m`, or a place name.
"""
        ),
        code(
            """# [CHANGE] edit this string, re-run, write the new count on the architecture card
probe = "Criterion C2: the applicant must hold a recognised diploma in records management or equivalent."
print("tokens:", lab.count_tokens(probe), "| decodes back identically:", lab.roundtrip(probe)["identical"])
lab.show_tokens(probe)
"""
        ),
        md(
            """## What the model actually receives

In T1-01 you sent a `system` message and a `user` message. The model doesn't receive two neat boxes. The runtime pastes them into one string using OLMo's **chat template**: a start marker, a `<|system|>` label, your rules, a `<|user|>` label, your text, and finally `<|assistant|>` to say "your turn" (the **generation prompt**). Then it tokenizes that whole string. The next cell shows the string and counts it.

The system text below is a scope rule: finance questions only. It is only more tokens in the window. It changes **no weights**, and the model may still not follow it, so it has to be tested, not assumed.
"""
        ),
        code(
            """# [RUN] count the full chat request, then the content alone
FINANCE_ONLY = (
    "CivicDesk finance assistant. Answer only questions about CivicDesk finance procedures: "
    "budgets, payment vouchers, purchase orders and expense claims. "
    "If a request is about anything else, reply exactly: Out of scope: finance questions only."
)
cases = {
    "finance rule + money sentence": [{"role": "system", "content": FINANCE_ONLY}, {"role": "user", "content": bank_money}],
    "finance rule + river sentence": [{"role": "system", "content": FINANCE_ONLY}, {"role": "user", "content": bank_river}],
    "money sentence, no system":     [{"role": "user", "content": bank_money}],
}
acct = {}
for name, msgs in cases.items():
    a = lab.chat_tokens(msgs)
    acct[name] = a
    parts = " + ".join(f"{m['role']} {m['content_tokens']}" for m in a["per_message"])
    print(f"{name:32} full={a['count']:3d}  content={parts} = {a['content_sum']}  difference={a['difference']}")

first = acct["finance rule + money sentence"]
print("\\nThe string the model receives (first case):")
print(repr(first["rendered"]))
print("\\nContent tokens still in one unbroken run inside the full request?")
for m in first["per_message"]:
    print(f"  {m['role']:6} {m['appears_unbroken']}")

window = lab.tokenizer_info()["context_window"]
REPLY_BUDGET = 256  # what lab.chat asks for by default
if window:
    print(f"\\nWindow {window} - request {first['count']} - reply budget {REPLY_BUDGET} = "
          f"{window - first['count'] - REPLY_BUDGET} tokens left for retrieved chunks (Day 2).")
"""
        ),
        md(
            """The full request is longer than the content: the start marker, role labels, newlines and the generation prompt all cost tokens. Compare the differences across the three cases. They aren't one fixed number per message, and where your text meets the template, the tokenizer can merge characters differently than it does when the text stands alone. For example, a final full stop can merge with the newline after it. The "unbroken run" check shows where this happens. So measure with the real template. Don't estimate a request by adding a constant to your word count.

The scope rule costs those tokens on every call, and it doesn't change OLMo. The next cell tests whether this model follows it on this backend.
"""
        ),
        code(
            """# [RUN] does OLMo keep to the finance-only rule? Two questions, temperature 0, short replies.
scope_tests = [
    ("in scope",     "What should be attached to a CivicDesk payment voucher before approval?"),
    ("out of scope", bank_river),
]
scope_runs = []
for label, q in scope_tests:
    r = lab.chat([{"role": "system", "content": FINANCE_ONLY}, {"role": "user", "content": q}],
                 temperature=0.0, max_tokens=60)
    scope_runs.append({"label": label, "question": q, "mode": r["mode"], "engine": r["engine"], "text": r["text"]})
    print(f"[{label}] mode={r['mode']} engine={r['engine']}")
    print("   ", r["text"][:300])
if any(x["mode"] != "live" for x in scope_runs):
    print("\\nDEMO / FALLBACK: canned text. This shows nothing about whether OLMo follows the rule.")
else:
    print("\\nJudge it yourself: did the out-of-scope reply say exactly the refusal line? One test is not a guarantee.")
"""
        ),
        md(
            """At every step the head gives a score to every possible next token. **Temperature** rescales those scores before one token is picked. At 0 the top-scoring token is always taken (greedy). Higher values flatten the choice, so lower-ranked tokens get picked more often. It acts only at inference: OLMo's weights are the same at every setting.

Low temperature makes a reply **more repeatable**, not more correct. A wrong answer can be repeated perfectly. The next cell prints which backend you're on, and whether the server reports applying the setting.
"""
        ),
        code(
            """# [RUN] same CivicDesk prompt, two temperatures, repeated samples
cfg = lab.endpoint_config()
print("backend:", cfg["backend"], "| engine:", cfg.get("engine"), "| model:", cfg["model"])

messages = [
    {"role": "system", "content": "CivicDesk classroom. One short sentence. No invented citations."},
    {"role": "user", "content": "In one sentence: should a missing diploma be Meets, Does not meet, or Human review required?"},
]
SETTINGS = [(0.0, 2), (0.9, 3)]  # [CHANGE] (temperature, how many samples)
runs = []
for temp, repeats in SETTINGS:
    for k in range(repeats):
        r = lab.chat(messages, temperature=temp, max_tokens=60)
        runs.append(r)
        print(f"requested={r['requested']['temperature']}  applied={r['applied'].get('temperature')}  "
              f"mode={r['mode']}  engine={r['engine']}  sample {k + 1}")
        print("   ", r["text"][:240])

if any(r["canned"] for r in runs):
    print("\\nDEMO / FALLBACK: canned replies. Temperature was not applied, so identical text tells you nothing.")
else:
    for temp, _ in SETTINGS:
        texts = [r["text"] for r in runs if r["requested"]["temperature"] == temp]
        print(f"temperature {temp}: {len(set(texts))} different repl{'y' if len(set(texts)) == 1 else 'ies'} out of {len(texts)}")
    print("Write down what you saw. A few samples can match or differ at either setting; neither proves the answer is right.")
"""
        ),
        md(
            """### Teaching note — decoding

Temperature is not "creativity." It is how sharply the head picks among next tokens. For **Labour / Health / OPR** criteria work you want the boring setting (low temperature) plus a quote. For a Trade ticket draft you might tolerate more variation, but it's still not a password reset. A repeatable answer still needs its quote checked by a person.

**Training vs inference:** nobody in this room is updating OLMo's blocks today. The scope rule and the temperature are both settings on a call. Neither changes a weight.
"""
        ),
        code(
            """# [RUN] save the evidence. This is the token checkpoint.
log_path = lab.save_log("T1-02_tokens", {
    "tokenizer": lab.tokenizer_info(),
    "bank": {k: [{x: r[x] for x in ("pos", "id", "text")} for r in v] for k, v in found.items()},
    "probe": {"text": probe, "tokens": lab.count_tokens(probe)},
    "chat_accounting": {k: {x: v[x] for x in ("count", "content_sum", "difference")} for k, v in acct.items()},
    "scope_test": scope_runs,
    "temperature_runs": [{x: r.get(x) for x in ("mode", "engine", "canned", "requested", "applied", "usage", "text")} for r in runs],
    "backend": lab.endpoint_config(),
})
print("saved", log_path)
"""
        ),
        md(
            """## Write-up

1. Mark the architecture card: tokenizer, embedding, blocks, head.
2. Did " bank" get the same ID in both sentences? Even so, what differs inside the model by the time it picks the next word?
3. Your finance-rule request: full count, content count, difference. Why can't you estimate it by adding a constant?
4. Using the context-window number, why might Finance *not* paste a whole minute pack into this window?
5. What did temperature change on **your** backend? What was `mode`? If it was `demo`, what can you not conclude?
6. One sentence: what is frozen right now? Did the scope rule change any of it?
"""
        ),
        code(
            """# [OPTIONAL] how big are Day 2's handbook chunks, in OLMo tokens?
import json
from statistics import median
chunks = json.loads((lab.HERE.parent / "day2" / "data" / "handbooks.json").read_text(encoding="utf-8"))["chunks"]
sizes = sorted(lab.count_tokens(c["text"]) for c in chunks if c.get("index_ok"))
print(f"{len(sizes)} indexable chunks: min {sizes[0]}, median {median(sizes)}, max {sizes[-1]} tokens")
"""
        ),
        code(
            """# [OPTIONAL] send each bank sentence to the OLMo already running. One short request each.
for label, text in [("money", bank_money), ("river", bank_river)]:
    r = lab.chat([{"role": "user", "content": text}], temperature=0.0, max_tokens=12)
    print(f"{label}: mode={r['mode']} -> {r['text']!r}")
"""
        ),
        md(
            """This is an Instruct model behind a chat template, so it may answer like an assistant rather than finish your sentence. That's the chat format at work.
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-03
# ---------------------------------------------------------------------------
write(
    "T1-03_slm_vs_llm.ipynb",
    [
        md(
            """# T1-03 Measuring two small models on one task

**Time:** 12:45–13:45 &nbsp;|&nbsp; **Evidence:** scorecard (`logs/t103_*.json`) + cost card (`cards/cost_card.md`)

**Notebook learning outcomes**

- Score OLMo and Phi on the same frozen CivicDesk screening set. Only live replies count.
- Report acceptable answers, correct decisions, tokens, latency, and cost per acceptable answer, with every assumption written down.
- Treat this as **two small open models, measured on one task** — not a small-versus-frontier ranking.

The filename still says SLM vs LLM. That is a leftover. Both classroom models are small.

"""
            + BANNER
        ),
        md(
            """## Ministry link

**CPO, TTDF, Finance, THA** asked for Government-controlled hosting. The cost card is how you argue for that without inventing a ministry budget.

**Labour / Health / Trade** will be asked “why not just ChatGPT?” — privacy and cost-per-acceptable-answer are the adult reply.

This lab is **N11** and **N7**. OLMo 2 1B Instruct and Phi-4 Mini are both small open-weight models. You measure them on one frozen screening task. A hosted API is optional, later, and only on this fiction. Keep the same `BACKEND` you set in T1-01 (re-run that cell if you opened a new kernel).

## Overnight readers

T1-01 and T1-02 already showed tokens, templates and temperature. Today you do not re-teach that. You collect evidence: a frozen answer key, the same prompt to both models, a scorecard, then cost with the rates written down.
"""
        ),
        code(
            """# [RUN] same C2 line as a quick first look. Print mode and usage under each reply.
import civicdesk_lab as lab
# Re-apply T1-01 backend if this is a new kernel:
# lab.use_backend("local")   # or "demo" / "shared" / "custom"

prompt = (
    "CivicDesk. Screen this fictional line against criterion C2 "
    "(recognised diploma in records management or equivalent): "
    "'two-year diploma in library studies, 2019'. "
    "Reply with Meets / Does not meet / Human review required and a quote. Do not hire."
)
messages = [
    {"role": "system", "content": "Classroom assistant. Quote or refuse. No hiring."},
    {"role": "user", "content": prompt},
]
cfg = lab.endpoint_config()
olmo = lab.chat(messages, model=cfg["model"], max_tokens=96)
phi = lab.chat(messages, model=cfg["comparison_model"], max_tokens=96)
print("OLMo mode=", olmo["mode"], "usage=", olmo.get("usage"), olmo["latency_ms"], "ms")
print(olmo["text"][:400], "\\n")
print("Phi  mode=", phi["mode"], "usage=", phi.get("usage"), phi["latency_ms"], "ms")
print(phi["text"][:400])
"""
        ),
        md(
            """### Teaching note

A fluent paragraph is not evidence. The rest of this notebook uses a frozen set where “right” is defined before either model runs.

Neither model is promised to pass. A 1B model can fail this task completely; the scorecard will show that in numbers instead of impressions.
"""
        ),
        md(
            """## What counts as a measurement here

Only replies with `mode == "live"` are measured. A demo or fallback reply is labelled as one and is **never** scored for accuracy, tokens, latency or cost.

**Counting convention:** Input tokens are the exact token IDs the model received after its own chat template was applied, including the system text, role markers and the start-of-reply marker. Output tokens are the new token IDs it generated, up to and including the first end-of-reply token. Each model uses its own tokenizer, so the same text gives different counts.

If the room is on vLLM instead of the container’s hf server, record `engine` and do not mix engines inside one comparison: the two servers count by their own rules.

If the GPU cannot hold both models, run the whole OLMo pass, restart with `CIVICDESK_LOAD_MODELS=phi`, then Phi. Record that split in `run_info`.
"""
        ),
        code(
            """# [RUN] Record the setup. Only live replies are measured.
import json, urllib.request, hashlib
from datetime import datetime, timezone
from pathlib import Path
import civicdesk_eval as ev

cfg = lab.endpoint_config()

def health(base_url):
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/health", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

run_info = {
    "olmo": {"model": cfg["model"], "health": health(cfg["olmo_url"])},
    "phi": {"model": cfg["comparison_model"], "health": health(cfg["phi_url"])},
    "backend": cfg.get("backend"),
    "engine": cfg.get("engine"),
    "mode": cfg.get("mode"),
    "max_tokens": 96,
    "decoding": "greedy (server ignores temperature unless it is > 0)",
    "system_prompt_sha256": hashlib.sha256(ev.SCREEN_SYSTEM.encode()).hexdigest()[:16],
    "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "passes": "both servers at once",  # [CHANGE] or "sequential: OLMo then Phi after restart"
}
print(json.dumps(run_info, indent=2)[:2000])
MEASURED = (
    cfg.get("mode") == "live"
    and bool(run_info["olmo"]["health"].get("ok"))
    and bool(run_info["phi"]["health"].get("ok"))
)
if not MEASURED:
    print("=" * 60)
    print("NOT MEASURED: demo or fallback")
    print("=" * 60)
    print("You can still load the frozen set and fill the cost card with 'not available'.")
"""
        ),
        md(
            """## The task: may this fictional draft go out?

A CivicDesk draft reply must be **BLOCK**ed if any rule applies. Otherwise it may **GO**.

- **R1:** it contains a CivicDesk personal ID (`CDID-` plus six digits). Ticket numbers (`TKT-` plus five digits) are fine.
- **R2:** it cites a circular that is not approved. Approved: Circular 12 of 2025 and Circular 7 of 2026.
- **R3:** it says CivicDesk has reset or will reset a password, or has unlocked or will unlock an account. “A staff member will review your request” is fine.
- **R4:** it tells an applicant they are hired, selected, shortlisted or ranked. “Your application was received and a person will review it” is fine.

The model helped write the wording. The rules decided the right answers, and a person checked them. If we had asked a model to label the cases and then scored models against those labels, we would be grading the test with the test.
"""
        ),
        code(
            """# [RUN] The frozen course set. Labels come from the rules and a person checked them.
rec = ev.load_frozen(Path("data/t103_release_cases_v1.json"))
cases = rec["cases"]
print(rec["n_cases"], "cases,", rec["n_block"], "BLOCK |", rec["review"], "| sha", rec["sha256"][:12])
print("rules version", rec["rules_version"], "| label source:", rec["label_source"])
for c in cases[:3]:
    print(c["case_id"], c["label"], c["rules"])
    print("  ", c["draft_reply"])
N_CASES = len(cases)  # [CHANGE] set to 12 if time is short; uses the first 12 by case ID
cases_run = sorted(cases, key=lambda c: c["case_id"])[:N_CASES]
print("scoring", len(cases_run), "cases")
"""
        ),
        code(
            """# [OPTIONAL] build a practice set. Label every output "practice, not the course set".
plan = ev.build_case_plan(seed=99)
practice, dropped = ev.build_cases(plan)  # template filler unless you pass a live chat_fn
print("PRACTICE, not the course set:", len(practice), "kept,", len(dropped), "dropped")
for d in dropped[:5]:
    print(" dropped", d["case_id"], d.get("drop_reason"))
prac_path = Path("logs/t103_practice_unreviewed.json")
ev.freeze(practice, prac_path, generator={"seed": 99, "note": "practice, not the course set"}, reviewed_by="")
print("wrote", prac_path, "(unreviewed; load with allow_unreviewed=True)")
"""
        ),
        code(
            """# [RUN] one token check on a single case. Tokenizer only — no weights in this kernel.
case0 = cases_run[0]
msgs = ev.screen_messages(case0)
print("Counting convention:\\n", ev.COUNTING_CONVENTION, "\\n")

def template_len(messages, source):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(source, local_files_only=True, trust_remote_code=True)
    ids = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], list):
        ids = ids[0]
    return len(ids)

olmo_dir = Path(lab.tokenizer_source())
print("naive word split of the user text:", len(case0["draft_reply"].split()), "(not the real count)")
if MEASURED:
    probe = lab.chat(msgs, model=cfg["model"], max_tokens=16)
    print("server prompt_tokens:", (probe.get("usage") or {}).get("prompt_tokens"), "← real count for this request")
    print("server completion_tokens:", (probe.get("usage") or {}).get("completion_tokens"), "← real output count")
    print("re-tokenized decoded reply length is usually one less (EOS is not in the text)")
    try:
        print("OLMo apply_chat_template length:", template_len(msgs, str(olmo_dir)), "← should match prompt_tokens")
    except Exception as e:
        print("tokenizer check skipped:", e)
else:
    print("NOT MEASURED: skip live token check")
"""
        ),
        code(
            """# [RUN] Same cases, same prompt, same settings. One request at a time. No third model.
def chat_fn(messages, model, max_tokens=96):
    return lab.chat(messages, model=model, max_tokens=max_tokens, timeout=120)

results = {}
if not MEASURED:
    print("NOT MEASURED: demo or fallback — not scoring")
    for key in ("olmo", "phi"):
        results[key] = {"rows": [], "summary": ev.aggregate([])}
else:
    for key, model in [("olmo", cfg["model"]), ("phi", cfg["comparison_model"])]:
        print("===", key, model)
        rows = ev.run_eval(cases_run, model, chat_fn, max_tokens=96, warmup=True)
        results[key] = {"rows": rows, "summary": ev.aggregate(rows)}
        for r in rows:
            tag = "warm" if not r["scored"] else r["case_id"]
            print(f"  {tag:8} mode={r['mode']} dec={r['decision']} acc={r['acceptable']} in={r['prompt_tokens']} out={r['completion_tokens']}")
        print(key, {k: results[key]["summary"][k] for k in ("rows_live", "acceptable", "decision_correct", "measured")})
"""
        ),
        code(
            """# [RUN] scorecard: both models, live rows only in the accuracy columns.
from datetime import datetime
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
run_info["n_cases_scored"] = len(cases_run)
run_info["frozen_sha256"] = rec["sha256"]
run_info["frozen_review"] = rec["review"]
run_info["rules_version"] = rec["rules_version"]
run_info["measured"] = bool(MEASURED)
ev.print_side_by_side(results["olmo"]["summary"], results["phi"]["summary"])
paths = []
for key in ("olmo", "phi"):
    csv_p, json_p = ev.write_scorecard(
        results[key]["rows"],
        results[key]["summary"],
        Path("logs") / f"t103_{key}_{ts}",
        run_info={**run_info, "model_key": key, "counting_convention": ev.COUNTING_CONVENTION},
    )
    paths.extend([csv_p, json_p])
    print("wrote", csv_p)
print("24 cases is a small sample; a difference of a few cases may be noise.")
"""
        ),
        md(
            """## How to read the scorecard

24 cases is a small sample. The 95% Wilson interval is wide on purpose. A difference of a few cases may be noise. Latency is for **this** hardware and these settings. Nothing here ranks the models in general, and nothing here is a Ministry document.

A bare `GO` is a readable decision and is not an acceptable answer. Format, named rule and quote all have to hold.
"""
        ),
        md(
            """## Cost: tokens are not prices

The local servers have no price per token. Tokens measure work and context used. They become money only through a rate somebody charges.

**Hosted API (illustrative)**

`api_cost = input_tokens × input_rate_per_million / 1,000,000 + output_tokens × output_rate_per_million / 1,000,000`

Use the provider’s own reported usage and its published rate on a stated date. Caching discounts, batch discounts, search grounding, taxes and minimum spends are excluded.

**Self-hosted OLMo and Phi** — two different numbers; show both.

- **Marginal active estimate:** hours = the sum of `generation_ms` for this batch. “What did these answers use while the GPU was busy.”
- **Billed allocation:** hours = the time the instance was allocated and billed, including start-up, loading, warm-up and idle. “What did we pay.”
- **Shared host:** split the billed cost with one stated rule (by active generation seconds is the default). Check that the shares add up to the bill. Never charge the full host to each model.

`cost_per_acceptable = total cost of every attempt in the batch / number of acceptable answers`

Every attempt counts: the warm-up, every scored case and any retry. Zero acceptable answers: print **undefined**, never 0, never a division error.

Staff time, monitoring, storage, support, security and retraining are out of scope for this cell.
"""
        ),
        code(
            """# [CHANGE] Fill only figures you have, with a source and date. Leave None if unknown.
currency = "USD"
api = {"input_rate_per_million": None, "output_rate_per_million": None, "source": "", "date": ""}
host = {"hourly_rate": None, "billed_hours": None, "source": "", "date": ""}

s_o, s_p = results["olmo"]["summary"], results["phi"]["summary"]
active = {"olmo": s_o["attempt_generation_s_total"] or 0, "phi": s_p["attempt_generation_s_total"] or 0}
for key, s in [("olmo", s_o), ("phi", s_p)]:
    print(f"--- {key}: {s['acceptable']} acceptable of {s['rows_live']} live")
    if s["attempts_without_usage"]:
        print("warning:", s["attempts_without_usage"], "live attempts had no token counts; token cost is incomplete")
    if None not in (api["input_rate_per_million"], api["output_rate_per_million"]):
        c = ev.api_cost(s["attempt_input_tokens_total"], s["attempt_output_tokens_total"], api["input_rate_per_million"], api["output_rate_per_million"])
        per = ev.cost_per_acceptable(c, s["acceptable"])
        print("illustrative API cost:", round(c, 6), currency, "| per acceptable:", per if per is not None else "undefined: no acceptable answers in this batch")
    else:
        print("illustrative API cost: not available (no rate entered)")
    if host["hourly_rate"] is not None:
        marginal = ev.compute_cost((active[key] or 0) / 3600, host["hourly_rate"])
        per_m = ev.cost_per_acceptable(marginal, s["acceptable"])
        print("marginal active compute:", round(marginal, 4), currency, "| per acceptable:", per_m if per_m is not None else "undefined")
        if host["billed_hours"] is not None and sum(active.values()) > 0:
            share = active[key] / sum(active.values())
            billed = ev.compute_cost(host["billed_hours"], host["hourly_rate"], share)
            per_b = ev.cost_per_acceptable(billed, s["acceptable"])
            print(f"billed share ({share:.0%} by active seconds):", round(billed, 4), currency, "| per acceptable:", per_b if per_b is not None else "undefined")
    else:
        print("self-hosted compute: not available (no hourly rate entered)")
print("Included: warm-up and every attempt. Excluded: caching, discounts, taxes, staff time, storage, support.")
"""
        ),
        md(
            """### Made-up numbers to show the arithmetic

These are **not** market prices.

- A batch has 25 requests (1 warm-up + 24 cases), 7,200 input tokens and 900 output tokens in total, and 15 acceptable answers.
- Hosted API at made-up rates of US$0.40 per million input tokens and US$1.60 per million output tokens: 7,200 × 0.40 / 1,000,000 = US$0.00288, plus 900 × 1.60 / 1,000,000 = US$0.00144, so US$0.00432. Per acceptable answer: US$0.00432 / 15 = US$0.000288.
- Self-hosted at a made-up US$1.00 an hour, 120 seconds of active generation: 120 / 3,600 × 1.00 = US$0.0333 marginal, or about US$0.0022 per acceptable answer.
- The same host was allocated for 45 minutes (US$0.75 billed) and shared with Phi, which used 180 active seconds. OLMo’s share by active seconds is 120 / 300 = 40%, so US$0.30, or US$0.02 per acceptable answer. Phi’s share is US$0.45. The two add up to US$0.75.
- If the batch had 0 acceptable answers, cost per acceptable answer is undefined, not US$0.

The billed figure is about ten times the marginal one here because of idle and loading time. Utilisation drives self-hosted cost.
"""
        ),
        md(
            """## Optional: the same frozen cases on a hosted API

**Free tiers can use what you send.** Google’s own terms for unpaid Gemini use say it may use your prompts and responses to improve its products and that human reviewers may read them. Other providers’ rules differ, and they change. Send only the fictional CivicDesk cases from this notebook. Never send Ministry documents, Cabinet notes, résumés, personal data or anything you would not post publicly.

The main path never needs a key. Skip this section with the room.
"""
        ),
        md(
            """### How to get a key (checked 12 November 2026 — re-check before you rely on it)

Free access may not cover a whole class (shared limits, daily caps, account eligibility) and may stop.

**Google AI Studio (Gemini API).** Create a key at https://aistudio.google.com/api-keys. Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` (`GOOGLE_API_KEY` wins if both are set). Trinidad and Tobago is listed on the available-regions page. Unpaid use may be read by human reviewers — fictional cases only. OpenAI-compatible URL: `https://generativelanguage.googleapis.com/v1beta/openai/`. Docs: https://ai.google.dev/gemini-api/docs/api-key

**GroqCloud.** Key: https://console.groq.com/keys. Set `GROQ_API_KEY`. Example open-weight model: `openai/gpt-oss-20b`. Free-plan limits apply to the organisation. Base URL: `https://api.groq.com/openai/v1`. If replies come back empty, raise `max_tokens` or set `include_reasoning: false` and record the setting.

**OpenRouter.** Key: https://openrouter.ai/keys. A `:free` model ID is free; the serving provider is chosen unless you pin it. Pin in the next cell. Free-variant limits: 20 requests a minute; 50 a day below US$10 of credits ever. Each provider has its own data policy.
"""
        ),
        code(
            """# [OPTIONAL] key for this session only. Never printed, never saved.
import civicdesk_remote as remote
# [CHANGE] "groq" or "google" or "openrouter"
PROVIDER = "groq"
print(remote.set_key(PROVIDER))
"""
        ),
        code(
            """# [OPTIONAL] [CHANGE] one model ID per provider, written out. No router aliases.
REMOTE_MODELS = {
    "google": "gemini-3.5-flash-lite",
    "groq": "openai/gpt-oss-20b",
    "openrouter": "google/gemma-4-26b-a4b-it:free",
}
EXTRA = {}
if PROVIDER == "openrouter":
    EXTRA = {"provider": {"order": ["google-ai-studio"], "allow_fallbacks": False}}
if PROVIDER == "groq":
    EXTRA = {"include_reasoning": False}
print("provider", PROVIDER, "model", REMOTE_MODELS[PROVIDER], "extra", EXTRA)
"""
        ),
        code(
            """# [OPTIONAL] same frozen cases, sequential, paused for free-tier limits.
if not cases_run:
    print("load the course set first")
else:
    chat_remote = remote.make_chat_fn(PROVIDER, REMOTE_MODELS[PROVIDER], extra_body=EXTRA or None, pause_s=3)
    remote_rows = ev.run_eval(cases_run, REMOTE_MODELS[PROVIDER], chat_remote, max_tokens=96, warmup=True)
    remote_summary = ev.aggregate(remote_rows)
    print(remote_summary)
    print("usage_source sample:", remote_rows[0]["usage_source"] if remote_rows else None)
    print("Provider token counts are not comparable number-for-number with the local ones.")
    ev.write_scorecard(remote_rows, remote_summary, Path("logs") / f"t103_{PROVIDER}_{ts}", run_info={"provider": PROVIDER, "optional": True})
"""
        ),
        code(
            """# [OPTIONAL] two lines that are never added together. Re-check rates on the day.
print("Observed charge on the free tier: US$0 (for this run, on this account, on this date).")
paid_in = None   # [CHANGE] published input USD / million tokens, or None
paid_out = None  # [CHANGE] published output USD / million tokens, or None
if "remote_summary" not in globals():
    print("Paid-equivalent at the published rate on [date]: not available (hosted eval not run)")
elif remote_summary.get("attempt_input_tokens_total") and None not in (paid_in, paid_out):
    paid = ev.api_cost(remote_summary["attempt_input_tokens_total"], remote_summary["attempt_output_tokens_total"], paid_in, paid_out)
    print(f"Paid-equivalent at the published rate on [date]: {paid} USD")
else:
    print("Paid-equivalent at the published rate on [date]: not available")
"""
        ),
        md(
            """A hosted model scoring higher on 24 fictional cases says nothing about Ministry documents, and a free tier being US$0 today is not a budget. Hosted models are not assumed to be better. The scorecard decides, case by case, and only for this task.
"""
        ),
        code(
            """# [OPTIONAL] drop keys from this process before you download the notebook.
remote.forget_keys()
print("keys forgotten for this process")
"""
        ),
        code(
            """# [CHANGE] write-up. Numbers come from the scorecard. Fill the two human fields.
s_o, s_p = results["olmo"]["summary"], results["phi"]["summary"]
writeup = {
    "olmo_acceptable_of_live": f"{s_o.get('acceptable')} of {s_o.get('rows_live')}",
    "phi_acceptable_of_live": f"{s_p.get('acceptable')} of {s_p.get('rows_live')}",
    "olmo_decisions_correct": s_o.get("decision_correct"),
    "phi_decisions_correct": s_p.get("decision_correct"),
    "measured": bool(s_o.get("measured") and s_p.get("measured")),
    "who_would_pay": "laptop / Ministry VM / MEA Azure / hosted API / unsure",
    "data_allowed_to_leave_our_control": "yes / no / only if fictional / unsure",
}
print(writeup)
lab.save_log("T1-03_scorecard", {
    "run_info": run_info,
    "olmo": results["olmo"]["summary"],
    "phi": results["phi"]["summary"],
    "writeup": writeup,
})
"""
        ),
        md(
            """## Cost card (also on paper)

Open `cards/cost_card.md`. Copy the live figures from the scorecard. Leave a field blank when you have no rate. Burst vs standing inference is a Day 3 mark; today the billed-versus-marginal gap is the answer to “if we left the GPU on overnight, who notices?”

## Write-up

1. Using **your** scorecard, which model would you show a domain verifier for this screening task, and why? If `measured` is false, say what you cannot conclude.
2. Name one reason a closed API is cheaper *this afternoon* and one reason it is expensive for a core process.
3. Would this data be allowed to leave our control under our rules?
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-04
# ---------------------------------------------------------------------------
write(
    "T1-04_openness_licences_gpu.ipynb",
    [
        md(
            """# T1-04 Openness, licences and GPU questions

**Time:** 13:45–14:20 &nbsp;|&nbsp; **Evidence:** licence scavenger-hunt answers + scenario labels + GPU question card

**Notebook learning outcomes**

- Say what a model licence controls, and find those terms in a real licence file.
- Sort a deployment into prohibited, permitted with obligations, permission required, or unclear (escalate), citing the clause.
- Tell open weights from open source, and say why downloadable does not mean unrestricted.
- Ask why two “24 GB” cards are not the same buy.

This is practice in reading licences, not legal advice. For a real project, your reading goes to counsel and procurement with the clause numbers attached.

**How to use this notebook**

- **No-code / code-light:** run every cell in order. Read the teaching note after a cell. Fill the write-up. Do not paste work files.
- **Occasional-code:** run all cells. Change only lines marked `# [CHANGE]`.
- **Deep-code:** optional cells are tagged `# [OPTIONAL]`. Stay with the room on the required path. Do not drive someone else's notebook.

Git is not required. If you are stuck, load the matching file in `completed/` for this notebook only, mark it as loaded from reference, and continue.
"""
        ),
        md(
            """## Ministry link

| Question | Who asked it in the EOIs without using these words |
|---|---|
| May we use it for this job, and what must we do if we share it? | Anyone who would put a model into a service or pass it to another agency |
| Can we see what it was trained on? | Anyone who must **audit** a system (Labour, Health, OPR, Finance). Published data helps audit what went in; it does not explain one particular answer |
| Can we run it here? | **CPO, TTDF, Finance, THA** (N7) |
| Llama vs OLMo | Llama ships under Meta's own community licence plus a use policy; OLMo under Apache 2.0 plus Ai2's guidelines. Both are open-weight; only one licence is OSI-approved |
| Azure already exists | Phi-4 Mini is in the room as the comparison, not the default |

**N4 named:** hosting choice is also an access choice — a public API is a disclosure path.

## Overnight readers

T1-01a put **weights** on disk and T1-03 picked a winner on quality. This notebook adds two gates before anyone builds on that winner: **may we** (the licence and any terms it pulls in) and **can we** (the GPU card). The files you read are in `licences/`, copied from the publishers with checksums, so nobody needs the internet to do this lab.
"""
        ),
        code(
            """# [RUN]
import licence_lab as L

ok = L.verify()   # every licence file matches the checksum recorded when it was downloaded

w = L.t1_03_winner()
if w["winner"] is None:
    print("No T1-03 scorecard on this machine. Pick the model you would build on and carry on.")
elif w.get("scale") == "acceptable":
    print(f"T1-03 winner on acceptable answers: {w['winner']}  (OLMo {w['olmo_score']}, Phi {w['phi_score']})")
else:
    print(f"T1-03 winner on quality: {w['winner']}  (OLMo {w['olmo_score']}/2, Phi {w['phi_score']}/2)")

print()
print("Three gates before a build:")
print("  1. Quality   - T1-03: does it do the job on CivicDesk text?")
print("  2. Permission - today: may we use it this way, and what must we do?")
print("  3. Hardware  - today: can we run it, for how many users, at what cost?")
print("A model that wins gate 1 can still fail gate 2 or 3.")
"""
        ),
        code(
            """# [RUN]
from pathlib import Path
print(Path("data/model_card_excerpts.md").read_text(encoding="utf-8"))
"""
        ),
        md(
            """### Teaching note: what a model licence controls

A licence is the publisher's written permission. Read it for seven things:

1. **Use** — may you run it at all, and for which purposes? Is there a separate rule for commercial or government use?
2. **Change** — may you fine-tune it, add an adapter, merge it, quantise it?
3. **Pass it on** — may you give the weights, or your changed version, to someone else? This is different from running a service people use over the web: some conditions only start when you hand over files.
4. **Say so** — what notices, credits, licence copies or naming rules come with passing it on or putting it in a product?
5. **Limits** — is there a cap on users, a list of banned uses, a place or type of organisation that is excluded?
6. **Other documents** — does the licence pull in a use policy or brand rules by link? Those count as part of the deal. A model card may also point to guidelines, data cards or third-party notices; read them too.
7. **What is not promised** — warranty, liability, who defends whom if someone sues.

Two things a licence usually does **not** do: it does not make your use lawful under data-protection law, and it does not make the model accurate. Privacy is a separate obligation that comes from the law and Ministry policy.

**Open weight, open source, closed product**

- **Open weight:** you can download the parameters and run them. The licence may still carry conditions or bans. Llama 3.2 is open weight under Meta's own licence.
- **Open-source licence:** a licence approved by the Open Source Initiative, such as Apache 2.0 or MIT. These let anyone use, change and share for any purpose, with conditions like keeping notices.
- **Open source AI (OSI definition 1.0):** asks for more than a licence on the weights. It wants enough information about the training data for a skilled person to build a substantially equivalent system, the complete training and running code, and the parameters, each under OSI-approved terms. An Apache licence on the weights is one piece of evidence, not the whole check.
- **Closed product:** ChatGPT, Claude, Grok as a service. You get outputs under the provider's terms of service, no weights.

Published training data lets you audit what went in (sources, filtering, licences of the pieces). It does not tell you why the model wrote one particular sentence.
"""
        ),
        md(
            """## Scavenger hunt: the Llama 3.2 licence (9 minutes)

You are reading `licences/llama-3.2/LICENSE`, the Llama 3.2 Community License Agreement (release date September 25, 2024), and the use policy it links to. Work in pairs.

For each question, write one of:

- `FOUND: §<section> — "<a few words quoted>"`
- `NOT FOUND` — the licence does not say. That is a correct answer when it is true.
- `NEED LINKED TERMS: <which document>` — the licence points somewhere else for the answer.

Use `L.find("llama32_licence", "word")` to search, or open the file in the Jupyter file browser. The second file is `L.find("llama32_aup", "word")`. Do not ask a chatbot; it is not the licence.

Suggested search words are in brackets. Questions 9 and 10 are for pairs who finish early.
"""
        ),
        code(
            """# [RUN]
L.files()
print()
L.find("llama32_licence", "royalty-free")
L.find("llama32_licence", "training data")   # shows what NOT FOUND looks like
"""
        ),
        code(
            """# [CHANGE] answer each line. Start with FOUND:, NOT FOUND or NEED LINKED TERMS:
hunt = {
    "Q1_use_and_any_commercial_or_government_rule (grant, royalty-free)": "",
    "Q2_may_we_fine_tune (derivative, modifications)": "",
    "Q3_if_we_publish_a_fine_tuned_model_what_must_we_do (distribute, Built with, Notice)": "",
    "Q4_is_there_a_user_limit (monthly active users)": "",
    "Q5_which_uses_are_banned (Acceptable Use)": "",
    "Q5b_now_in_the_AUP_is_military_use_covered (Military)": "",
    "Q6_does_it_say_what_data_trained_the_model (training data, dataset)": "",
    "Q7_does_Meta_promise_the_outputs_are_correct (warranty, AS IS)": "",
    "Q8_does_the_licence_handle_privacy_for_documents_we_feed_it (privacy, laws, personal)": "",
    "Q9_optional_which_courts (Governing Law)": "",
    "Q10_optional_how_can_we_lose_the_licence (terminate)": "",
}
problems = L.check_format({k: v for k, v in hunt.items() if "optional" not in k})
print("\n".join(problems) if problems else "Format OK. Your instructor checks the content.")
import civicdesk_lab as lab
lab.save_log("T1-04_licences", {"hunt": hunt})
"""
        ),
        md(
            """## Walkthrough: same job, two licences (instructor-led, 4 minutes)

The two texts:

- **OLMo 2 1B Instruct:** Apache License 2.0 (`licences/apache-2.0/LICENSE-2.0.txt`). Its card also links Ai2's Responsible Use Guidelines, which say they "govern your use" of Ai2 models.
- **Llama 3.2 1B Instruct:** Llama 3.2 Community License Agreement plus the Llama 3.2 Acceptable Use Policy.

The labels you will use:

| Label | Meaning |
|---|---|
| **permitted** | The grant covers it and no condition is triggered |
| **permitted with obligations** | Allowed if you do something: keep a notice, show a credit, follow a policy, name it a certain way |
| **permission required** | The licence says you must ask the publisher, and you have no rights until they agree |
| **prohibited** | A term you agreed to says you may not |
| **unclear - escalate** | The text does not settle it, or a linked document might. Write down the clause and the question, and send it on |

**Scenario S4 (made-up facts):** A defence-force operations cell wants a model on its own servers to summarise intelligence reports for planning military operations. Nothing is published or shared outside.

The next cell prints the clauses. Watch which licence has a term that reaches this job.
"""
        ),
        code(
            """# [RUN]
print("=== Llama 3.2 licence: the clause that pulls in the use policy")
L.find("llama32_licence", "hereby incorporated by reference")
print("=== Llama 3.2 Acceptable Use Policy: item 2 and 2.a")
L.find("llama32_aup", "risk of death or bodily harm")
L.find("llama32_aup", "Military, warfare")
print("=== Apache 2.0: the grant")
L.find("apache", "Grant of Copyright License")
print("=== Ai2 guidelines linked from the OLMo card: any military item?")
L.find("ai2_guidelines", "military")
L.find("ai2_guidelines", "illustrative and not exhaustive")
"""
        ),
        md(
            """## Your turn: label four scenarios (5 minutes)

All facts are made up so the clauses can be tested. For each scenario give a label for **each** licence, and the clause you relied on (or `none found`).

**S1. Internal pilot.** A Ministry runs the model on its own server. Staff paste internal policy memos and get summaries. A named officer checks every summary before it is used. No files leave the Ministry.

**S2. Public chatbot.** The Ministry hosts the model on its own server behind a public web page that answers questions about services. Citizens type questions. The weights never leave the server.

**S3. Publishing an adapter.** The Ministry fine-tunes the model for résumé redaction and publishes the result on Hugging Face as **“CivicDesk-Redact-1B”** so other Caribbean governments can download it.

**S5. A very large partner.** The Ministry partners with GlobalChat Inc. GlobalChat and its affiliates had 750 million monthly active users across their products in August 2024. GlobalChat will itself fine-tune and run the model for the Ministry's service.

Useful searches: `L.find("apache", "Redistribution")`, `L.find("llama32_licence", "Built with Llama")`, `L.find("llama32_licence", "700 million")`, `L.find("llama32_aup", "disclose")`.
"""
        ),
        code(
            """# [CHANGE] label: permitted / permitted with obligations / permission required / prohibited / unclear - escalate
scenarios = {
    "S1_OLMo_Apache":  {"class": "", "clause": ""},
    "S1_Llama32":      {"class": "", "clause": ""},
    "S2_OLMo_Apache":  {"class": "", "clause": ""},
    "S2_Llama32":      {"class": "", "clause": ""},
    "S3_OLMo_Apache":  {"class": "", "clause": ""},
    "S3_Llama32":      {"class": "", "clause": ""},
    "S5_OLMo_Apache":  {"class": "", "clause": ""},
    "S5_Llama32":      {"class": "", "clause": ""},
}
problems = L.check_classes(scenarios)
print("\n".join(problems) if problems else "Labels OK. Compare with the room.")
lab.save_log("T1-04_scenarios", {"scenarios": scenarios})
"""
        ),
        md(
            """## When it goes to counsel or procurement

Send one short note per model, not a verdict:

1. Exact model name and revision (from the card), and where the licence came from, with the date you read it.
2. The job, in two lines: who uses it, on what data, hosted or shipped, shared with whom.
3. The clauses you think apply, by number, and the label you would give.
4. The open questions, word for word (for example: “Do the Ai2 guidelines bind us on top of Apache 2.0?”, “Is our internal tool ‘made available’ under Llama 3.2 §1.b.i?”).
5. The separate privacy question: what personal data goes in, and which law and Ministry policy cover it.

Recheck the linked documents on the day you decide. Use policies can change after a model is released: the Llama 3.2 policy you read today has different wording from the version published in September 2024 (both are in `licences/llama-3.2/`).
"""
        ),
        md(
            """## GPU question card

**4 minutes in the room:** answer questions 1, 2 and 6 for this machine. Questions 3 to 5 go home with you tonight.

Ministries hear “we need a GPU” and buy one box for everything. Split **burst** (a short fine-tune, Day 3 / Tier 2) from **standing inference** (this chat API). VRAM is necessary and not sufficient.

Fill `cards/gpu_questions.md` — do not memorise SKUs:

1. Burst or standing, and how many users?
2. How much VRAM, at what precision?
3. Architecture / compute capability — will vLLM actually run?
4. Compute-bound or memory-bandwidth-bound?
5. Consumer vs datacentre (ECC, multi-user, driver, licence)?
6. Can it idle-stop?

`# [OPTIONAL]` look at `lab.gpu_note()` again and write which of the six questions you can already answer for *this* machine.
"""
        ),
        code(
            """# [OPTIONAL]
import civicdesk_lab as lab
print(lab.gpu_note())
"""
        ),
        md(
            """`# [OPTIONAL]` After class: `tier1/deep/T1-04d_licences_deep.ipynb` compares Meta Llama 3 with Llama 3.2, shows how the use policy changed, looks at Phi's MIT licence and third-party notice, and reads the licences of OLMo's fine-tuning data. Nothing in it is needed for Day 2.
"""
        ),
        md(
            """## Write-up

1. In one line: OLMo, Phi, ChatGPT — what can you *see*, and what are you *allowed* to do with it?
2. Your T1-03 winner: which of its licence terms would matter most for a Ministry service, and which clause says so?
3. Why might TTDF refuse a pretty public API even if it scored higher in T1-03?
4. Which GPU question from the card could you not answer today, and who in your Ministry could?
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-05
# ---------------------------------------------------------------------------
write(
    "T1-05_usecase_canvas.ipynb",
    [
        md(
            """# T1-05 Use-case canvas (group)

**Time:** 14:20–14:55, then overnight 20–30 min &nbsp;|&nbsp; **Evidence:** canvas (`cards/usecase_canvas.md`) + gold pairs (logged)

**Notebook learning outcomes**

Write a testable use case a domain person can verify. Frame the *type* of problem in the EOI, not a live system. Watch one worked canvas get measured, then design your own experiment: what you would measure, what counts as good enough, and what stops a document.

**This block is (group).** Ministry groups of three to four. A singleton joins the same learning-need cluster. Each member still has this notebook open.


**How to use this notebook**

- **No-code / code-light:** run every cell in order. Read the teaching note after a cell. Fill the write-up. Do not paste work files.
- **Occasional-code:** run all cells. Change only lines marked `# [CHANGE]`.
- **Deep-code:** optional cells are tagged `# [OPTIONAL]`. Stay with the room on the required path. Do not drive someone else's notebook.

Git is not required. If you are stuck, load the matching file in `completed/` for this notebook only, mark it as loaded from reference, and continue."""
        ),
        md(
            """## This block is design, not build

This is a thought exercise in **experimental design**. Nobody builds a system here.

- You do **not** need your own dataset today. Do not fetch one.
- Your job is to design the experiment and pin down the metrics: who checks the output, what "wrong" looks like, how you would count it, what number is good enough (written down **before** any run), and what makes a single document stop.
- The instructor's worked example runs a real measurement so you can see what your design turns into later. You copy the *shape*, not the task."""
        ),
        md(
            """## Ministry link — pick the row for your table

| Cluster | Sit with | Canvas must include |
|---|---|---|
| **A Criteria** | Labour, Health | Published criteria; quote or flag; **human review**; stop = no hire / no published grade |
| **B Retrieval** | Finance, Defence OPR, MPSDFS policy, MOWI ECMS, RDLG minutes, THA | Approved corpus; cite or abstain; access rule (N4) |
| **C Service desk** | Trade IMSD, Defence assets-as-query | Triage; tools the model must **never** call; register vs generation (N10) |
| **D Local control** | CPO, TTDF, others with custody constraints | Where the box lives; what data never leaves; agentic “no” |

If the real job is GIS routes or radar patterns, say **maybe no language model** (AUX-02) on the canvas. That is a valid Day 1 outcome.

## Overnight readers

The morning was the machine. This is the **job**. Write a use case a domain person can mark wrong. You will not choose prompt vs RAG vs fine-tune until Day 2 (T1-06). Tonight: owner, verifier, baseline, measure, error cost, stop, data that stays out. CivicDesk names only — no live EOI attachments."""
        ),
        md(
            """## Worked example: what Day 1 already gave us, and what it did not

The instructor's example is a fictional CivicDesk HR task: **remove personal data from CVs before an internal shortlisting panel reads them**, so the panel judges qualifications, not identity. Every CV is synthetic.

What the morning gave this project:

- **T1-01 first call:** we can send text to OLMo through the course pipeline and get text back. That is plumbing, not quality.
- **T1-02 tokens:** we can count what a CV costs in tokens, so latency and cost questions have a unit.
- **T1-03 model comparison:** we learned how to measure on a frozen, rule-labelled set. Its GO/BLOCK labels scored draft-reply screening, a **different task**. It says nothing about redaction.
- **T1-04 licence and GPU gates:** OLMo passed "may we" and "can we" for classroom use. That makes it the *provisional* model to measure, not the chosen one.

What we do not know yet: whether a prompted OLMo redacts CVs well enough. Only a measurement on this task can say."""
        ),
        code(
            """# [RUN] the instructor's worked canvas. Fictional CivicDesk names only.
worked = {
    "organisation": "CivicDesk HR Recruitment Unit (fictional)",
    "cluster": "A Criteria, with D custody constraints",
    "problem_in_one_line": "Before an internal shortlisting panel reads CVs for a vacancy, remove applicant and third-party "
                           "personal identifiers without changing any work content.",
    "owner_role": "Recruitment manager (owns the process and the go/no-go for each stage)",
    "domain_verifier_role": "Recruitment officer already authorised to see unredacted CVs; the data protection "
                            "officer rules on policy edge cases (e.g. a family business name)",
    "current_non_ai_baseline": "Officer redacts by hand in a word processor; a second officer spot-checks. "
                               "Minutes per CV and misses per 100 CVs: not yet measured. Measure on 20 synthetic CVs "
                               "before comparing.",
    "success_measure": "On the frozen 40-CV held-out set: missed PII by type (recall), documents with any leak, "
                       "over-redaction or altered text, empty/truncated outputs, latency, tokens, "
                       "cost per acceptable answer (scoped).",
    "acceptance_rule": "EXAMPLE, fixed before the run: 0 documents with a residual email/phone/ID/DOB; at most "
                       "2 of 35 with any leak; at most 4 of 40 over-redacted or altered; 0 empty or truncated; "
                       "p95 latency at most 20 s on the course GPU.",
    "test_set_plan": "40 synthetic CVs, 8 layouts fixed in advance, labels from code, frozen by hash. Never used "
                     "to train, tune prompts or pick examples. Day 3 reuses it unchanged.",
    "error_cost_if_wrong": "Missed PII: the panel sees identity (bias, privacy breach). Over-redaction or altered "
                           "text: the panel misjudges a candidate. Truncation: experience silently disappears.",
    "data_that_must_stay_out": "Real CVs, photos, scans, anything from the live HR system; no raw CV text in "
                               "shared logs.",
    "preferred_intervention_guess": "unsure. Measure prompted OLMo first (provisional). T1-06 argues prompt vs RAG "
                                    "vs fine-tune; Day 3 measures one adapter on this same set. No outcome assumed.",
    "stop_condition": "Per document: any residual email/phone/ID, a known name from the application form, empty, "
                      "much shorter than the input, timeout, out-of-scope input -> HOLD for authorised review, "
                      "not released. Whole service: pause on a failed audit sample, a burst of holds, suspected "
                      "drift or a new layout/language -> fall back to the manual process.",
    "one_cost_question": "Reviewer minutes per held CV, times the hold rate, versus today's manual minutes per CV.",
    "next_question_for_MPAAI": "Who owns the redaction policy, and may a family business name stay?",
}
for k, v in worked.items():
    print(f"{k}: {v}\n")"""
        ),
        md(
            """### Teaching note: a quality target is not a stop trigger

Two different things sit on the canvas.

- **Acceptance rule (quality target):** a pass mark for a *batch*, checked once on the frozen test set. It needs the answer key. It answers "is this good enough to continue to the next stage?"
- **Stop condition (per-document trigger):** checked on *every* document at run time, with no answer key. It answers "may this one output go to the panel, or does it wait for a person?" If the email check fires, that CV is held and routed to the authorised verifier. It is not released.

The checks have false alarms (a reference number that looks like a phone number) and misses (an email spelled out in words). **No alert does not mean safe.**"""
        ),
        code(
            """# [RUN] seven worked CVs, scored against the answer key, then through the stop rule.
# The outputs below were WRITTEN BY HAND to show one failure each. No model produced them.
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..") / "shared" / "resume_redaction"))
import redaction_eval as R

teach = R.load_fixture()
replay = R.load_replay()
assert replay["fixture_sha256"] == teach["sha256"], "replay does not belong to this teaching set"
print(replay["label"], "\n")
rows = R.evaluate(teach, replay["outputs"])
for doc, r in zip(teach["docs"], rows):
    print(f"{r['id']} ({doc['layout']})")
    print(f"   shown on purpose: {replay['what_each_shows'][r['id']]}")
    print(f"   answer key says: missed={[m['type'] + ': ' + m['text'] for m in r['spans_missed']]}"
          f" errors={[e['kind'] for e in r['edits']]}")
    print(f"   run-time stop rule: {r['reasons'] or 'nothing fired'} -> {r['decision']}\n")"""
        ),
        md(
            """### Reading the replay

- **R05 is the lesson.** The email leaked and no check fired. A quiet run is not a safe run.
- **R07 is the cost.** A correct output was held. Every false hold is a person's time.
- **R03's 30% → 40%** is invisible to every run-time check. Only the answer key catches it, which is why you measure on a labelled set *before* trusting run-time checks.
- **R04** passed the checks and still harmed the candidate (the employer vanished). Over-redaction is an error with a cost, not a safe default.
- **R06** cut off mid-sentence. Span recall would count the cut-off name as "removed", so read recall beside truncation.

Adding a second detector or a second model does not automatically fix this. Two systems trained on similar text tend to miss the same spelled-out email."""
        ),
        code(
            """# [RUN] the frozen 40-CV benchmark for prompted OLMo.
# Learners: leave MODE = "replay" (loads the run measured in this container image).
# Instructor: MODE = "live" sends 40 requests to the backend chosen in T1-01. Same set, same prompt, same rule.
MODE = "replay"  # [CHANGE] instructor only: "live"

bench = R.load_benchmark()
if MODE == "live":
    import civicdesk_lab as lab
    run = R.run_live(bench, "olmo")
    if not run["measured"]:
        print("Not measured (demo or fallback replies). Showing the committed baseline instead.")
        run = R.load_run("olmo_baseline_v1")
else:
    run = R.load_run("olmo_baseline_v1")
assert run["fixture_sha256"] == bench["sha256"], "baseline was not run on this benchmark"
assert run["measured"], "baseline file is not a measured run"
print(f"model {run['model']} | prompt {run['prompt_version']} | benchmark {run['benchmark_version']} | run {run['run_at_utc']}")

rows = R.evaluate(bench, run["outputs"], run["latency_s"])
summary = R.summary_table(bench, rows)
for k, v in summary.items():
    print(f"{k}: {v}")

by_cat = {}
for d, r in zip(bench["docs"], rows):
    c = by_cat.setdefault(d["category"], [0, 0])
    c[0] += 1
    c[1] += r["acceptable"]
print("\nacceptable as-is by category:", {k: f"{v[1]}/{v[0]}" for k, v in by_cat.items()})

verdict = R.check_rule(rows, run["latency_s"])
print("\n" + verdict["rule"])
for name, value, ok in verdict["criteria"]:
    print(f"  {'ok  ' if ok else 'FAIL'} {name}: {value}")
print("Meets the example rule:", verdict["meets_rule"])"""
        ),
        md(
            """### What the baseline says, and what it does not

- It is a **measurement of one prompt on one model on 40 synthetic CVs**. It is the number Day 3 has to beat, and the same 40 CVs, scorer and rule come back on Day 3 unchanged.
- If it **meets** the rule, the honest conclusion is that a prompt may be enough for this classroom task. Fine-tuning would need another reason.
- If it **does not**, Day 3 tests whether one adapter closes the gap. It may help, it may not, and it may fix one category and break another. Nobody knows until it is measured.
- Either way, **meeting the rule is not permission to release anything.** It is synthetic, classroom evidence. Real CVs need a real test set, an authorised environment and the owner's decision.
- 40 documents is small. Zero failures in 40 is consistent with a true failure rate up to about 7% (one-sided 95% bound, and only for documents like these). Differences of one or two documents between runs are noise-sized.
- The rule was written **before** the run. Changing it after seeing the result is a new experiment, not a pass."""
        ),
        code(
            """# [CHANGE] fill as a group. Fictional CivicDesk names only. Design only: no dataset needed today.
canvas = {
    "organisation": "",
    "cluster": "A / B / C / D",
    "problem_in_one_line": "",
    "owner_role": "",
    "domain_verifier_role": "",
    "current_non_ai_baseline": "",
    "success_measure": "",
    "acceptance_rule": "write the pass mark BEFORE any run, as numbers",
    "test_set_plan": "how many examples, which categories, who labels them, how it stays frozen",
    "error_cost_if_wrong": "",
    "data_that_must_stay_out": "",
    "preferred_intervention_guess": "prompt / RAG / integration / fine-tune / none / unsure",
    "stop_condition": "",
    "one_cost_question": "",
    "next_question_for_MPAAI": "",
}
for k, v in canvas.items():
    print(f"{k}: {v}")"""
        ),
        md(
            """### Teaching note

A fluent paragraph is not a use case. A domain verifier must be able to say “that output is wrong” using a measure you wrote down. Labour: evidence quote vs criterion. Trade: ticket fields complete, password not reset. Finance: citation present or abstain.

Compare your canvas with the worked one, line for line. Yours does not need data, only a design: each measure should be something you could count, with a pass mark you would accept or reject before seeing a result, and a stop condition that works on one document at run time without an answer key.

You will **not** finish the intervention label today. Day 2 morning (T1-06) is that argument. Overnight you add: owner, verifier, baseline, measure, error cost, stop, and three remaining questions.

Copy the dict into `cards/usecase_canvas.md` before you leave. Download this notebook at 14:55."""
        ),
        code(
            """# [CHANGE] Gold pairs: for YOUR use case, write text that SHOULD trigger the action beside a near miss that
# should NOT. Invent the text. Fictional CivicDesk only. One pair in class, six by tomorrow.
# These are design drafts, not training data and not test data.
gold_pairs = [
    {
        "rule": "which line of your policy or criteria this tests",
        "should_trigger": "",
        "near_miss_should_not": "",
        "why_they_differ": "",
        "what_real_data_you_would_need": "",
    },
]

worked_pair = {  # the instructor's example, from the résumé task
    "rule": "PERSON: redact private individuals; keep employer names",
    "should_trigger": "Referee: Gail Ramsaran, Former Supervisor",
    "near_miss_should_not": "Accounts Clerk, Ramdass & Sons Hardware Ltd",
    "why_they_differ": "Same kind of word (a family name); one is a person, one is an employer the policy keeps",
    "what_real_data_you_would_need": "CVs where family names appear in employer names, labelled by the policy owner",
}

for i, p in enumerate(gold_pairs, 1):
    empty = [k for k, v in p.items() if not str(v).strip()]
    same = p["should_trigger"].strip() and p["should_trigger"].strip() == p["near_miss_should_not"].strip()
    print(f"pair {i}: " + ("complete" if not empty and not same else f"to finish: {empty or 'the two texts are identical'}"))"""
        ),
        md(
            """### Teaching note: pairs are your data roadmap

A model learns a boundary from examples on both sides of it. A near miss is where a system usually fails. Your pairs are the start of a data-preparation plan:

1. **Freeze the test set first.** Before anyone writes training examples, set aside held-out examples nobody trains on or tunes against.
2. **Each pair names a category** the test set must cover, and a category the training data must cover.
3. **Labels come from your policy, checked by your verifier,** not from a model marking its own work.
4. **Don't copy test items into training.** If a pair came from a failure you saw in the test set, write a new example of that *kind*. Never reuse the test text.
5. The column "what real data you would need" is your shopping list for the real project, and the list of what must stay out."""
        ),
        code(
            """# [RUN] save whatever you have. Empty strings are allowed at 14:55; overnight fills them.
import civicdesk_lab as lab
lab.save_log("T1-05_canvas_draft", canvas)
lab.save_log("T1-05_gold_pairs", {"pairs": gold_pairs})
print("draft and pairs saved — finish overnight in cards/usecase_canvas.md")"""
        ),
        md(
            """## Overnight 1 (20–30 min, no GPU)

Finish the canvas, including the acceptance rule and test set plan. Write six gold pairs (at least two near misses that a careless system would get wrong). Three remaining questions for Day 2. No home GPU. Do not fetch ministry files. If the lab was unfinished, also open `completed/T1-05_canvas_example.md`.

You can re-read T1-01a without starting servers: the point is the chain data → weights → runtime → API → output, and which of those you own. Tomorrow you add **retrieval** (approved handbook chunks) beside those frozen weights — you still will not train.

If you loaded a reference file, also see `completed/T1-05_gold_pairs_example.md`. Optional reading: `cards/t1_05_release_and_rollout.md` (how a stop rule becomes a safe rollout)."""
        ),
        md(
            """## [OPTIONAL] After the canvas: release safety and rollout

For those who want more. Not needed for Day 2. Read `cards/t1_05_release_and_rollout.md`. Short version: a per-document hold protects one CV; a sampled audit estimates how often misses happen across many; a canary limits how many people one bad version can reach. None of them is permission to release, and none can un-send a CV that already leaked."""
        ),
        code(
            """# [OPTIONAL] Two calculators. Every input is your own assumption, not a measured price or rate.
for n in (7, 40, 100, 300):
    print(f"0 failures in {n:>3} random audits -> true rate could still be up to {R.upper_bound_95(0, n):.1%} (one-sided 95%)")
print("(Valid only if the audited documents are a random sample of the documents you care about.)\n")

# Scoped cost per acceptable answer for the benchmark run in cell 8: compute + review of held docs only.
print(R.cost_per_acceptable(rows, compute_cost_per_doc=0.0,      # [CHANGE] your figure
                            review_minutes_per_hold=5,           # [CHANGE] your figure
                            reviewer_cost_per_hour=0.0))         # [CHANGE] your figure"""
        ),
    ],
)

print("done")
