# Tier 1 content plan — by day

Maps `00_common_needs_from_eois.md` onto the notebooks in the final workplan. **Direct** = the notebook practises that need. **Woven** = a CivicDesk example or a “ministry link” callout, not a full lab. **Aux** = self-taught workshop; will not fit in 15 contact hours.

Days run 09:00–15:00. Instruction lives in the notebook. CivicDesk only.

## Coverage matrix

| Need | Day 1 | Day 2 | Day 3 | Aux (self-taught) |
|---|---|---|---|---|
| N1 Criteria + quote | Woven in T1-01 request and T1-05 canvas | Direct in T1-08/T1-09 (cite the paragraph) | Direct in T1-11 criteria-matching rows; T1-14 defence | — |
| N2 Human review / no decide | Direct in opening rules + T1-05 stop condition | Woven (abstain) | Direct T1-13 hire/grade/award stay human; T1-14 | — |
| N3 RAG + citations | Woven (“this answer has no source yet”) | **Direct** T1-08, T1-09 | Woven vs fine-tune | — |
| N4 Access ≠ retrieval | Named in T1-04 as a GPU/hosting *and* access question | **Direct** T1-10 | Woven | AUX-03 identity |
| N5 PII / ops data ban | **Direct** opening + every notebook banner | **Direct** T1-07 classification | Direct canaries in T1-11 | AUX-04 DPIA sketch |
| N6 Bounded agency | Woven in opening (no passwords in chat) | Woven | **Direct** T1-13 | AUX-01 tools/APIs |
| N7 Own the box if core | **Direct** T1-01 (start local/shared endpoint) + T1-04 GPU card | — | Burst vs standing briefing | — |
| N8 Summarise / extract | Woven (first reply is short) | Direct-ish T1-08 (quote, not a long summary) | Woven | AUX-02 when extraction is not generation |
| N9 Classify incoming text | Woven T1-01 CivicDesk request type | Direct T1-07 | — | — |
| N10 Structured register query | Named in T1-05 (“is the source of truth a database?”) | Woven | — | **AUX-02** |
| N11 Cost / GPU / burst vs standing | **Direct** T1-03 cost card; T1-04 GPU questions | Woven (RAG cheaper than LoRA) | Direct architecture card burst vs standing | — |
| N12 Open vs open-weight vs API | **Direct** T1-04 | — | Woven (licence inheritance of an adapter) | — |
| N13 Existing systems | Named only | Named (do not wire GLPI/EDMS) | Named | **AUX-01** |
| N14 Audit / override | Woven T1-05 (who verifies) | Woven T1-10 | Direct T1-14 transfer card | AUX-04 |
| N15 Tabular / GIS / ops patterns | Named as “maybe no LM” in T1-05 | — | — | **AUX-02**, **AUX-05** (TTDF custody) |

## Day 1 — Start a model and see how it works

**Goal (workplan):** every participant starts an approved SLM, can point at the architecture card (tokenizer → embedding → blocks → head), and can explain what happened between typed text and the reply.

| Time | Notebook | What they do | Needs | Ministry link (how it is pointed out in the notebook) |
|---|---|---|---|---|
| 09:00–09:15 | Opening | Safe-use rules, data ban, pre-test | N5, N2 | Banner: no CVs, Cabinet, case, health, burgess, patrol files |
| 09:15–09:50 | **T1-01a** Build from scratch | Check host; download OLMo+Phi weights; start vLLM/docker/hf or skip | N7 | CPO/TTDF/Finance: own the door. Script: `build_llms.py` |
| 09:50–10:30 | **T1-01** First CivicDesk call | `BACKEND` = demo/local/shared/custom; send one request; save log | N7, N9, N1 woven | Request is a **service ticket** (Trade) that also needs a **criteria quote** (Labour/Health). Reply must not hire, grade, or reset a password |
| 10:30–10:45 | Break | | | |
| 10:45–12:00 | **T1-02** Tokens and the transformer | Tokenize public-sector *fictional* sentences; architecture card; two decoding settings | N12 woven (the weights are this machine) | Sentences stand in for Finance minute-style prose, OPR-style rule, vacancy criterion, asset question — **fictional** |
| 12:00–12:45 | Lunch | | | |
| 12:45–13:45 | **T1-03** SLM vs LLM | Same prompt to OLMo and Phi-4 Mini; cost card | N11, N7 | Cost-per-acceptable-answer and “who pays” — CPO/TTDF/Finance arguing for owned inference |
| 13:45–14:20 | **T1-04** Openness, licences, GPU questions | Model cards; Apache vs MIT; OSAID vs open-weight; GPU question card | N12, N11, N7, N4 named | Closed API vs weights you can host — why Finance/CPO/TTDF care |
| 14:20–14:55 | **T1-05** Use-case canvas (group) | Frame the *type* of their EOI; owner, verifier, baseline, stop | N2, N5, N10 named, N15 named | Each cluster gets a prompt: criteria / retrieval / desk / local-control |
| 14:55–15:00 | Download | | | |
| Overnight | Finish canvas | 20–30 min, no GPU | | Arrive Day 2 able to label prompt / RAG / fine-tune / none |

