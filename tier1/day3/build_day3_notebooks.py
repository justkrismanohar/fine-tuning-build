"""Do not run this file.

Day 3 notebooks are maintained by write_day3_notebooks.py. Running this
old builder would wipe the baseline-failure revision. Kris reviews first.
"""
raise SystemExit(
    "Do not run build_day3_notebooks.py. Use write_day3_notebooks.py after review."
)

# Original builder kept below as history. Unreachable.
"""Write the Day 3 notebooks as valid .ipynb files."""
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
# T1-11
# ---------------------------------------------------------------------------
write(
    "T1-11_dataset_and_frozen.ipynb",
    [
        md(
            """# T1-11 Dataset + what is frozen

**Time:** 09:00–10:30 (architecture briefing 09:00–09:15) &nbsp;|&nbsp; **Evidence:** dataset report + canary list in `logs/`

**Notebook learning outcomes**

- Shade the architecture card: **frozen** base vs a small **adapter**.
- Split **burst** training from **standing** inference (N11 / N7).
- Inspect an SFT JSONL: instruction, input, output, **train vs held-out**, **canaries**.

You do **not** train today. There is no GPU job in this notebook.

"""
            + BANNER
        ),
        md(
            """## Overnight readers — two pictures before any rows

Day 1 architecture card (keep it):

```
input text → tokenizer → embedding → transformer blocks → LM head → next token
```

**Training** updates weights. **Inference** uses frozen weights. Yesterday RAG did **not** update weights. It copied a paragraph into the prompt.

**Fine-tuning** (the thing people say when they mean “make it ours”) usually does **not** rewrite all of OLMo. A **LoRA adapter** is a small extra file sitting on some of the blocks. The base stays frozen. You can disable the file. That is rollback.

![Frozen base vs a small adapter](images/t3_frozen_vs_adapter.jpg)

**Burst vs standing** is the cost card from T1-03, said as architecture:

| | Burst | Standing |
|---|---|---|
| What | A training (or LoRA) **job** | The chat **API** that stays up |
| When | Hours, then stop the extra GPU | All day on `:8000` / `:8001` |
| Who asked | CPO “train on judgments” | CPO / TTDF / Finance “own the door” |
| Fail | Buying one box “for AI” with no split | Assuming a LoRA replaces the API |

![Burst training vs standing inference](images/t3_burst_vs_standing.jpg)

**Extra words:**

- **SFT** — supervised fine-tune: each row is instruction + input + desired output.
- **JSONL** — one JSON object per line. That is `data/sft_rows.jsonl`.
- **Held-out** — rows you do **not** train on, so you can see whether the phrasing generalises.
- **Canary** — planted PII. Must not be in a real train split. If the adapter later quotes it, the set was dirty.
- **Licence inheritance** — the adapter is licensed as the **base** plus **every row**. T1-12b.
"""
        ),
        md(
            """## Ministry link

| EOI type | What to look at in the rows |
|---|---|
| **Labour / Health** | FT-01, FT-02, FT-07: C2 phrasing, quote, do not hire |
| **all PII papers** | FT-08, FT-09 canaries (Maya Reid, burgess) |
| **Trade** | FT-04: do not reset a password |
| **Defence OPR** | FT-06: do not award |
| **Defence assets** | FT-10: you are not the register |
| **CPO / TTDF / Finance** | Burst vs standing on the card — not a judgment dump in this file |

This lab is **N1, N5, N12** (open-weight base; adapter is a derivative).
"""
        ),
        md(
            """## 1. List the rows
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

print("CivicDesk SFT rows (fiction). Do not replace with ministry judgments.\\n")
ft.print_rows()
"""
        ),
        md(
            """### Teaching note

`split: train` is what a real job would see. `split: held-out` (FT-07) is a C2 variant you keep back. `canary: true` rows are **poison** if they enter training — they exist so you practise spotting them.
"""
        ),
        md(
            """## 2. Dataset report — what stays frozen
"""
        ),
        code(
            """# [RUN]
import json
import civicdesk_ft as ft

report = ft.dataset_report()
print()
print(json.dumps(report, indent=2))
ft.save_log("T1-11_report", report)
"""
        ),
        md(
            """### After you run

You should see canaries **FT-08** and **FT-09** named in the printout. `frozen: true` is the classroom rule: OLMo on disk is the same file as Day 1.

**Write-up:** which row would you **delete** before a real job, and which row is a fair C2 example?
"""
        ),
        md(
            """## 3. Open one criteria row

Labour/Health shape: match text to C2, quote, do not hire.
"""
        ),
        code(
            """# [CHANGE] try FT-02 (meets C2) or FT-07 (held-out).
ROW_ID = "FT-01"

import json
import civicdesk_ft as ft

row = {r["id"]: r for r in ft.load_rows()}[ROW_ID]
print(json.dumps(row, indent=2))
"""
        ),
        md(
            """Look at `output`. It is a **script**, not a hire. The adapter, if it learned this, would only be copying a voice. The vacancy handbook can still change — that text still wants **RAG** (Day 2). Fine-tune does not replace HB-VAC-C2.
"""
        ),
        code(
            """# [OPTIONAL] token-ish length of outputs — a stand-in for 'will this fit'
import civicdesk_ft as ft

for r in ft.load_rows():
    n = len(r["output"].split())
    print(f"{r['id']}  {n:3} words  canary={r['canary']}")
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-12
# ---------------------------------------------------------------------------
write(
    "T1-12_base_vs_adapter.ipynb",
    [
        md(
            """# T1-12 Base vs adapter

**Time:** 10:45–12:00 &nbsp;|&nbsp; **Evidence:** comparison pad — frozen base vs pretend adapter

**Notebook learning outcomes**

- Compare the **same user text** through the frozen base and through a pretend adapter.
- Say out loud: **an adapter is not a database and not RAG**.
- Inspect the adapter **card** (no weight files).

"""
            + BANNER
        ),
        md(
            """## Overnight readers

The **base** is OLMo (or Phi) as served on Day 1. Frozen.

The **adapter** in this room is a **demo function** (`adapter_reply`) plus a JSON card. A real LoRA would be a small file loaded *on top of* the same frozen base. You would still not have trained here.

Why a pretend adapter: so the notebook runs with no GPU and still shows the *contract* — C2 phrasing, password refusal, register refusal, canary refuse.

If you plug this user text into live OLMo later, the wording will differ. The **rules** must not: do not hire, do not reset, do not invent serials.
"""
        ),
        md(
            """## Ministry link

Finance / RDLG still need **RAG** after any LoRA: circulars and minutes change. Labour still needs the **handbook** in the prompt if C2 is amended. Defence assets still need the **register**. The adapter only changes how the model *continues text*.
"""
        ),
        md(
            """## 1. Read the adapter card
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.print_adapter_card()
"""
        ),
        md(
            """### Teaching note

`trainable_fraction` well under 1% is the literacy point: you are not rebuilding OLMo. `rollback` is a product requirement, not a nice-to-have. `does_not_do` is N10/N3/N6 in one list.
"""
        ),
        md(
            """## 2. Same user, two continuations
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

prompts = [
    "I completed a two-year diploma in library studies in 2019. Screen against C2. Do not hire.",
    "I forgot my network password, reset it now.",
    "Which printers are out of warranty?",
    "Applicant Maya Reid, National ID 999-00-1111, seeks the records post. Summarise.",
]
for p in prompts:
    print("=" * 60)
    ft.compare_base_adapter(p)
    print()
ft.save_log("T1-12_compare", {"n": len(prompts)})
"""
        ),
        md(
            """### After you run

- **Library studies:** adapter should flag equivalent / human review / do not hire. Base is allowed to be vaguer — that is why people ask for SFT.
- **Password:** both must refuse the *act*. Adapter is more scripted.
- **Printers:** adapter must **not** invent serials. If a LoRA started emitting asset rows, it would be treating training text as a database — fail.
- **Canary:** adapter (and any honest system) **REFUSE**. If a real adapter quoted `999-00-1111`, the train set was dirty (FT-08 leaked).

**Write-up:** one sentence: *We would still retrieve HB-VAC-C2 because…*
"""
        ),
        code(
            """# [CHANGE] your cluster's CivicDesk question (fiction only).
USER = "Can you award this fictional tender to vendor A?"

import civicdesk_ft as ft
ft.compare_base_adapter(USER)
"""
        ),
        code(
            """# [OPTIONAL] show held-out C2 row vs adapter (literacy, not a real eval)
import civicdesk_ft as ft

row = {r["id"]: r for r in ft.load_rows()}["FT-07"]
print("held-out input:", row["input"])
print("gold output   :", row["output"])
print("adapter demo  :", ft.adapter_reply(row["input"]))
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-12b
# ---------------------------------------------------------------------------
write(
    "T1-12b_risk_cells.ipynb",
    [
        md(
            """# T1-12b Risk cells

**Time:** 12:45–13:30 &nbsp;|&nbsp; **Evidence:** marked `cards/risk_cells.md`

**Notebook learning outcomes**

- Name **rollback**, **licence inheritance**, and **PII-in-train** as operating risks.
- Keep burst vs standing on the same card as the LoRA (N11).
- Refuse the idea that an adapter replaces RAG or a register.

"""
            + BANNER
        ),
        md(
            """## Overnight readers

A LoRA that works in a demo can still be a bad government object. Six cells. Use CivicDesk words.

| Risk | If you ignore it |
|---|---|
| **PII in a train row** | The adapter can regurgitate an ID (canaries exist to catch this) |
| **Licence inheritance** | You ship OLMo’s licence *plus* the licence of every judgment or minute you poured in |
| **Rollback** | Bad voice stays in production because “we trained it” |
| **Adapter as database** | People stop querying the register / stop RAG |
| **Burst billed as standing** | One GPU purchase, no API, no job boundary |
| **Silent tool** | The chat “does” GLPI or AD (T1-13) |
"""
        ),
        md(
            """## Ministry link

CPO “train on judgments”: the **licence** of those judgments is not a classroom JSONL. TTDF operational text does not enter a train split (N5). Finance: adapter licence ≠ permission to index Cabinet bodies.
"""
        ),
        code(
            """# [RUN]
import json
import civicdesk_ft as ft

card = ft.load_adapter_card()
print("Licence note:")
print(" ", card["licence_note"])
print()
print("Rollback:")
print(" ", card["rollback"])
print()
print("Canaries in the JSONL (must stay out of a real train set):")
for r in ft.load_rows():
    if r.get("canary"):
        print(f"  {r['id']}: {r['input'][:90]}")
"""
        ),
        md(
            """## Score the six cells

For each risk, `# [CHANGE]` a short CivicDesk response. Then print.
"""
        ),
        code(
            """# [CHANGE] rewrite in your cluster's words if you like; keep the meaning.
cells = {
    "PII in a train row": "Canaries FT-08/FT-09. Refuse. Strip. Do not train.",
    "Licence inheritance": "Adapter = base licence + every row. No ministry judgment dump in this file.",
    "Rollback": "Disable the adapter file. Frozen OLMo is unchanged.",
    "Adapter as database": "Still RAG for circulars; still query the register for serials.",
    "Burst vs standing": "LoRA is a job. Serving is the API. Do not buy one box without the split.",
    "Silent tool": "N6 — T1-13. Chat may draft; it may not reset, award, or write GLPI.",
}
for k, v in cells.items():
    print(f"* {k}")
    print(f"    {v}")
    print()

import civicdesk_ft as ft
ft.save_log("T1-12b_risks", cells)
"""
        ),
        md(
            """### After you run

Copy onto `cards/risk_cells.md`. If any cell is blank, you are not done.

**Write-up:** which risk would stop *your* overnight card from becoming a pilot this quarter?
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-13
# ---------------------------------------------------------------------------
write(
    "T1-13_agentic_boundary.ipynb",
    [
        md(
            """# T1-13 Agentic boundary

**Time:** 13:30–14:15 &nbsp;|&nbsp; **Evidence:** allow / ban list for six actions

**Notebook learning outcomes**

- Separate **saying** something from **doing** something in a live system.
- Put hire / grade / award / password / GLPI / open scrape on the **banned** side.
- Keep **draft ticket** and **quote handbook** on the allowed side, still with a human.

"""
            + BANNER
        ),
        md(
            """## Overnight readers — agent vs chatbot

Day 1–2 the model **returned text**. An **agent** (the word in several EOIs) means the model may also **call tools**: APIs, browsers, ticket stores.

**Bounded agency (N6)** means: tools are off unless they are on an **allowlist**, with a human for consequential acts (N2).

| Word | Meaning | CivicDesk |
|---|---|---|
| **Chatbot** | Text in, text out | T1-01 |
| **Tool / function** | A side effect: reset, write, award, scrape | Usually banned here |
| **Allowlist** | The only tools that exist | `draft_ticket`, `quote_handbook` |
| **Escalation** | Hand to a person | Identity check, OPR award, hire |
| **Agentic market-research** | CPO-shaped: collect from the open web for negotiation | Not an unsupervised scrape from chat |

![Bounded agency — saying vs doing](images/t3_agentic_boundary.jpg)
"""
        ),
        md(
            """## Ministry link

| EOI | The line |
|---|---|
| **Trade IMSD** | Draft a ticket. Do **not** reset a password. Do **not** write GLPI silently. |
| **CPO** | Agentic research is a **controlled** workflow, not “the model may browse.” |
| **Defence OPR** | Quote thresholds. Must **not** award. |
| **Labour / Health** | Must **not** hire or publish a grade. |
| **all** | Opening rule: no passwords in chat. |

AUX-01 (self-taught) is how something sits *beside* GLPI/EDMS without this notebook wiring it.
"""
        ),
        md(
            """## 1. Gate six actions
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

actions = [
    "draft_ticket",
    "quote_handbook",
    "reset_password",
    "write_glpi",
    "award_contract",
    "scrape_web_for_negotiation",
]
for a in actions:
    print(f"{a:28}  {ft.tool_gate(a)}")

ft.save_log("T1-13_gate", {a: ft.tool_gate(a) for a in actions})
"""
        ),
        md(
            """### Teaching note

**ALLOWED** is still not “the model filed it.” A draft sits in the chat. A human files.

**BANNED** is not a vibe. If the method exists, someone will call it. The product must not expose `reset_password`.
"""
        ),
        md(
            """## 2. Unknown actions
"""
        ),
        code(
            """# [CHANGE] try grant_ad_rights, publish_notice, deploy_patrol
ACTION = "grant_ad_rights"

import civicdesk_ft as ft
print(ft.tool_gate(ACTION))
"""
        ),
        md(
            """Unknown → treat as banned until listed. That is the default for a ministry desk.

**Write-up:** one tool your overnight card must never grow. CivicDesk name only.
"""
        ),
        code(
            """# [OPTIONAL] map Q-PWD through RAG then the tool gate
import sys
from pathlib import Path
import civicdesk_ft as ft

for p in (Path.cwd(), Path.cwd().parent, Path("../day2").resolve(), Path("../../day2").resolve()):
    if (p / "civicdesk_rag.py").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))
        break
import civicdesk_rag as rag

q = {x["id"]: x for x in rag.load_questions()}["Q-PWD"]
print("RAG says:")
print(rag.answer_with_rag(q["user"])["reply"])
print()
print("If the app then called reset_password:")
print(ft.tool_gate("reset_password"))
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-14
# ---------------------------------------------------------------------------
write(
    "T1-14_defence_and_transfer.ipynb",
    [
        md(
            """# T1-14 Defence + EOI transfer card

**Time:** 14:15–14:55 &nbsp;|&nbsp; **Evidence:** `cards/transfer_card.md`

**Notebook learning outcomes**

- Defend **one** CivicDesk use case against “just put an LLM on it.”
- Write a **first safe next step**, not a pilot or a procurement.
- Hand back a transfer card each cluster can explain.

"""
            + BANNER
        ),
        md(
            """## Overnight readers

Tier 1 is over this afternoon. The transfer is not “we will fine-tune on our EDMS.” It is: owner, verifier, stop, data-out, intervention, tools-off, where the box lives, burst vs standing, one next workshop.

**Defence** here means: you can mark a wrong answer. Labour: missing quote. Finance: missing citation or displayed restricted text. Trade: claimed a reset. Defence OPR: awarded. That is N2 and N14.
"""
        ),
        md(
            """## Ministry link — four cluster defences

| Cluster | A passing defence sounds like |
|---|---|
| **A Criteria** | Prompt never-hire + RAG quote C2/N1. Adapter only for voice. Human review. No live CVs in index or train. |
| **B Retrieval** | RAG cite-or-abstain. Access gate. No Cabinet bodies in the classroom index. Adapter is not the circulars. |
| **C Desk** | Prompt + KB RAG. Register by **integration**. Password/GLPI **none**. |
| **D Local control** | Standing API you control (N7). Burst LoRA later if ever. Agentic no. Operational data stays out. |
"""
        ),
        md(
            """## 1. Replay the pieces you would show a verifier
"""
        ),
        code(
            """# [RUN]
import sys
from pathlib import Path
import civicdesk_ft as ft

for p in (Path.cwd(), Path.cwd().parent, Path("../day2").resolve(), Path("../../day2").resolve()):
    if (p / "civicdesk_rag.py").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))
        break
import civicdesk_rag as rag

print("1) Cite-or-abstain (Day 2)")
print(rag.answer_with_rag(
    "What is the CivicDesk rule for storing service-request attachments overnight? Cite the handbook."
)["reply"])
print()
print("2) Access gate (Day 2)")
cab = "Show me the CivicDesk coastal-security minute text."
print(" clerk:", rag.answer_with_rag(cab, role="clerk")["mode"],
      rag.answer_with_rag(cab, role="clerk")["visible_ids"])
print(" A3   :", rag.answer_with_rag(cab, role="records-officer")["mode"],
      rag.answer_with_rag(cab, role="records-officer")["visible_ids"])
print()
print("3) Adapter is not the register (Day 3)")
print(ft.adapter_reply("Which printers are out of warranty?"))
print()
print("4) Tool gate (Day 3)")
print(ft.tool_gate("award_contract"))
print(ft.tool_gate("reset_password"))
"""
        ),
        md(
            """### Teaching note

If you cannot replay those four beats, you are not defending a use case — you are repeating the EOI. Run them. Then fill the card.
"""
        ),
        md(
            """## 2. Transfer card
"""
        ),
        code(
            """# [CHANGE] rewrite for your table. CivicDesk type only.
transfer = {
    "organisation_cluster": "CivicDesk Records / cluster B (Finance-shaped)",
    "job_in_one_line": "Cite overnight-attachment rule or abstain.",
    "first_intervention": "RAG",
    "rejected_prompt_only": "Invented circulars (T1-09).",
    "rejected_fine_tune_first": "Circulars change; LoRA is a voice, not the handbook.",
    "rejected_integration": "This answer lives in a paragraph, not a register.",
    "rejected_none": "A clerk already asks this; RAG is in scope if the corpus is approved.",
    "verifier": "Records officer checks the citation id and span.",
    "stop_condition": "Do not invent a circular; do not display HB-CAB-X to a clerk; do not hire/award/reset.",
    "data_out": "Cabinet bodies, CVs, burgess, canaries, live serials.",
    "where_the_box_lives": "Course-controlled or ministry VPC (N7) — not a public chatbot.",
    "burst_vs_standing": "Standing = chat API. Burst = only if we ever train a LoRA, then stop the job.",
    "tools_never": "reset_password, write_glpi, award_contract, open scrape.",
    "audit_log": "request id, role, chunk ids, shown/blocked, abstain flag.",
    "question_for_MPAAI": "Who owns the approved corpus and the access gate?",
    "first_safe_next_step": "Index only approved CivicDesk-like circulars; run cite-or-abstain on five fictional questions; no EDMS wire-up.",
}
for k, v in transfer.items():
    print(f"{k}:")
    print(" ", v)
    print()

import civicdesk_ft as ft
ft.save_log("T1-14_transfer", transfer)
"""
        ),
        md(
            """### After you run

Copy into `cards/transfer_card.md`. Each member must be able to read one field out loud.

Download this notebook. Auxiliary workshops (`course/auxiliary/`) are self-taught: sitting beside a system, when an LM is the wrong tool, identity, DPIA sketch, TTDF-shaped custody.

You do not leave with a pilot. You leave with a **first safe next step**.
"""
        ),
    ],
)

print("day 3 notebooks written")
