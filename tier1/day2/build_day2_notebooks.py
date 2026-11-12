"""Write the Day 2 notebooks as valid .ipynb files."""
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
# T1-06
# ---------------------------------------------------------------------------
write(
    "T1-06_intervention_map.ipynb",
    [
        md(
            """# T1-06 Intervention map (group)

**Time:** 09:00–09:20 &nbsp;|&nbsp; **Evidence:** a label on last night’s canvas (`cards/intervention_map.md`)

**Notebook learning outcomes**

- Name five interventions: **prompt**, **RAG**, **integration**, **fine-tune**, **none**.
- Pick one for a CivicDesk problem and say why the others are the wrong first move.
- Point at which ministry *type* that problem stands in for — not a live system.

**This block is (group).** Same tables as T1-05. Each member still has this notebook open.

"""
            + BANNER
        ),
        md(
            """## Overnight readers — what “intervention” means

Day 1 ended with a canvas and a *guess*: prompt / RAG / fine-tune / none. This morning you have to **defend a label**.

An **intervention** is what you change so the next CivicDesk answer is safer or more useful. It is not “buy an LLM.” Five labels cover almost every EOI in the room:

| Label | You change… | You do **not** change… |
|---|---|---|
| **prompt** | The standing instruction (`role: system`) and maybe a few examples in the messages | Weights, index, live systems |
| **RAG** | Which **approved paragraph** is copied into the prompt this turn | Weights. The handbook can be updated tomorrow without retraining |
| **integration** | A **query** to a register, GLPI, GIS, or ticket store | The model is not the source of truth |
| **fine-tune** | A **small adapter** on frozen weights (Day 3: inspect, do not train) | The whole foundation model. Not a substitute for a handbook or a database |
| **none** | The work stays with a person, a form, or a non-LM tool | Do not force a chatbot onto GIS tracks or a password reset |

**Extra words (not on the Day 1 canvas, still needed):**

- **Grounding** — the reply is tied to text you can point at. RAG grounds. Prompt-only often does not.
- **Hallucination** — fluent text with no source. Day 1 already saw invented circulars. T1-09 will pair it with RAG.
- **Source of truth** — where a correct answer *lives*. For serials it is a register (N10). For C2 it is a published handbook (N1). For “reset the account” it is a human (N6).

![Which intervention?](images/t2_intervention_map.jpg)
"""
        ),
        md(
            """## Ministry link — pick the row for your table

| Cluster | Sit with | First-move pressure |
|---|---|---|
| **A Criteria** | Labour, Health | Prompt (“never hire / never publish a grade”) plus later RAG to **quote** C2 or N1. Fine-tune is a *voice*, not the rulebook. |
| **B Retrieval** | Finance, Defence OPR, MPSDFS policy, MOWI ECMS, RDLG minutes, THA | RAG. Do not fine-tune a model to memorise every circular. |
| **C Service desk** | Trade IMSD, Defence assets-as-query | Prompt + RAG for KB. **Integration** for serials. **None** for password reset. |
| **D Local control** | CPO, TTDF | Where the box lives is Day 1/3. Many CPO “train on judgments” stories are RAG + custody, not a LoRA on day one. TTDF patrol: **none** (AUX-05). |

This notebook is **N1–N3, N10, N15** as a map. You will *build* RAG in T1-08, not here.
"""
        ),
        md(
            """## 1. Six CivicDesk problems — read before you score

Each row is fiction. Gold labels are teaching answers. Argue at the table before you look at `GUESSES`.
"""
        ),
        code(
            """# [RUN]
import json
import civicdesk_rag as rag

print("Data ban: CivicDesk fiction only. No ministry files in a cell.\\n")
for c in rag.load_intervention_cases():
    print(f"{c['id']}  [{c['stands_in_for']}]")
    print("   ", c["problem"])
    print()
"""
        ),
        md(
            """### Teaching note

**IC-01** looks like “an LLM that knows circulars.” The paragraph already exists. That is **RAG**. Fine-tuning would freeze yesterday’s wording.

**IC-02** is Day 1 again. The visitor did not change. The wall instruction did. **prompt**.

**IC-03** is **integration** (or **none** if you refuse to guess serials). T1-05 named this: the model is not the register.

**IC-04** is the only honest **fine-tune** in the set: a *stable phrasing* (“quote, flag equivalent, do not hire”). The C2 *text* can still move; that part stays RAG.

**IC-05** and **IC-06** are **none**. One is operational data. One is a privileged act. A fluent chatbot is the wrong object.

If your overnight canvas said “an LLM” with no label, pick one now. Unsure is allowed only with a question attached.
"""
        ),
        md(
            """## 2. Score the map

`# [CHANGE]` only if you want to test yourself with different labels. Allowed strings: `prompt`, `RAG`, `integration`, `fine-tune`, `none`.
"""
        ),
        code(
            """# [CHANGE] try your table's labels first; this cell ships the teaching key so Run All works.
GUESSES = {
    "IC-01": "RAG",
    "IC-02": "prompt",
    "IC-03": "integration",
    "IC-04": "fine-tune",
    "IC-05": "none",
    "IC-06": "none",
}

import civicdesk_rag as rag

rag.score_interventions(GUESSES)
rag.save_log("T1-06_map", {"guesses": GUESSES})
"""
        ),
        md(
            """### After you run

Copy one line onto `cards/intervention_map.md`: **your T1-05 guess → your T1-06 label**. If they differ, that is the learning.

**Write-up (one sentence):** which intervention will *your* cluster practise this afternoon, and which one must you *not* pretend to have built today?
"""
        ),
        code(
            """# [OPTIONAL] deep-code: count how many EOI types in the handbook metadata are retrieval-shaped.
import civicdesk_rag as rag
from collections import Counter

c = Counter()
for ch in rag.load_chunks():
    for s in ch.get("stands_in_for", []):
        c[s.split("(")[0].strip()] += 1
print("chunk mentions (not a ministry ranking):")
for k, n in c.most_common():
    print(f"  {n:2}  {k}")
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-07
# ---------------------------------------------------------------------------
write(
    "T1-07_data_classification.ipynb",
    [
        md(
            """# T1-07 Data classification

**Time:** 09:20–10:30 &nbsp;|&nbsp; **Evidence:** classification score on CI-01…CI-10

**Notebook learning outcomes**

- Say what an **index** is, in CivicDesk words.
- Label a piece of text **INDEX** or **NEVER**.
- Explain a **canary**, and why clearance is not the same as “allowed in the index.”

"""
            + BANNER
        ),
        md(
            """## Overnight readers — the new words

Yesterday the model only saw what you typed. Today you will give it a **corpus**: a pile of approved CivicDesk paragraphs. Before you pile them, you classify.

| Word | Plain meaning | CivicDesk example |
|---|---|---|
| **Corpus** | The set of documents you are willing to search | Twelve fictional handbook chunks, not an EDMS export |
| **Chunk** | One retrieval unit (a paragraph or short section), not a 200-page PDF | `HB-VAC-C2` is one chunk |
| **Index** | The searchable structure over chunks (keyword overlap here; embeddings in production) | Only chunks with `index_ok: true` |
| **Metadata** | Labels on a chunk that are not the paragraph itself | `clearance`, `id`, `citation` |
| **Canary** | Planted sensitive text. If a reply quotes it, the exercise **fails** | National ID `999-00-1111`, name Maya Reid |
| **PII** | Information that identifies a person | CVs, burgess forms, health records, live tickets |

**INDEX** means: this text may be stored in the classroom search pile. **NEVER** means: do not copy it in, even “just to try.”

This is **N5** (data ban) and the start of **N4** (access). T1-10 is the access gate. Today is “does it enter the pile at all?”

![May this enter the CivicDesk index?](images/t2_index_or_not.jpg)
"""
        ),
        md(
            """## Ministry link

| Your EOI type | What must never enter an index in *this* room |
|---|---|
| **Labour** | Real CVs, scores, names |
| **Health / THA** | Patient detail, LMS submissions, suicide-guideline *cases* (the *rule* N1 may be indexed) |
| **Finance** | Cabinet *bodies*. Class metadata is a later access question |
| **RDLG** | Burgess applications, household names, addresses |
| **TTDF** | Patrol notes, landing sites, tracks (AUX-05) |
| **Trade / Defence assets** | Live GLPI/serial dumps — query the register; do not index this month’s extract |
| **all** | The canary line. If you index it, you fail the drill |

**N14 woven:** someone must be able to say later “this chunk was / was not in the index.” That is why every chunk has an id.
"""
        ),
        md(
            """## 1. Look at the handbook pile (including the canary)

`index_ok` is a flag on the chunk. `clearance` is who may *see* it later. A restricted chunk can still be in the index (T1-10). A prohibited canary must not be.
"""
        ),
        code(
            """# [RUN]
import civicdesk_rag as rag

print("All chunks in data/handbooks.json\\n")
rag.print_chunks(include_prohibited=True)
print()
print("Indexed only (index_ok True):", len(rag.indexed_chunks()), "of", len(rag.load_chunks()))
"""
        ),
        md(
            """### Teaching note

`HB-CANARY` has `index_ok: false` and `clearance: prohibited`. The helper `retrieve()` skips it unless you pass `include_prohibited=True` (a drill, not a product feature).

`HB-CAB-X` is **restricted** but `index_ok: true`. That is deliberate. The index may know a classed minute exists. Displaying the body is T1-10. Finance-shaped: even that is generous — many rooms would keep Cabinet bodies **out** of the index entirely (see CI-05).
"""
        ),
        md(
            """## 2. Classification sheet

Read CI-01…CI-10. Decide INDEX or NEVER **before** you open the next cell if you can.
"""
        ),
        code(
            """# [RUN]
import civicdesk_rag as rag

rag.print_classify_sheet()
"""
        ),
        md(
            """## 3. Score your labels

Allowed values: `index` or `never`. The cell ships the teaching key so Run All works. Cover it and try first if you want a real score.
"""
        ),
        code(
            """# [CHANGE] replace with your labels to test yourself.
GUESSES = {
    "CI-01": "index",
    "CI-02": "never",
    "CI-03": "index",
    "CI-04": "never",
    "CI-05": "never",
    "CI-06": "index",
    "CI-07": "never",
    "CI-08": "index",
    "CI-09": "never",
    "CI-10": "never",
}

import civicdesk_rag as rag

rag.score_classification(GUESSES)
rag.save_log("T1-07_classify", {"guesses": GUESSES})
"""
        ),
        md(
            """### After you run

A published **rule** can be indexed. A **person’s file** cannot. A **live extract** of a register cannot — you would be copying operational data into a search pile that the model might quote.

**Write-up:** name one thing from *your* overnight canvas that would be NEVER, in CivicDesk words (no real identifiers).
"""
        ),
        code(
            """# [OPTIONAL] what retrieve() would do if someone left the canary searchable
import civicdesk_rag as rag

print("Normal retrieve (canary excluded):")
for h in rag.retrieve("Maya Reid national ID", k=5):
    print(" ", h["id"], "score", h["score"])
print()
print("Unsafe retrieve (include_prohibited=True) — classroom drill only:")
for h in rag.retrieve("Maya Reid national ID", k=5, include_prohibited=True):
    print(" ", h["id"], "score", h["score"], "index_ok", h.get("index_ok"))
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-08
# ---------------------------------------------------------------------------
write(
    "T1-08_build_rag.ipynb",
    [
        md(
            """# T1-08 Build RAG

**Time:** 10:45–12:00 &nbsp;|&nbsp; **Evidence:** a cited reply for Q-ATTACH and Q-C2 in `logs/`

**Notebook learning outcomes**

- Draw **retrieve, then generate** (RAG) as a pipeline, not a magic box.
- Run a classroom retriever (word overlap) and say how it stands in for embeddings.
- Produce a reply that **quotes a span** or **abstains**.

"""
            + BANNER
        ),
        md(
            """## Overnight readers — RAG in one page

**RAG** = Retrieval-Augmented Generation. Two steps, in order:

1. **Retrieve** — search an *approved* pile for chunks that match the question.
2. **Generate** — put those chunks into the prompt, then ask the model to answer **only** from that text (cite) or stop (abstain).

Day 1 generation had **no** handbook in the messages. The model continued text from weights. That is why it could invent Circular 99.

| Piece | What it is | What it is not |
|---|---|---|
| **Query** | The clerk’s question | A SQL statement (unless you chose **integration**) |
| **Retriever** | Scores chunks against the query | The generator |
| **k / top-k** | How many chunks you keep | “The whole EDMS” |
| **Score** | Overlap count here; cosine similarity if you use embeddings later | Proof the chunk is *allowed* |
| **Citation** | Handbook id + quoted span | A URL the model imagined |
| **Abstain** | “I cannot cite. Stop.” | A guessed circular |

**Embeddings (extra):** production RAG often turns chunks and the query into vectors and finds nearest neighbours. You are **not** training embeddings today. `civicdesk_rag.retrieve` counts shared words after dropping tiny stopwords. Same *job*: rank chunks. Different *engine*. If overlap feels crude, that is the point — you can see why it hit.

**Context window (from T1-02):** you retrieve *chunks* because a 400-page minute pack will not fit, and should not.

![RAG = retrieve, then generate](images/t2_rag_pipeline.jpg)
"""
        ),
        md(
            """## Ministry link

The twelve chunks stand in for OPR notes, EDMS-style rules, circulars, ECMS, a KB article, minutes procedure — **fiction**.

| Question | Stands in for |
|---|---|
| Q-ATTACH overnight store | Finance / MOWI / RDLG |
| Q-C2 library-studies diploma | Labour / Health (quote C2, do not hire) |
| Q-PWD reset my password | Trade IMSD (KB says the assistant must not reset) |
| Q-MISSING Circular 88 drones | Abstain drill for everyone |
| Q-CAB coastal-security minute | Finance access (T1-10) |

This lab is **N3** with **N1** and **N8** (quote, do not write a long unsourced summary).
"""
        ),
        md(
            """## 1. The questions
"""
        ),
        code(
            """# [RUN]
import civicdesk_rag as rag

rag.print_questions()
"""
        ),
        md(
            """## 2. Retrieve only — no generation yet

Watch ids and scores. A score is **shared tokens**, not permission.
"""
        ),
        code(
            """# [CHANGE] try Q-C2 or Q-PWD after you run Q-ATTACH.
QUESTION_ID = "Q-ATTACH"

import json
import civicdesk_rag as rag

q = {x["id"]: x for x in rag.load_questions()}[QUESTION_ID]
print("USER:", q["user"])
print("expect_chunk:", q["expect_chunk"])
print()
hits = rag.retrieve(q["user"], k=3)
print("top-k hits")
print(json.dumps([{"id": h["id"], "score": h["score"], "overlap": h["overlap"]} for h in hits], indent=2))
print()
if hits:
    print("Top chunk text:")
    print(hits[0]["text"])
"""
        ),
        md(
            """### Teaching note

If `HB-ATTACH-04` is on top for Q-ATTACH, the overlap retriever did its job. If a different internal chunk wins, read `overlap` — that is debugging, not a ministry failure.

**k=3** means you only *look* at three. Raising k can pull in extra noise (and extra access questions). Lowering k can miss the paragraph. There is no sacred k.
"""
        ),
        md(
            """## 3. Generate with the retrieved text

`answer_with_rag` applies a small access gate (role `clerk` by default) and then **cites or abstains**. It does not call OLMo. The wording is a classroom stand-in so this notebook runs with no GPU — same contract as `BACKEND='demo'` on Day 1. The skill is the pipeline, not a new model.
"""
        ),
        code(
            """# [RUN]
import json
import civicdesk_rag as rag

for qid in ("Q-ATTACH", "Q-C2", "Q-PWD"):
    q = {x["id"]: x for x in rag.load_questions()}[qid]
    out = rag.answer_with_rag(q["user"], role="clerk")
    print("=" * 60)
    print(qid, "→", out["mode"], "visible", out["visible_ids"])
    print(out["reply"])
    print()
    rag.save_log(f"T1-08_{qid}", out)
"""
        ),
        md(
            """### After you run

You should see **cite** for ATTACH and C2, with a quoted span. Q-PWD should still **cite the KB** that forbids a reset — citing is not doing. The assistant must not claim the account changed.

**Write-up:** copy one quoted span. Circle the citation id. If you cannot point at a span, you do not have RAG; you have a chatbot.
"""
        ),
        code(
            """# [OPTIONAL] deep-code: implement overlap yourself and compare to the helper
import civicdesk_rag as rag

q = "overnight attachments file store"
mine = rag.retrieve(q, k=5)
print("query tokens:", sorted(rag._tok(q)))
for h in mine:
    print(h["id"], h["score"], h["overlap"])
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-09
# ---------------------------------------------------------------------------
write(
    "T1-09_prompt_vs_rag.ipynb",
    [
        md(
            """# T1-09 Prompt vs RAG

**Time:** 12:45–13:45 &nbsp;|&nbsp; **Evidence:** side-by-side log — invented circular vs cited paragraph vs abstain

**Notebook learning outcomes**

- Show the **same question** answered from weights only vs from a retrieved chunk.
- Name **hallucination** when a circular number appears with no source.
- **Abstain** when the corpus has no paragraph (Q-MISSING).

"""
            + BANNER
        ),
        md(
            """## Overnight readers

**Prompt-only** here means: the generator never sees a handbook chunk. It continues from the standing instruction plus the user text. That is Day 1.

**RAG** means: retrieve first, then generate from visible chunks.

The failure mode ministries actually fear is not a blank. It is a **fluent wrong**: “CivicDesk Circular 99 of 2024 appears to allow…” — invented, confident, unusable in Finance or Defence.

![Same question, two paths](images/t2_prompt_vs_rag.jpg)

**Extra words:**

- **Grounded** — every factual clause points at a chunk id.
- **Ungrounded / hallucinated** — the clause cannot be found in the prompt or the retrieved set.
- **Abstain** — the honest third output. Not a shrug: a logged stop.
"""
        ),
        md(
            """## Ministry link

Finance / Defence / Health cannot accept an invented circular, OPR note, or guideline number. Labour cannot accept an invented C2. Trade cannot accept “your password has been reset” because the model sounded sure.

This lab is **N3**. The abstain on Q-MISSING is the skill to take home.
"""
        ),
        md(
            """## 1. Same question, two replies
"""
        ),
        code(
            """# [RUN]
import civicdesk_rag as rag

q = {x["id"]: x for x in rag.load_questions()}["Q-ATTACH"]
print("USER:", q["user"])
print()
print("--- prompt-only (no retrieval) ---")
print(rag.answer_prompt_only(q["user"]))
print()
print("--- RAG ---")
out = rag.answer_with_rag(q["user"], role="clerk")
print(out["reply"])
print("mode:", out["mode"], "chunks:", out["visible_ids"])
rag.save_log("T1-09_attach", {"prompt_only": rag.answer_prompt_only(q["user"]), "rag": out})
"""
        ),
        md(
            """### Teaching note

Mark the prompt-only reply: it **fails** even if it reads like a circular. Fluency is not evidence.

The RAG reply must show `HB-ATTACH-04` (or another approved chunk that actually answers). If your overlap retriever missed, that is a retrieval bug — still better than a fake circular, because you can see the empty hit list.
"""
        ),
        md(
            """## 2. Missing source — abstain drill

Q-MISSING asks for CivicDesk Circular 88 of 2019 on drone permits. That document is **not** in the pile. The correct product behaviour is stop.
"""
        ),
        code(
            """# [RUN]
import civicdesk_rag as rag

q = {x["id"]: x for x in rag.load_questions()}["Q-MISSING"]
print("USER:", q["user"])
print("expect_chunk:", q["expect_chunk"])
print()
print("hits:", [(h["id"], h["score"]) for h in rag.retrieve(q["user"], k=3)])
out = rag.answer_with_rag(q["user"], role="clerk")
print()
print(out["reply"])
print("mode:", out["mode"])
rag.save_log("T1-09_missing", out)
"""
        ),
        md(
            """### After you run

`mode` should be **abstain**. Hits may be empty or weakly related. Weak overlap is not permission to invent Circular 88.

**Write-up:** one sentence you would put in a service-desk script: *If the chunk is not in the retrieved set, we will not…*
"""
        ),
        code(
            """# [CHANGE] occasional-code: swap the question id.
QUESTION_ID = "Q-C2"  # try Q-PWD

import civicdesk_rag as rag

q = {x["id"]: x for x in rag.load_questions()}[QUESTION_ID]
print("prompt-only:")
print(rag.answer_prompt_only(q["user"]))
print()
print("RAG:")
print(rag.answer_with_rag(q["user"])["reply"])
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-10
# ---------------------------------------------------------------------------
write(
    "T1-10_access_and_governance.ipynb",
    [
        md(
            """# T1-10 Access and governance (group)

**Time:** 13:45–14:20 &nbsp;|&nbsp; **Evidence:** clerk vs records-officer on Q-CAB

**Notebook learning outcomes**

- Separate **a hit in the index** from **permission to display**.
- Run the same question as a **clerk** and as a **records-officer**.
- Say who would audit that decision (N14 woven).

**This block is (group).**

"""
            + BANNER
        ),
        md(
            """## Overnight readers — N4 in one picture

Day 1 named access as a hosting question. Today it is a **retrieval** question.

The index is a search engine. Search engines are greedy. They will surface `HB-CAB-X` for “coastal-security minute” because the words match. That does **not** mean a front-desk clerk may read the paragraph.

| Idea | Meaning |
|---|---|
| **Retrieval** | The chunk scored high |
| **Access / authorisation** | This **role** may see this **clearance** |
| **Class metadata** | Telling someone “a Cabinet-class item exists” without the body |
| **Audit** | Log: query, chunk ids, role, shown or blocked |

![Access is not retrieval](images/t2_access_not_retrieval.jpg)

**Extra:** this is the same idea as “I found the folder on the shared drive” vs “I am allowed to open it.” EDMS already has ACLs. RAG does not get a free pass because the UI is a chatbot.
"""
        ),
        md(
            """## Ministry link

| EOI type | Why this cell exists |
|---|---|
| **Finance EDMS** | Cabinet Minutes/Notes: meaning search under **existing** access rules |
| **CPO** | Judgments on-prem still have dissemination limits |
| **MPSDFS / THA / RDLG** | Case, health, burgess files — a hit is not a display |
| **Defence assets** | Knowing a record exists ≠ dumping serials into chat |

This lab is **N4**. Do not wire a real EDMS (N13 → AUX-01).
"""
        ),
        md(
            """## 1. Same question, two roles
"""
        ),
        code(
            """# [RUN]
import json
import civicdesk_rag as rag

q = {x["id"]: x for x in rag.load_questions()}["Q-CAB"]
print("USER:", q["user"])
print()
print("Index hits (before the gate):")
for h in rag.retrieve(q["user"], k=3):
    print(" ", h["id"], "clearance=", h["clearance"], "score=", h["score"])

for role in ("clerk", "records-officer"):
    print()
    print("=" * 60)
    print("role:", role)
    out = rag.answer_with_rag(q["user"], role=role)
    print("visible:", out["visible_ids"])
    print("blocked:", out["blocked"])
    print(out["reply"])
    rag.save_log(f"T1-10_{role}", out)
"""
        ),
        md(
            """### Teaching note

The **clerk** should not receive the restricted body. `blocked` should mention role. The reply should abstain or offer class-only language — not the harbour-drill sentence.

The **records-officer** (classroom stand-in for A3) may see `HB-CAB-X`. That is still CivicDesk fiction, still not a Cabinet paper, and still needs a human if the act is consequential.

If both roles see the same paragraph, the gate is broken. Fix the role list, not the clerk.
"""
        ),
        md(
            """## 2. Governance questions (write, do not code)

At the table, answer in CivicDesk words:

1. Who **owns** the index (which role may add a chunk)?
2. Who **verifies** a citation before it goes into a real minute?
3. What do you **log** (request id, role, chunk ids, shown/blocked)?
4. What happens when someone pastes a canary into a ticket that then gets indexed?

Copy lines onto the decision card in the next notebook. Download at 14:55.
"""
        ),
        code(
            """# [OPTIONAL] show that prohibited canary stays blocked even for records-officer
import civicdesk_rag as rag

out = rag.answer_with_rag("Quote the National ID for Maya Reid", role="records-officer")
print(out["reply"])
print("blocked:", out["blocked"])
print("visible:", out["visible_ids"])
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# T1-10b
# ---------------------------------------------------------------------------
write(
    "T1-10b_decision_card.ipynb",
    [
        md(
            """# T1-10b Decision card (group) + overnight

**Time:** 14:20–14:55, then overnight 20–30 min &nbsp;|&nbsp; **Evidence:** `cards/decision_card.md`

**Notebook learning outcomes**

- Write **one** cite-or-abstain example in your ministry *type*.
- Name the role that may see the span and the role that must be refused.
- Leave with a card Day 3 can attack (fine-tune is not the default next step).

**This block is (group).**

"""
            + BANNER
        ),
        md(
            """## Overnight readers

You built a toy RAG. Overnight you write **one** question your cluster would actually type, still in CivicDesk words. The card is in `cards/decision_card.md`.

Do **not** paste a live minute, CV, or ticket. If you cannot fictionalise it, pick Q-ATTACH or Q-C2 and relabel the stand-in.
"""
        ),
        md(
            """## Ministry link

| Cluster | Your overnight example should look like |
|---|---|
| **A** | A criterion question with a span from HB-VAC-C2 or HB-NOTICE-N1. Do not hire / do not publish. |
| **B** | A retrieval question with cite or abstain. Include an access line (N4). |
| **C** | A desk question. Password: cite KB, do not reset. Assets: no table → stop. |
| **D** | Where would this index live? What never goes in? Agentic “no” waits for T1-13. |
"""
        ),
        code(
            """# [CHANGE] fill as a group. Fictional CivicDesk names only.
card = {
    "organisation": "CivicDesk Records Office (Finance-shaped)",
    "cluster": "B",
    "clerk_question": "What is the rule for storing service-request attachments overnight?",
    "approved_source": "HB-ATTACH-04",
    "quoted_span_or_abstain": "stored overnight only on the CivicDesk approved file store",
    "role_that_may_see": "clerk (internal clearance)",
    "role_that_must_be_refused": "public chatbot user; also clerk for HB-CAB-X",
    "stop_condition": "If the store is unavailable, stop. Do not invent a workaround circular.",
    "never_enter_index": "Cabinet bodies, CVs, burgess PII, canaries, live serial dumps",
    "will_not_do": "hire / publish / award / reset a password",
}
for k, v in card.items():
    print(f"{k}: {v}")

import civicdesk_rag as rag
rag.save_log("T1-10b_card", card)
"""
        ),
        md(
            """### Teaching note

A card without a **quoted span** is a wish. A card without a **refused role** has not done N4. A card that says “fine-tune the circulars” has not done today.

Copy the dict into `cards/decision_card.md` before you leave. Day 3 will ask whether an adapter would help. Often the answer is no.

**Overnight:** 20–30 minutes. No GPU. No ministry files. Arrive able to say cite-or-abstain out loud.
"""
        ),
    ],
)

print("day 2 notebooks written")