Day 1 does **not** build RAG or fine-tune. It gives people the machine, the cost of the machine, and a canvas so Day 2 has somewhere to land.

## Day 2 — Retrieve local information before changing weights

**Goal:** retrieve from an approved set, cite it, refuse when the source is missing.

| Time | Notebook | Needs | Why this is the retrieval ministries’ day |
|---|---|---|---|
| 09:00–09:20 | T1-06 Intervention map (group) | N1–N3, N10, N15 | Force a label: many EOIs want “an LLM”; some need a database or no model |
| 09:20–10:30 | T1-07 Data classification | N5, N4, N14 | Finance/MPSDFS/THA/RDLG/TTDF: what must never enter an index |
| 10:45–12:00 | T1-08 Build RAG | **N3**, N1, N8 | 12 fictional handbooks stand in for OPR, EDMS-style notes, circulars, ECMS, KB, minutes |
| 12:45–13:45 | T1-09 Prompt vs RAG | N3 | Invented consensus vs a cited paragraph — Finance/Defence/Health |
| 13:45–14:20 | T1-10 Access and governance (group) | **N4** | Same chunk, wrong user |
| 14:20–14:55 | Decision card (group) | N3, N4, N14 | Overnight: one cite-or-abstain example in *their* ministry type |

## Day 3 — Fine-tuning literacy and operating questions

**Goal:** inspect a training set and a pre-built adapter. They do **not** train.

| Time | Notebook | Needs | Why |
|---|---|---|---|
| 09:00–09:15 | Architecture card: frozen vs updated; burst vs standing | N11, N7 | CPO “train on judgments” meets “LoRA is a burst, serving is standing” |
| 09:15–10:30 | T1-11 Dataset + what is frozen | N1, N5, N12 | Criteria-matching rows (Labour/Health); canaries (all PII papers) |
| 10:45–12:00 | T1-12 Base vs adapter | N1 | Adapter is not a database (Finance/RDLG still need RAG) |
| 12:45–13:30 | Risk cells | N5, N11 | Rollback, licence inheritance |
| 13:30–14:15 | T1-13 Agentic boundary | **N6**, N2 | Trade password/GLPI; CPO agentic research; Defence “must not award” |
| 14:15–14:55 | T1-14 Defence + EOI transfer card | N2, N14, all clusters | First safe next step, not a pilot |

## How Day 1 notebooks will mark ministry relevance

A short **Ministry link** box after the first working cell in each notebook, using this pattern:

> **Labour / Health:** this request is classified against a published rule and must quote a span. The model does not shortlist a person or publish a grade.  
> **Trade IMSD:** same shape as a Tier-1 ticket: interpret plain language, do not reset a password.  
> **Finance / Defence OPR / MPSDFS / MOWI / RDLG / THA:** notice there is *no* handbook retrieval yet — that is Day 2. Today you are only starting the model.  
> **CPO / TTDF:** the call is against a workspace you control (or the course shared endpoint), not a public chatbot.

## Auxiliary workshops (self-taught; not in the 15 hours)

Written so a participant can do them after Day 3, without a GPU. They absorb N10, N13, N15 and the integration work the contact hours cannot take. Files live in `course/auxiliary/` (`aux` is a reserved Windows name).

| ID | Title | Absorbs | Est. |
|---|---|---|---|
| AUX-01 | Sitting beside a system you already have | N13, N6 | 45–60 min |
| AUX-02 | When a language model is the wrong tool | N10, N15, N8 | 40 min |
| AUX-03 | Identity is not a chat message | N4, Trade WhatsApp/AD | 30 min |
| AUX-04 | A one-page DPIA sketch | N5, N14 | 40 min |
| AUX-05 | Operational data and why TTDF-shaped work stays out | N5, N15, N7 | 25 min |

## Built in this pass (for review)

- This plan and the common-needs file.
- The five auxiliary workshops (markdown, self-taught).
- **Tier 1 Day 1** notebooks and cards only. Days 2–3 are not built until Day 1 is reviewed.
