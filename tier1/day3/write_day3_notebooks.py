"""Write the five Day 3 learner notebooks. Not build_day3_notebooks.py."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in source.strip("\n").split("\n")]}


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
    path.write_text(json.dumps(nb(cells), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", path.name)


BANNER = """
**How to use this notebook**

- **No-code / code-light:** run every cell in order. Read the teaching note after a cell. Fill the write-up. Do not paste work files.
- **Occasional-code:** run all cells. Change only lines marked `# [CHANGE]`.
- **Deep-code:** optional cells are tagged `# [OPTIONAL]`. Stay with the room on the required path. Do not drive someone else's notebook.

Git is not required. If you are stuck, load the matching file in `completed/` for this notebook only, mark it as loaded from reference, and continue.
"""

BAN = """**Data ban:** CivicDesk fiction only. The frozen held-out cases are a **test** set. Do not train on them. Do not paste ministry CVs, tickets or minutes."""

BACKEND = """# [CHANGE] olmo is the classroom default. phi needs :8001. demo = labelled stand-ins, not scored.
BACKEND = "olmo"  # "olmo" | "phi" | "demo"

import civicdesk_ft as ft

cfg = ft.set_backend(BACKEND)
"""

write(
    "T1-11_dataset_and_frozen.ipynb",
    [
        md(
            """# T1-11 Prove the prompt fails, then inspect what extra practice would teach

**Time:** 09:00–10:30 (architecture 09:00–09:15) &nbsp;|&nbsp; **Evidence:** pre-flight JSON in `logs/` + training-row report

**Notebook learning outcomes**

- Shade the architecture card: **frozen** base vs a small **adapter**.
- Split **burst** training from **standing** inference.
- **Prove** that a careful prompt still fails on this machine (or say clearly that it did not).
- Inspect the **criteria** training rows the adapter would see. `human_review` is the centre of the job.

"""
            + BANNER
            + "\n\n"
            + BAN
        ),
        md(
            """## Overnight readers — two pictures before any rows

Day 1 architecture card (keep it):

```
input text → tokenizer → embedding → transformer blocks → LM head → next token
```

**Training** updates weights. **Inference** uses frozen weights. Yesterday RAG did **not** update weights.

**Fine-tuning** here is a **LoRA adapter**: a small extra file on some of the blocks. The base stays frozen. Disable the file = rollback.

**Burst vs standing**

| | Burst | Standing |
|---|---|---|
| What | A training (or LoRA) **job** | The chat **API** that stays up |
| When | Hours, then stop the extra GPU | All day on `:8000` / `:8001` |
| Fail | Buying one box “for AI” with no split | Assuming a LoRA replaces the API |

**Headline task today:** résumé **criteria** (`meets` / `does_not_meet` / `human_review`). Tickets are Track A. Redaction stays aligned with the Day 1 40-document test. Minutes are a stretch.

**The prompt is a description of the job.** One worked example in a prompt is copied. Hundreds of labelled rows in training teach the pattern.
"""
        ),
        md(
            """## Ministry link

| Cluster | What fails in the frozen set |
|---|---|
| **Labour / MOLSED** | Criteria: silence labelled as failure; in-progress counted as meets |
| **Trade / MTIT** | Tickets: security buried under a printer; none of four incidents escalated in the CPU reference |
| **Rural Development / MRDLG** | Minutes: a defeated motion logged as work to chase |
| **all PII papers** | Redaction: example header pasted, then the real name underneath |

This lab is **N1** (quote a span) and **N2** (human_review is not a fail).
"""
        ),
        md("## 0. Backend"),
        code(BACKEND),
        md(
            """## 1. Where a LoRA would sit

`print_anatomy` reads the OLMo **config**, not the weights. Type the attention names from the printout.
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.print_anatomy()
"""
        ),
        code(
            """# [CHANGE] fill from the printout. Then try four attention names, then all seven.
TARGETS = ["q_proj", "v_proj"]
RANK = 8

import civicdesk_ft as ft

ft.lora_param_count(TARGETS, RANK)
"""
        ),
        md(
            """## 2. Pre-flight — prove the problem on *this* machine

Load the frozen 20-case set (7 CVs, 9 tickets, 4 excerpts). Call the **base** model at temperature 0. Save a dated JSON.

