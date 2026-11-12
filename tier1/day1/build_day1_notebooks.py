"""Write the Day 1 notebooks as valid .ipynb files (includes T1-01a build)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


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

**Time:** 10:45–12:00 &nbsp;|&nbsp; **Evidence:** token checkpoint + marked architecture card

**Notebook learning outcomes**

Explain tokens, embeddings, attention, context windows, prediction, training vs inference.

"""
            + BANNER
        ),
        md(
            """## Ministry link

The sentences below are **fictional**. They are shaped like the prose each cluster actually lives with. You are counting tokens, not retrieving classified files.

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
"""
        ),
        code(
            """# [RUN]
import civicdesk_lab as lab

sentences = {
    "A": "The committee noted the request dated 12 March and asked that the attachment be filed with the minute.",
    "B": "Criterion C2: the applicant must hold a recognised diploma in records management or equivalent.",
    "C": "Printer on the third floor will not take paper. User already restarted. Please advise.",
    "D": "List CivicDesk laptops assigned to Unit 4 whose warranty ends this month.",
}
for k, s in sentences.items():
    toks = lab.naive_tokens(s)
    print(f\"{k}  tokens={len(toks):3d}  {toks[:12]}{'...' if len(toks)>12 else ''}\")
"""
        ),
        md(
            """### Teaching note — after the counts

The classroom tokenizer is a **stand-in**. OLMo’s tokenizer will split some words differently. The idea is the same: the model never sees letters; it sees IDs. A long Cabinet pack (Finance) or a 2,000-application batch (Labour) can blow a **context window** even if a human could skim it. That is one reason Day 2 retrieves *chunks*, not whole EDMS filings.

`# [CHANGE]` below: pick sentence B or C and add one word. Watch the count move.
"""
        ),
        code(
            """# [CHANGE] edit this string, re-run, write the new count on the architecture card
probe = "Criterion C2: the applicant must hold a recognised diploma in records management or equivalent."
print(len(lab.naive_tokens(probe)), lab.naive_tokens(probe))
"""
        ),
        code(
            """# [RUN] two decoding settings on the same CivicDesk prompt
messages = [
    {"role": "system", "content": "CivicDesk classroom. One short sentence. No invented citations."},
    {"role": "user", "content": "In one sentence: should a missing diploma be Meets, Does not meet, or Human review required?"},
]
for label, temp in [("greedy-ish (temp 0)", 0.0), ("more random (temp 0.9)", 0.9)]:
    # demo client ignores temperature; live vLLM will not
    r = lab.chat(messages)
    print(label, "→", r["text"][:240])
    print()
"""
        ),
        md(
            """### Teaching note — decoding

Temperature is not “creativity.” It is how sharply the head picks among next tokens. For **Labour / Health / OPR** criteria work you want the boring setting (low temperature) plus a quote. For a Trade ticket draft you might tolerate more variation — still not a password reset.

**Training vs inference:** nobody in this room is updating OLMo’s blocks today. You are only running them.
"""
        ),
        md(
            """## Write-up

1. Mark the architecture card: tokenizer, embedding, blocks, head.
2. Why might Finance *not* paste a whole minute pack into this window?
3. One sentence: what is frozen right now?
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
            """# T1-03 SLM vs LLM comparison

**Time:** 12:45–13:45 &nbsp;|&nbsp; **Evidence:** scorecard + cost card (`cards/cost_card.md`)

**Notebook learning outcomes**

Distinguish SLM from LLM using measured evidence (quality, latency, memory, privacy, cost).

"""
            + BANNER
        ),
        md(
            """## Ministry link

**CPO, TTDF, Finance, THA** asked for Government-controlled hosting. The cost card is how you argue for that without inventing a ministry budget.

**Labour / Health / Trade** will be asked “why not just ChatGPT?” — privacy and cost-per-acceptable-answer are the adult reply.

This lab is **N11** and **N7**. The two classroom models are both small. Phi-4 Mini stands in as the “other small open-weight” comparison (Azure-shaped). A closed frontier API is discussed on the card, not called.

## Overnight readers

You already have two doors (OLMo :8000, Phi :8001) or demo stand-ins. “Small vs large” is not a logo. It is **this prompt**: label + quote, milliseconds, whether the text left the building, who would pay. Keep the same `BACKEND` you set in T1-01 (re-run that cell if you opened a new kernel).
"""
        ),
        code(
            """# [RUN]
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
olmo = lab.chat(messages, model=cfg["model"])
phi = lab.chat(messages, model=cfg["comparison_model"])
print("OLMo", olmo["latency_ms"], "ms\\n", olmo["text"], "\\n")
print("Phi ", phi["latency_ms"], "ms\\n", phi["text"])
"""
        ),
        md(
            """### Teaching note

“Small” vs “large” is not a brand. It is measured on **this** prompt: did it label correctly, did it quote, how many milliseconds, could it run on the course GPU, did the text leave the building.

A larger closed model might write a prettier paragraph and still be the wrong buy for CVs or Cabinet search.

Classroom figures (order of magnitude, not a quote): treat the TTD 80,000 hosting envelope as the *course* bill, not a ministry TCO. On the card, estimate **cost per acceptable answer** as a ratio, not an invoice.
"""
        ),
        code(
            """# [CHANGE] fill these after you read both replies. 0–2 each: 0 wrong, 1 partial, 2 quote+label.
scores = {
    "olmo_quality_0to2": 0,
    "phi_quality_0to2": 0,
    "would_leave_the_building_if_this_were_ChatGPT": True,
    "who_would_pay": "laptop / Ministry VM / MEA Azure / hosted API / unsure",
}
print(scores)
lab.save_log("T1-03_scorecard", {"olmo": {k: olmo[k] for k in ("model","latency_ms","text","mode")},
                                 "phi": {k: phi[k] for k in ("model","latency_ms","text","mode")},
                                 "scores": scores})
"""
        ),
        md(
            """## Cost card (also on paper)

Open `cards/cost_card.md`. Fill it for **this** prompt only. Burst (fine-tune later) vs standing inference is a Day 3 mark; today just answer: if we left the GPU on overnight, who notices?

## Write-up

1. Which reply would you show a domain verifier (Labour HR / Health administrator)? Why?
2. Name one reason a closed API is cheaper *this afternoon* and one reason it is expensive for a core process.
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

**Time:** 13:45–14:20 &nbsp;|&nbsp; **Evidence:** licence notes + GPU question card

**Notebook learning outcomes**

- Distinguish open-source AI, open-weight, and proprietary APIs.
- Ask why two “24 GB” cards are not the same buy.

"""
            + BANNER
        ),
        md(
            """## Ministry link

| Question | Who asked it in the EOIs without using these words |
|---|---|
| Can we see the training data? | Anyone who must **explain** an output (Labour, Health, OPR, Finance) |
| Can we run it here? | **CPO, TTDF, Finance, THA** (N7) |
| Llama vs OLMo | Llama is often **open-weight + community licence**, not OSI |
| Azure already exists | Phi-4 Mini is in the room as the comparison, not the default |

**N4 named:** hosting choice is also an access choice — a public API is a disclosure path.

## Overnight readers

T1-01a put **weights** on disk. This notebook asks: what were you *allowed* to see, and is that enough to explain an output to Labour HR or an OPR officer? Open weight ≠ open source. ChatGPT is neither. The GPU card is the same “own the box” argument as T1-01a, with the burst vs standing split made explicit.
"""
        ),
        code(
            """# [RUN]
from pathlib import Path
print(Path("data/model_card_excerpts.md").read_text(encoding="utf-8"))
"""
        ),
        md(
            """### Teaching note

**Open weight** = you can download the file and run it. **Open source (OSAID-style)** = you can also inspect data, code, and how it was trained. **Closed product** = ChatGPT / Claude / Grok as a service.

OLMo is the course primary because the lineage is public enough to teach. Phi is the comparison because many GoRTT shops already speak Azure. Neither is “the ministry standard.” A later project still reads the live card.
"""
        ),
        code(
            """# [CHANGE] mark each row True/False
licence_notes = {
    "OLMo_weights_are_runnable_in_this_course": True,
    "OLMo_training_data_is_inspectable_in_principle": True,
    "Phi4mini_is_open_weight": True,
    "Phi4mini_is_treated_as_full_OSAID_here": False,
    "ChatGPT_gives_us_weights": False,
    "Llama_community_licence_equals_OSI": False,
    "vLLM_is_the_shared_server_path_today": True,
    "Ollama_is_a_typical_laptop_path_not_todays_lab": True,
}
assert licence_notes["Phi4mini_is_treated_as_full_OSAID_here"] is False
assert licence_notes["ChatGPT_gives_us_weights"] is False
print("licence notes accepted")
import civicdesk_lab as lab
lab.save_log("T1-04_licences", licence_notes)
"""
        ),
        md(
            """## GPU question card

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
            """## Write-up

1. In one line: OLMo vs Phi vs ChatGPT — what can you *see*?
2. Why might TTDF refuse a pretty public API even if it scored higher in T1-03?
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

**Time:** 14:20–14:55, then overnight 20–30 min &nbsp;|&nbsp; **Evidence:** canvas (`cards/usecase_canvas.md`)

**Notebook learning outcomes**

Write a testable use case a domain person can verify. Frame the *type* of problem in the EOI, not a live system.

**This block is (group).** Ministry groups of three to four. A singleton joins the same learning-need cluster. Each member still has this notebook open.

"""
            + BANNER
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

The morning was the machine. This is the **job**. Write a use case a domain person can mark wrong. You will not choose prompt vs RAG vs fine-tune until Day 2 (T1-06). Tonight: owner, verifier, baseline, measure, error cost, stop, data that stays out. CivicDesk names only — no live EOI attachments.
"""
        ),
        code(
            """# [CHANGE] fill as a group. Fictional CivicDesk names only.
canvas = {
    "organisation": "",
    "cluster": "A / B / C / D",
    "problem_in_one_line": "",
    "owner_role": "",
    "domain_verifier_role": "",
    "current_non_ai_baseline": "",
    "success_measure": "",
    "error_cost_if_wrong": "",
    "data_that_must_stay_out": "",
    "preferred_intervention_guess": "prompt / RAG / integration / fine-tune / none / unsure",
    "stop_condition": "",
    "one_cost_question": "",
    "next_question_for_MPAAI": "",
}
for k, v in canvas.items():
    print(f\"{k}: {v}\")
"""
        ),
        md(
            """### Teaching note

A fluent paragraph is not a use case. A domain verifier must be able to say “that output is wrong” using a measure you wrote down. Labour: evidence quote vs criterion. Trade: ticket fields complete, password not reset. Finance: citation present or abstain.

You will **not** finish the intervention label today. Day 2 morning (T1-06) is that argument. Overnight you add: owner, verifier, baseline, measure, error cost, stop, and three remaining questions.

Copy the dict into `cards/usecase_canvas.md` before you leave. Download this notebook at 14:55.
"""
        ),
        code(
            """# [RUN] save whatever you have. Empty strings are allowed at 14:55; overnight fills them.
import civicdesk_lab as lab
lab.save_log("T1-05_canvas_draft", canvas)
print("draft saved — finish overnight in cards/usecase_canvas.md")
"""
        ),
        md(
            """## Overnight 1 (20–30 min, no GPU)

Finish the canvas. Three remaining questions for Day 2. No home GPU. Do not fetch ministry files. If the lab was unfinished, also open `completed/T1-05_canvas_example.md`.

You can re-read T1-01a without starting servers: the point is the chain data → weights → runtime → API → output, and which of those you own. Tomorrow you add **retrieval** (approved handbook chunks) beside those frozen weights — you still will not train.
"""
        ),
    ],
)

print("done")