The notebook **must not** reuse percentages from a briefing note. If a tripwire does not fire, that is a real result: print the notice. Do not fake a failure.
"""
        ),
        code(
            """# [CHANGE] drop a task if the room is short on time. Default is all four.
TASKS = ["criteria", "tickets", "redaction", "minutes"]

import civicdesk_ft as ft

record = ft.run_preflight(TASKS)
"""
        ),
        md(
            """### Teaching note

- **criteria** is scored **one criterion per call** — the format the adapter will train on.
- R2 is also stored as a **multi-criteria** call so the teaching card matches the prompt that copied the example.
- `BACKEND=demo` or a down server: the cell writes an unmeasured file and tells you to use the labelled CPU cards. Those cards are **not** this session's score.
"""
        ),
        md("## 3. Three failures, one per scenario"),
        code(
            """# [CHANGE] "R2-criteria" | "T1" | "M1"
SHOW = "R2-criteria"

import civicdesk_ft as ft

ft.show_failure(SHOW)
"""
        ),
        md(
            """**Write-up:** in one line, what did the prompt *ask* for, and what did the model *do*? Then change `SHOW` and run the other two.
"""
        ),
        md(
            """## 4. Generate the criteria training rows

Seeded script. Asserts: evidence is a substring, `does_not_meet` never has empty evidence, no held-out names or criterion types.
"""
        ),
        code(
            """# [RUN]
import runpy
from pathlib import Path

runpy.run_path(str(Path("build_criteria_set.py")), run_name="__main__")
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

rows = ft.inspect_criteria_rows()
"""
        ),
        md(
            """**Write-up:** which of your T1-05 gold pairs does this set cover, and which does it miss? Silence → `human_review` is the policy this file teaches. A stricter unit might label an unrelated degree as `does_not_meet`. Say which policy you would take back.
"""
        ),
        md(
            """## 5. Also inspect the redaction hunt (same 40-document test as Day 1)

The redaction adapter, if it exists, is scored on **that** test, not on today's 7-CV stress slice. Find five planted problems in the inspect file.
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.inspect_training_rows()
"""
        ),
        code(
            """# [CHANGE] put the row id, or None for the set-level problem.
FOUND = {"leak": None, "inconsistent": None, "canary": None, "rewrite": None, "imbalance": None}

import civicdesk_ft as ft

ft.score_hunt(FOUND)
"""
        ),
        md(
            """## Appendix — CivicDesk warm-up rows

FT-01..FT-10 stay as literacy rows. FT-07 is a near-copy of FT-01: the same leak in miniature. Canaries FT-08 / FT-09 and TR-P3 never enter a real train split.
"""
        ),
        code(
            """# [OPTIONAL] warm-up list
import civicdesk_ft as ft

ft.print_rows()
"""
        ),
        code(
            """# [OPTIONAL] short LoRA job on the learner GPU. Skip with no GPU.
# The evaluated classroom adapter is the pre-built directory, not this run.
!python train_adapter.py --task criteria --max-steps 30 --time-cap-s 180 --out adapters/learner_run
"""
        ),
    ],
)

write(
    "T1-12_base_vs_adapter.ipynb",
    [
        md(
            """# T1-12 Same held-out cases: base vs floor vs adapter

**Time:** 10:45–12:00 &nbsp;|&nbsp; **Evidence:** confusion matrix + harmful-error count in `logs/`

**Notebook learning outcomes**

- Re-score **criteria** on the frozen set with the **same** one-criterion prompt.
- Put the **rule floor** next to the base (if evidence is not a substring, force `human_review`).
- Read the **redaction** 40-document comparison from run files (HOLD / PASS CHECKS). Nothing here promises the adapter is better.

"""
            + BANNER
            + "\n\n"
            + BAN
        ),
        md(
            """## Overnight readers

The **base** is OLMo as served on Day 1. Frozen.

A **LoRA** would be a small file on that base. This pack may not contain measured adapter weights yet. If `olmo_adapter_v1.json` is missing, the redaction comparison uses a **demo** file labelled not scored, and criteria comparison uses the **floor**, not a fake win.
"""
        ),
        md(
            """## Ministry link

Labour: `human_review` recall and the count of **human_review → does_not_meet** (an applicant marked as failing for something the CV never addressed).
"""
        ),
        md("## 0. Backend"),
        code(BACKEND),
        md("## 1. Adapter card"),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.print_adapter_card()
"""
        ),
        md(
            """## 2. Criteria — this session's base numbers

If pre-flight did not run live, this cell says so. Do not type percentages from memory.
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.print_preflight_metrics()
"""
        ),
        md(
            """## 3. Simplest thing first: the evidence floor

If the model's evidence string is not copied from the résumé, force `human_review`. If this floor gets most of the gain, that is an honest result.
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

floored = ft.floor_from_preflight()
"""
        ),
        md(
            """## 4. Redaction — the same 40 documents as Day 1

Per document: **HOLD** or **PASS CHECKS**. Per run: **meets** or **does not meet** the example rule. A one- or two-document swing is noise.
"""
        ),
        code(
            """# [RUN]
import civicdesk_ft as ft

cmp = ft.compare_runs(ft.baseline_run_path(), ft.adapter_run_path())
ft.save_log("T1-12_compare", cmp)
"""
        ),
        md(
            """## 5. Two or three documents, both ways
"""
        ),
        code(
            """# [CHANGE] test ids from the Day 1 40-document file
DOC_IDS = ["B01", "B12"]

import civicdesk_ft as ft

try:
    redact = ft.load_redactor()
    print("live redactor")
    from pathlib import Path
    import json, sys
    sys.path.insert(0, str(Path("../shared/resume_redaction").resolve()))
    import redaction_eval as R
    bench = R.load_benchmark()
    by = {d["id"]: d for d in bench["docs"]}
    for did in DOC_IDS:
        doc = by[did]
        print("=" * 60, did)
        for flag, tag in ((False, "base"), (True, "adapter")):
            out = redact(doc["text"], use_adapter=flag)
            sc = R.score_doc(doc, out)
            fired = R.release_checks(out, doc.get("form"))
            decision, reasons = R.route(fired, out, doc)
            print("---", tag, "---")
            print(out[:400])
            print("leaked", sc["leaked"], "route", decision)
except Exception as exc:
    print("live unavailable:", exc)
    ft.docs_from_runs(DOC_IDS)
"""
        ),
        md(
            """## 6. Failure analysis

List three criteria cases the **base** (or the floor) still gets wrong. For each: more data, a rule, RAG, or a human?
"""
        ),
        code(
            """# [CHANGE] keep three ids after you read the printout
STILL_WRONG = []

import civicdesk_ft as ft

print("from this session:")
ft.still_wrong_criteria()
print("your list:", STILL_WRONG)
"""
        ),
        md(
            """## 7. Probes — an adapter is not a database
"""
        ),
        code(
            """# [RUN]
import json
from pathlib import Path
import civicdesk_ft as ft

probe = json.loads(Path("data/demo/not_a_database_probe.json").read_text(encoding="utf-8"))
print(probe.get("question") or probe)
print("An adapter does not look up a handbook. That was Day 2.")
"""
        ),
        code(
            """# [OPTIONAL] tickets Track A preview (full treatment in T1-13)
import civicdesk_ft as ft

ft.show_failure("T1")
"""
        ),
        code(
            """# [OPTIONAL] unfamiliar layout / cabinet note (not in the redaction train set)
import json
from pathlib import Path

docs = json.loads(Path("data/demo/unfamiliar_layouts.json").read_text(encoding="utf-8"))
print(docs.get("note"))
for d in docs["docs"]:
    print("---", d["id"], d["layout"], "---")
    print(d["text"][:300])
"""
        ),
        code(
            """# [OPTIONAL] regex floor on one stress CV (emails and phones only)
import civicdesk_ft as ft

ft.print_redaction_floor("R2")
"""
        ),
        md("Phi-4 Mini is a generate-only column here unless a measured `phi_baseline_v1.json` exists."),
    ],
)

write(
    "T1-12b_risk_cells.ipynb",
    [
        md(
            """# T1-12b Risk cells

**Time:** 12:45–13:30 &nbsp;|&nbsp; **Evidence:** marked `cards/risk_cells.md`

**Notebook learning outcomes**

- Name **rollback**, **licence inheritance**, and **PII-in-train** as operating risks.
- Cite **today's** evidence, not a ministry anecdote.

"""
            + BANNER
            + "\n\n"
            + BAN
        ),
        md(
            """## Overnight readers

If the add-on is wrong, you **stop loading the directory** and rerun the benchmark. That is rollback. Licence of an adapter = base licence + every training row. A canary in train is a memorisation fail.
"""
        ),
        md(
            """## Ministry link

Finance / CPO: GPU hours are a **burst** bill. Labour: releasing a PASS CHECKS résumé is still a person. Trade: an adapter that routes tickets is not permission to reset a password.
"""
        ),
        md("## 0. Backend"),
        code(BACKEND),
        code(
            """# [RUN]
from pathlib import Path

print(Path("cards/risk_cells.md").read_text(encoding="utf-8"))
"""
        ),
        md("## Score the six cells"),
        code(
            """# [CHANGE] rewrite in your cluster's words; keep the meaning. Cite today's printouts.
CELLS = {
    "overfitting": "Broken list / still-wrong criteria ids from T1-12",
    "memorisation": "TR-P3 canary. It must not be in a real train split.",
    "licence": "Day 1 T1-04 files. Adapter licence = base + every row.",
    "gpu_hours": "training_report.json when present; else the adapter card count. Burst, not standing.",
    "rollback": "Stop loading the adapter directory, rerun the held-out set.",
    "release": "PASS CHECKS is not a release. human_review is not a hire.",
}

import json
import civicdesk_ft as ft

print(json.dumps(CELLS, indent=2))
ft.save_log("T1-12b_risks", CELLS)
"""
        ),
        md(
            """### After you run

Each cell needs a pointer to a file or printout from **today**. Copy the table into `cards/risk_cells.md` if you want a paper copy.
"""
        ),
    ],
)

write(
    "T1-13_agentic_boundary.ipynb",
    [
        md(
            """# T1-13 Agentic boundary + ticket routing (Track A)

**Time:** 13:30–14:15 &nbsp;|&nbsp; **Evidence:** allow/ban list + ticket security recall

**Notebook learning outcomes**

- Separate **saying** something from **doing** something in a live system.
- See why a prompt that says “if ANY problem is security, escalate” still classified a printer.
- Keep hire / grade / award / password reset / GLPI / open scrape on the **banned** side.

"""
            + BANNER
            + "\n\n"
            + BAN
        ),
        md(
            """## Overnight readers — agent vs chatbot

A chatbot **writes text**. An agent **calls a tool** that changes a live system. The model can draft a ticket. It must not reset a password, write GLPI, or escalate “in the system.” Escalation as **text** is still a draft until a person files it.
"""
        ),
        md(
            """## Ministry link

**Trade IMSD:** T1 in the frozen set is a phishing password typed on a fake page, buried under a printer jam. Gold is `security_incident` / `escalate_security` / `high`.
"""
        ),
        md("## 0. Backend"),
        code(BACKEND),
        md("## 1. The T1 ticket"),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.show_failure("T1")
"""
        ),
        md(
            """**Write-up:** the user typed a password on a fake page. The model talked about the printer. What would you add to **training** (not to the prompt) so security wins?
"""
        ),
        md("## 2. Ticket training mix (security buried, injection, shouting)"),
        code(
            """# [RUN]
import runpy
from pathlib import Path
import civicdesk_ft as ft

runpy.run_path(str(Path("build_tickets_set.py")), run_name="__main__")
ft.inspect_ticket_rows()
"""
        ),
        md("## 3. Gate six (now nine) actions"),
        code(
            """# [RUN]
import civicdesk_ft as ft

for action in [
    "draft_ticket",
    "quote_handbook",
    "draft_redacted_copy",
    "reset_password",
    "write_glpi",
    "award_contract",
    "scrape_web_for_negotiation",
    "release_to_panel",
    "auto_release_if_pass_checks",
]:
    print(f"{action:32} {ft.tool_gate(action)}")
"""
        ),
        md(
            """### Teaching note

ALLOWED is still **saying**. BANNED is **doing**. `auto_release_if_pass_checks` is banned because PASS CHECKS means no check fired, not that the document is clean.
"""
        ),
        md("## 4. Unknown actions"),
        code(
            """# [CHANGE] try grant_ad_rights, publish_notice, deploy_patrol
ACTION = "grant_ad_rights"

import civicdesk_ft as ft

print(ACTION, ft.tool_gate(ACTION))
"""
        ),
        code(
            """# [OPTIONAL] injection ticket T8 from the frozen set
import civicdesk_ft as ft
from heldout.cases import TICKETS

t8 = next(t for t in TICKETS if t["id"] == "T8")
print(t8["text"])
print("gold:", t8["gold"])
print("If pre-flight ran, T8 is in logs/preflight_latest.json outputs.tickets")
"""
        ),
    ],
)

write(
    "T1-14_defence_and_transfer.ipynb",
    [
        md(
            """# T1-14 Defence + EOI transfer card

**Time:** 14:15–14:55 &nbsp;|&nbsp; **Evidence:** `cards/transfer_card.md`

**Notebook learning outcomes**

- Close on the policy line: **AI assists. HR validates. Authorized officers decide.**
- Treat minutes extraction as a **partial** case — hardest to score, most likely to stay imperfect after a 1B LoRA.
- Write a **first safe next step**, not a pilot.

"""
            + BANNER
            + "\n\n"
            + BAN
        ),
        md(
            """## Overnight readers

A better `human_review` rate makes the human's queue more accurate. It does not remove the human. Minutes that log a defeated motion as work would send the corporation chasing the wrong thing.
"""
        ),
        md(
            """## Ministry link

Defence / every cluster: the transfer card is one workshop you could run next week without going live. Not a procurement.
"""
        ),
        md("## 0. Backend"),
        code(BACKEND),
        md("## 1. Policy line"),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.policy_line()
"""
        ),
        md("## 2. Minutes (Track B / stretch) — one excerpt"),
        code(
            """# [RUN]
import civicdesk_ft as ft

ft.show_failure("M1")
print()
print("Stretch: we do not claim a 1B LoRA will clean this. Frame any later adapter as partial improvement.")
"""
        ),
        md("## 3. Numbers you actually have"),
        code(
            """# [RUN]
from pathlib import Path
import json
import civicdesk_ft as ft

print("--- criteria pre-flight (this machine only if measured) ---")
ft.print_preflight_metrics()
print("--- redaction compare_runs ---")
try:
    cmp = ft.compare_runs(ft.baseline_run_path(), ft.adapter_run_path())
except Exception as exc:
    cmp = {"error": str(exc)}
    print(exc)
day2 = Path("../day2/logs/replay/T1-09_run1.json")
print("Day 2 known-answer file:", day2.is_file())
ft.save_log("T1-14_transfer", {"redaction": {k: cmp[k] for k in cmp if k != "error"} if isinstance(cmp, dict) else {}, "day2_replay": day2.is_file()})
"""
        ),
        md("## 4. Transfer card"),
        code(
            """# [CHANGE] fill in your cluster's words. Keep "first safe next step", not a pilot.
CARD = {
    "organisation": "",
    "job_in_one_line": "first-pass résumé criteria with human_review as the default for silence",
    "intervention": "inspect-adapter / prompt / RAG / none",
    "why_not_the_others": "",
    "human_who_verifies": "",
    "stop_condition": "hire / grade / award / reset / publish",
    "data_that_stays_out": "real CVs, national IDs, tickets with real names",
    "where_the_box_lives": "",
    "burst_vs_standing": "",
    "tools_never": "reset_password, write_glpi, award_contract, release_to_panel",
    "audit": "request id, prompt version, gold file sha256, abstain/human_review",
    "question_for_mpaai": "",
    "first_safe_next_step": "",
    "day1_baseline_rule": "meets or does not meet (redaction example rule)",
    "day3_adapter_rule": "meets or does not meet, or not measured",
    "docs_fixed": [],
    "docs_broken": [],
    "cost_per_acceptable_base": "not measured",
    "cost_per_acceptable_adapter": "not measured",
    "data_prep_roadmap": "",
    "who_maintains": "Tier 2 question",
}

import json
from pathlib import Path
import civicdesk_ft as ft

print(json.dumps(CARD, indent=2))
print()
print(Path("cards/transfer_card.md").read_text(encoding="utf-8"))
ft.save_log("T1-14_transfer_card", CARD)
"""
        ),
        md(
            """### After you run

Hand the card to the next cluster. If they cannot explain `human_review`, the card is not done.
"""
        ),
    ],
)

print("done")
