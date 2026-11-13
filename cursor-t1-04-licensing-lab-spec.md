# Cursor spec: turn T1-04 into a licence-reading lab

Repo: https://github.com/justkrismanohar/fine-tuning-build, read at commit `main` as of 12 November 2026 (no local changes were made or pushed).
Target: `tier1/day1/T1-04_openness_licences_gpu.ipynb`.
Slot: 13:45 to 14:20 (35 minutes), unchanged.

This spec is for Cursor. It says which files to add, which notebook cells to replace and in what order, the exact teaching text, the worksheet, the instructor answer key and the checks to report on. Every licence quotation below was copied from the local licence files that ship with this spec (folder `t1-04-licence-files/`) and re-checked against them.

The lab teaches people to **read** licences. It is not legal clearance. The notebook says this once, in plain words, and points real projects to counsel and procurement.

---

## 0. Ground rules for Cursor

1. **Edit the notebook directly.** Do not run `tier1/day1/build_day1_notebooks.py`. It writes every Day 1 notebook from strings in the script, and the current T1-04 cell 0 (the title cell) no longer matches the script, so running it would overwrite hand edits. Other Day 1 notebooks have also drifted from the script. Edit the `.ipynb` JSON with a short one-off Python script using `json` or `nbformat`, then delete that script. Do not commit it.
2. **Then bring the generator in line.** After the notebook is right, replace the T1-04 block in `build_day1_notebooks.py` (it starts at the `# T1-04` comment, around line 799, and ends with the `write("T1-04_openness_licences_gpu.ipynb", ...)` call) with the same cell sources, so a future run cannot undo this lab. Do not run the generator to test this. Instead compare: load the notebook, load the cell strings from the script, assert they are identical.
3. **Do not change any other notebook.** One exception: T1-01a and T1-02 promise that T1-04 covers training data "as a licence question". Leave those lines; this lab answers them in the teaching note.
4. **Copy the licence files byte for byte.** Do not retype, reflow, trim or "clean" any licence text. Do not add or remove trailing newlines. The checksums must still pass after the copy.
5. **No model calls in this notebook.** Nothing here asks OLMo or Phi what a licence means. The only code is file reading and answer-format checks.
6. **Do not commit `logs/*.json`.** They are already ignored by `.dockerignore`; keep them out of git as well.

---

## 1. Files to add

### 1.1 `tier1/day1/licences/` (copy the whole supplied folder)

Copy the supplied `t1-04-licence-files/` folder to `tier1/day1/licences/`. It contains:

| Path in `licences/` | What it is | Kind |
|---|---|---|
| `README.md` | Sources, pins, retrieval date and the differences found | Notes |
| `SHA256SUMS` | Checksums for every file | Checks |
| `apache-2.0/LICENSE-2.0.txt` | Apache License 2.0, full text, from apache.org | Verbatim |
| `olmo-2-0425-1b-instruct/MODEL_CARD_README.md` | OLMo 2 1B Instruct card at revision `48d788e` | Verbatim |
| `olmo-2-0425-1b-instruct/AI2_RESPONSIBLE_USE_GUIDELINES_2026-11-12.txt` | Ai2 Responsible Use Guidelines, "Last Updated: June, 2024" | Extracted from web page |
| `olmo-2-0425-1b-instruct/TULU3_SFT_MIXTURE_DATASET_CARD.md` | Parent Tülu 3 SFT data card (ODC-BY-1.0, some portions non-commercial) | Verbatim |
| `olmo-2-0425-1b-instruct/TULU3_SFT_OLMO2_MIXTURE_0225_DATASET_CARD.md` | OLMo-specific SFT data card (states no licence) | Verbatim |
| `llama-3.2/LICENSE` | Llama 3.2 Community License Agreement, release date September 25, 2024 | Verbatim, GitHub `meta-llama/llama-models` commit `8d29d93` |
| `llama-3.2/LICENSE_llama.com_current_2026-11-12.txt` | Same licence from llama.com, for the cross-check | Extracted |
| `llama-3.2/USE_POLICY_llama.com_current_2026-11-12.txt` | Llama 3.2 Acceptable Use Policy, current web version (the one the licence incorporates by URL) | Extracted |
| `llama-3.2/USE_POLICY_github_2024-09-25.md` | The AUP as first published | Verbatim, historical |
| `llama-3.2/MODEL_CARD.md`, `MODEL_CARD_VISION.md` | Llama 3.2 text and vision model cards | Verbatim |
| `meta-llama-3/LICENSE`, `USE_POLICY.md` | Meta Llama 3 licence (release date April 18, 2024) and AUP | Verbatim |
| `phi-4-mini-instruct/LICENSE`, `NOTICE.md`, `MODEL_CARD_README.md` | Phi-4-mini-instruct at revision `cfbefac` | Verbatim |
| `osaid-1.0/OSAID_1.0_text_2026-11-12.txt` | OSI Open Source AI Definition 1.0 | Extracted |
| `source-snapshots/*.html` | Raw HTML of every web page used | Record copies |

`source-snapshots/` is about 1.2 MB. Keep it in the repo as the record. If image size matters, it can be excluded from the Docker image (add `tier1/day1/licences/source-snapshots` to `.dockerignore`) but then remove its lines from the copy of `SHA256SUMS` used in the image, or `verify()` will report missing files. Simplest: keep it in both.

The Llama 3.2 Hugging Face repo is gated, so its own copies could not be checked. If the instructor has accepted the gate, compare `LICENSE.txt` and `USE_POLICY.md` at revision `9213176726f574b556790deb65791e0c5aa438b6` with these before class and note the result in `licences/README.md`.

### 1.2 `tier1/day1/licence_lab.py` (new helper)

A reference implementation ships with this spec as `licence_lab.py`. Copy it to `tier1/day1/licence_lab.py`. It was tested against the licence folder: `verify()` passes on all files, and every `find()` call used in the notebook returns the clause listed in the answer key. What it does:

- `verify()`: checks every file against `SHA256SUMS` and says how many match. If any are missing or changed it lists them and says not to teach from them.
- `files()`: lists short names such as `llama32_licence`, `llama32_aup`, `apache`, `olmo_card`, `ai2_guidelines`.
- `find(name, phrase)`: prints each clause (numbered or lettered item, or paragraph) containing the phrase, case-insensitive. When nothing matches it prints "NOT FOUND in this file. That is an answer too: say which file you would need next."
- `show(name, start, end)`: prints a run of clauses from one heading to the next.
- `check_format(answers)`: checks only the **form** of worksheet answers: each starts with `FOUND:`, `NOT FOUND` or `NEED LINKED TERMS:`, and each `FOUND:` names a section or AUP item. It never judges whether an answer is legally right.
- `check_classes(table)`: checks each scenario label is one of `permitted`, `permitted with obligations`, `permission required`, `prohibited`, `unclear - escalate`, and that a clause is named (or `none found`).
- `t1_03_winner()`: reads `logs/T1-03_scorecard.json` if the learner saved one and returns which model had the higher 0 to 2 quality score, or says there is no scorecard. It uses the keys T1-03 really writes: `scores.olmo_quality_0to2`, `scores.phi_quality_0to2`, `olmo.model`, `phi.model`.

It imports nothing outside the standard library and makes no network calls.

### 1.3 `tier1/day1/data/model_card_excerpts.md` (edit)

Replace the OLMo, Phi and "Families" sections with the text below. Keep the title, the first paragraph and the "Closed products" section as they are.

```markdown
## allenai/OLMo-2-0425-1B-Instruct (primary)

- **Revision used in this course:** 48d788eca847d4d7548f375ad03d3c9312f6139e.
- **Licence as stated on the card:** "OLMo 2 is licensed under the Apache 2.0 license." The model repo has no separate LICENSE or NOTICE file, so `licences/apache-2.0/LICENSE-2.0.txt` is the text.
- **Also on the card:** "OLMo 2 is intended for research and educational use. For more information, please see our Responsible Use Guidelines." Those guidelines are a separate document (`licences/olmo-2-0425-1b-instruct/`).
- **What Ai2 publishes:** weights, code, training data mixtures and recipes. That lets you audit what went in. It does not let you explain why the model wrote one particular sentence.
- **Openness:** an open-weight model under an OSI-approved licence, with training data published. Whether the whole system meets the OSI Open Source AI Definition is a separate check (data information, code and parameters, each under OSI-approved terms), not something the word "Apache" settles.
- **Use in class:** default chat model on vLLM.

## microsoft/Phi-4-mini-instruct (comparison)

- **Revision used in this course:** cfbefacb99257ffa30c83adab238a50856ac3083.
- **Licence:** MIT (LICENSE file in the repo). NOTICE.md lists a third-party component (flash-attention, BSD 3-Clause). The card's Trademarks section limits use of Microsoft marks.
- **Openness:** open-weight under a permissive licence. Training data is described in the card, not published as a dataset you can download.
- **Use in class:** comparison only. Same prompt, same CivicDesk text.

## meta-llama/Llama-3.2-1B-Instruct (licence comparison only, not run in class)

- **Revision checked:** 9213176726f574b556790deb65791e0c5aa438b6 (gated on Hugging Face: you accept Meta's terms before download).
- **Licence:** Llama 3.2 Community License Agreement plus the Llama 3.2 Acceptable Use Policy, which the licence incorporates by reference. Not an OSI-approved licence.
- **Text only:** the model card describes the 1B and 3B models as "text in/text out".
- **Use in class:** the licence you read in the scavenger hunt.

## Families you will hear about (not extra labs)

Mistral, Gemma, Llama, Qwen each publish several models, and the licence can differ by model and by version inside one family. Always read the licence for the exact model and revision. Ollama and vLLM are runtimes, not models: they have their own software licences and do not change the model's licence.
```

### 1.4 `tier1/day1/cards/gpu_questions.md` (no change)

Keep it exactly as it is. The lab keeps the GPU card and budgets four minutes for it (section 3).

### 1.5 `tier1/day1/completed/T1-04_openness_licences_gpu.ipynb` (new)

The completed copy of the notebook, with all cells run and the answer cells filled in from the answer key in section 5. Learners can load it when stuck, as the notebook's opening cell already promises. The folder exists and is empty for Day 1.

---

## 2. What the learner should leave with

1. A licence controls a short list of things: who may use the model, for what, whether you may change it, whether and how you may pass it on, what you must say when you do, what limits apply (scale, purpose, place), and what the publisher does not promise.
2. "I can download it" does not mean "I can do anything with it". Open weights are not the same as open source.
3. Some terms live outside the licence file (an acceptable-use policy, a developer's guidelines, a data card). "Need the linked terms" is a correct answer.
4. Four outcomes, not two: **prohibited**, **permitted with obligations**, **permission required**, **unclear: escalate**. Plain **permitted** exists too, when no condition is triggered.
5. The licence is not the privacy check. Data-protection law and Ministry rules apply whatever the licence says.
6. The model that won T1-03 still has to pass two more gates: may we use it this way (licence), and can we run it (GPU card).

---

## 3. Timing inside the 35 minutes

| Clock | Minutes | Cells | Activity |
|---|---|---|---|
| 13:45 | 3 | 0 to 2 | Title, Ministry link, T1-03 winner bridge, file check |
| 13:48 | 6 | 3 to 4 | Teaching: what a licence governs; open weight vs open source |
| 13:54 | 9 | 5 to 7 | Scavenger hunt in the Llama 3.2 licence and AUP |
| 14:03 | 9 | 8 to 11 | Walkthrough: Apache 2.0 vs Llama 3.2 on one scenario, then pairs label four scenarios |
| 14:12 | 4 | 12 to 13 | GPU question card: questions 1, 2 and 6 in the room, 3 to 5 after class |
| 14:16 | 4 | 14 to 15 | Escalation card and write-up |

**If the room runs late:** at 14:08, stop pairs after S1 and S3 and read S2 and S5 from the answer key. Do not cut the GPU card; move its questions 3 to 5 to the evening.

The deeper track (section 7) is a separate optional notebook. It takes no time from the room.

---

## 4. Notebook cells, in order

The current notebook has 8 cells (0 to 7). The new one has 17 (0 to 16). Mapping:

| Old cell | What happens to it |
|---|---|
| 0 Title | Replaced by new cell 0 (keeps "How to use this notebook" text word for word) |
| 1 Ministry link | Replaced by new cell 1 (first table row changed; "overnight readers" rewritten) |
| 2 Print model card excerpts | Kept as new cell 3, unchanged code |
| 3 Teaching note | Replaced by new cell 4 |
| 4 `licence_notes` True/False | Removed. Its two useful asserts (ChatGPT gives no weights; a community licence is not OSI) become hunt questions and scenario answers. The log name `T1-04_licences` is reused by the new hunt cell, so nothing downstream breaks. Nothing else in the repo reads that log. |
| 5 GPU question card | Kept as new cell 13, with a time budget line added |
| 6 `gpu_note()` | Kept as new cell 14, unchanged |
| 7 Write-up | Replaced by new cell 16 |

Cell tags used by the course: `# [RUN]`, `# [CHANGE]`, `# [OPTIONAL]` as the first line of code cells. Keep them.

### Cell 0 (markdown): title

```markdown
# T1-04 Openness, licences and GPU questions

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
```

### Cell 1 (markdown): Ministry link

```markdown
## Ministry link

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
```

### Cell 2 (code): bridge from T1-03 and file check

```python
# [RUN]
import licence_lab as L

ok = L.verify()   # every licence file matches the checksum recorded when it was downloaded

w = L.t1_03_winner()
if w["winner"] is None:
    print("No T1-03 scorecard on this machine. Pick the model you would build on and carry on.")
else:
    print(f"T1-03 winner on quality: {w['winner']}  (OLMo {w['olmo_score']}/2, Phi {w['phi_score']}/2)")

print("""
Three gates before a build:
  1. Quality   - T1-03: does it do the job on CivicDesk text?
  2. Permission - today: may we use it this way, and what must we do?
  3. Hardware  - today: can we run it, for how many users, at what cost?
A model that wins gate 1 can still fail gate 2 or 3.
""")
```

### Cell 3 (code): model card excerpts (old cell 2, unchanged)

```python
# [RUN]
from pathlib import Path
print(Path("data/model_card_excerpts.md").read_text(encoding="utf-8"))
```

### Cell 4 (markdown): teaching note, what a licence governs

```markdown
### Teaching note: what a model licence controls

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
```

### Cell 5 (markdown): scavenger hunt instructions

```markdown
## Scavenger hunt: the Llama 3.2 licence (9 minutes)

You are reading `licences/llama-3.2/LICENSE`, the Llama 3.2 Community License Agreement (release date September 25, 2024), and the use policy it links to. Work in pairs.

For each question, write one of:

- `FOUND: §<section> — "<a few words quoted>"`
- `NOT FOUND` — the licence does not say. That is a correct answer when it is true.
- `NEED LINKED TERMS: <which document>` — the licence points somewhere else for the answer.

Use `L.find("llama32_licence", "word")` to search, or open the file in the Jupyter file browser. The second file is `L.find("llama32_aup", "word")`. Do not ask a chatbot; it is not the licence.

Suggested search words are in brackets. Questions 9 and 10 are for pairs who finish early.
```

### Cell 6 (code): search examples

```python
# [RUN]
L.files()
print()
L.find("llama32_licence", "royalty-free")
L.find("llama32_licence", "training data")   # shows what NOT FOUND looks like
```

### Cell 7 (code): hunt answers

```python
# [CHANGE] answer each line. Start with FOUND:, NOT FOUND or NEED LINKED TERMS:
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
```

### Cell 8 (markdown): walkthrough, Apache 2.0 vs Llama 3.2

```markdown
## Walkthrough: same job, two licences (instructor-led, 4 minutes)

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
```

### Cell 9 (code): print the walkthrough clauses

```python
# [RUN]
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
```

Instructor script for S4 (put this in the completed notebook's markdown under cell 9, and in the answer key):

> Llama first. Section 1.b.iv says your use must "adhere to the Acceptable Use Policy", which "is hereby incorporated by reference into this Agreement". So the policy is part of the licence. The policy's item 2 bans using Llama 3.2 to "assist in the planning or development of activities that present a risk of death or bodily harm", "including" item 2.a, "Military, warfare". Planning military operations sits squarely there. Label: **prohibited**. Under section 6, Meta "may terminate this Agreement if you are in breach".
>
> Now Apache. Section 2 grants the right to "reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute" with no list of purposes and no banned uses. Nothing in Apache stops this job. But read the card: it points to Ai2's guidelines, which say they "govern your use". Search them for military: not found. They also say the list is "illustrative and not exhaustive" and Ai2 "reserves the right to terminate access for harms that are not listed". So: under the licence, **permitted**; on the linked guidelines, **unclear - escalate**. Whether those guidelines bind on top of Apache is a question for counsel, and that is exactly the kind of question you write down rather than guess.
>
> The point: one text has a term that reaches this job and one does not. And notice what we did not claim. A defence force drafting leave letters is not obviously "planning activities that present a risk of death or bodily harm". If that came up, it is unclear, and you escalate; you do not declare it banned.

### Cell 10 (markdown): pairs, four scenarios

```markdown
## Your turn: label four scenarios (5 minutes)

All facts are made up so the clauses can be tested. For each scenario give a label for **each** licence, and the clause you relied on (or `none found`).

**S1. Internal pilot.** A Ministry runs the model on its own server. Staff paste internal policy memos and get summaries. A named officer checks every summary before it is used. No files leave the Ministry.

**S2. Public chatbot.** The Ministry hosts the model on its own server behind a public web page that answers questions about services. Citizens type questions. The weights never leave the server.

**S3. Publishing an adapter.** The Ministry fine-tunes the model for résumé redaction and publishes the result on Hugging Face as **“CivicDesk-Redact-1B”** so other Caribbean governments can download it.

**S5. A very large partner.** The Ministry partners with GlobalChat Inc. GlobalChat and its affiliates had 750 million monthly active users across their products in August 2024. GlobalChat will itself fine-tune and run the model for the Ministry's service.

Useful searches: `L.find("apache", "Redistribution")`, `L.find("llama32_licence", "Built with Llama")`, `L.find("llama32_licence", "700 million")`, `L.find("llama32_aup", "disclose")`.
```

### Cell 11 (code): scenario labels

```python
# [CHANGE] label: permitted / permitted with obligations / permission required / prohibited / unclear - escalate
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
```

### Cell 12 (markdown): escalation card

```markdown
## When it goes to counsel or procurement

Send one short note per model, not a verdict:

1. Exact model name and revision (from the card), and where the licence came from, with the date you read it.
2. The job, in two lines: who uses it, on what data, hosted or shipped, shared with whom.
3. The clauses you think apply, by number, and the label you would give.
4. The open questions, word for word (for example: “Do the Ai2 guidelines bind us on top of Apache 2.0?”, “Is our internal tool ‘made available’ under Llama 3.2 §1.b.i?”).
5. The separate privacy question: what personal data goes in, and which law and Ministry policy cover it.

Recheck the linked documents on the day you decide. Use policies can change after a model is released: the Llama 3.2 policy you read today has different wording from the version published in September 2024 (both are in `licences/llama-3.2/`).
```

### Cell 13 (markdown): GPU question card (old cell 5, plus the time line)

Keep the old cell 5 text word for word, and add this line directly under the heading:

```markdown
**4 minutes in the room:** answer questions 1, 2 and 6 for this machine. Questions 3 to 5 go home with you tonight.
```

### Cell 14 (code): GPU note (old cell 6, unchanged)

```python
# [OPTIONAL]
import civicdesk_lab as lab
print(lab.gpu_note())
```

### Cell 15 (markdown): link to the deeper track

```markdown
`# [OPTIONAL]` After class: `tier1/deep/T1-04d_licences_deep.ipynb` compares Meta Llama 3 with Llama 3.2, shows how the use policy changed, looks at Phi's MIT licence and third-party notice, and reads the licences of OLMo's fine-tuning data. Nothing in it is needed for Day 2.
```

### Cell 16 (markdown): write-up

```markdown
## Write-up

1. In one line: OLMo, Phi, ChatGPT — what can you *see*, and what are you *allowed* to do with it?
2. Your T1-03 winner: which of its licence terms would matter most for a Ministry service, and which clause says so?
3. Why might TTDF refuse a pretty public API even if it scored higher in T1-03?
4. Which GPU question from the card could you not answer today, and who in your Ministry could?
```

---

## 5. Instructor answer key (goes in the completed notebook, filled into cells 7 and 11)

Quotes are exact from the local files. Section numbers follow the documents' own numbering.

### 5.1 Scavenger hunt (Llama 3.2 Community License Agreement and AUP)

| Q | Answer | Exact words |
|---|---|---|
| 1 | FOUND: §1.a. No separate rule for commercial or government use; the only size rule is §2 | §1.a: “non-exclusive, worldwide, non-transferable and royalty-free limited license … to use, reproduce, distribute, copy, create derivative works of, and make modifications to the Llama Materials” |
| 2 | FOUND: §1.a, and §5.b (you own your changes) | §1.a: “create derivative works of, and make modifications”. §5.b: “you are and will be the owner of such derivative works and modifications” |
| 3 | FOUND: §1.b.i and §1.b.iii | §1.b.i: “(A) provide a copy of this Agreement with any such Llama Materials; and (B) prominently display ‘Built with Llama’ … you shall also include ‘Llama’ at the beginning of any such AI model name.” §1.b.iii: a “Notice” text file containing “Llama 3.2 is licensed under the Llama 3.2 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved.” |
| 4 | FOUND: §2 Additional Commercial Terms | “If, on the Llama 3.2 version release date, the monthly active users of the products or services made available by or for Licensee, or Licensee’s affiliates, is greater than 700 million monthly active users in the preceding calendar month, you must request a license from Meta, which Meta may grant to you in its sole discretion” |
| 5 | NEED LINKED TERMS: Acceptable Use Policy, via §1.b.iv | “adhere to the Acceptable Use Policy for the Llama Materials (available at https://www.llama.com/llama3_2/use-policy), which is hereby incorporated by reference into this Agreement” |
| 5b | FOUND: AUP item 2.a | Item 2: “Engage in, promote, incite, facilitate, or assist in the planning or development of activities that present a risk of death or bodily harm to individuals, including use of Llama 3.2 related to the following:” 2.a: “Military, warfare, nuclear industries or applications, espionage …” |
| 6 | NOT FOUND. The licence says nothing about training data. The model card is where you would look next | (search for “training data” returns nothing in the licence) |
| 7 | FOUND: §3 Disclaimer of Warranty (and §4 Limitation of Liability) | §3: “THE LLAMA MATERIALS AND ANY OUTPUT AND RESULTS THEREFROM ARE PROVIDED ON AN ‘AS IS’ BASIS, WITHOUT WARRANTIES OF ANY KIND” |
| 8 | Accept either FOUND: §1.b.iv and AUP item 1.e, or NEED LINKED TERMS: AUP 1.e and data-protection law. The point: the licence has no privacy rules of its own; it sends you to the law | §1.b.iv: “must comply with applicable laws and regulations”. AUP 1.e: “Collect, process, disclose, generate, or infer health, demographic, or other sensitive personal or private information about individuals without rights and consents required by applicable laws” |
| 9 | FOUND: §7 | “governed and construed under the laws of the State of California … The courts of California shall have exclusive jurisdiction” |
| 10 | FOUND: §6 and §5.c | §6: “Meta may terminate this Agreement if you are in breach of any term or condition of this Agreement.” §5.c: licences “shall terminate” if you sue Meta claiming the Llama Materials infringe your rights |

### 5.2 Scenarios

**S1 Internal pilot**

- **OLMo / Apache 2.0: permitted.** §2 grants use. The conditions in §4 apply only when you “reproduce and distribute copies”, and nothing leaves the Ministry. Linked Ai2 guidelines: item 6.a disallows “using output toward larger decision-making systems that will influence actions, decisions, or policies without a human in the loop”; the named reviewer keeps a human in the loop. Privacy and records rules apply separately.
- **Llama 3.2: permitted with obligations.** §1.a grants use; §1.b.iv requires compliance with law and the AUP. Whether an internal staff tool is “make available … a product or service” under §1.b.i (which would need “Built with Llama”) is not settled by the text: either show “Built with Llama” on the tool's About page, which costs nothing, or escalate.
- **Teaching point:** the common Ministry case is not barred under either licence.

**S2 Public chatbot, weights stay on the server**

- **OLMo / Apache 2.0: permitted.** No copies of the Work are distributed, so §4 is not triggered. Linked Ai2 guidelines: item 5.b disallows “Applications that do not disclose that the content is generated through automated means”, so say on the page that answers are AI-generated.
- **Llama 3.2: permitted with obligations.** §1.b.i(B): a service that “contains” Llama Materials must “prominently display ‘Built with Llama’” on a related website or interface. AUP item 4: do not “Fail to appropriately disclose to end users any known dangers of your AI system”. AUP item 3.e: do not represent “that the use of Llama 3.2 or outputs are human-generated”. §1.b.i(A) (a copy of the Agreement “with any such Llama Materials”) is aimed at handing over the materials themselves; linking the licence on the About page is a cheap way to cover it.
- **Teaching point:** hosting a service and shipping weights are different events. Apache's conditions start on distribution; Llama's credit rule also covers products and services.

**S3 Publishing “CivicDesk-Redact-1B”**

- **OLMo / Apache 2.0: permitted with obligations.** §4(a) “give any other recipients … a copy of this License”: the OLMo repo has no LICENSE file at this revision, so add the Apache text yourself. §4(b) changed files “carry prominent notices stating that You changed the files”. §4(c) keep existing copyright and attribution notices. §4(d) does not bite: the OLMo repo has no NOTICE file. The closing paragraph of §4 lets you put your own licence terms on your modifications. §6: no right to use Ai2's marks beyond “reasonable and customary use in describing the origin of the Work”. The name “CivicDesk-Redact-1B” is fine.
- **Llama 3.2: permitted with obligations, but not under that name.** §1.b.i: include “‘Llama’ at the beginning of any such AI model name” (for example “Llama-CivicDesk-Redact-1B”), provide a copy of the Agreement, display “Built with Llama”; §1.b.iii: ship the Notice file with the exact sentence; §5.a: the “Llama” mark is licensed only for that naming rule and under Meta's brand guidelines. If Ministry branding rules do not allow a third-party trademark at the front of a product name, this route does not work, and the Apache model does.
- **Unclear - escalate:** whether an adapter published without the base weights is itself “Llama Materials (or any derivative works thereof)”. The text does not say. The safe course is to follow §1.b.i and §1.b.iii anyway.
- **Teaching point:** the second walkthrough of the day, if time allows. Same job, one licence needs a renamed product.

**S5 GlobalChat, 750 million monthly active users in August 2024**

- **OLMo / Apache 2.0: permitted.** Apache has no user cap.
- **Llama 3.2: permission required (for GlobalChat).** §2 counts monthly active users “on the Llama 3.2 version release date” (September 25, 2024) “in the preceding calendar month” (August 2024), including “Licensee’s affiliates”. Over 700 million means GlobalChat “must request a license from Meta, which Meta may grant … in its sole discretion”, and has no rights “unless or until Meta otherwise expressly grants” them. The text says nothing about a fee: it is a separate licence Meta may or may not grant, not an automatic charge.
- **The Ministry itself** is not over the threshold, so §2 does not apply to it. If it receives the model from GlobalChat “as part of an integrated end user product”, §1.b.ii says §2 “will not apply to you”.
- **Teaching point:** the rule is a snapshot tied to one date per release. Under the earlier Meta Llama 3 licence the date is April 18, 2024, so the month counted is March 2024 (see the deep track).

**S4 (walkthrough):** Llama 3.2 prohibited (AUP 2.a via §1.b.iv); OLMo permitted under Apache §2, Ai2 guidelines unclear - escalate. See the script under cell 9.

**Extra scenarios for the deep track or questions from the floor**

- **S6 EU partner and the vision model.** An organisation whose principal place of business is in the EU wants to run Llama 3.2 11B Vision to read scanned Cabinet notes. The AUP's closing paragraph: “With respect to any multimodal models included in Llama 3.2, the rights granted under Section 1(a) … are not being granted to you if you are … a company with a principal place of business in, the European Union. This restriction does not apply to end users of a product or service that incorporates any such multimodal models.” Label for that organisation: **prohibited** (no rights granted). It does not touch the 1B model, which the card calls “text in/text out”, and it does not touch a Trinidad and Tobago Ministry.
- **S7 Résumés with national ID numbers.** Running either model locally on résumés is a licence question only at the edges (Llama AUP 1.e points to “rights and consents required by applicable laws”; Ai2 guideline 6.b disallows classifying people “based on protected characteristics”). The main question is data protection. Label: **unclear - escalate**, to the data-protection officer, whatever the licence.

---

## 6. Learner worksheet (printable, `tier1/day1/cards/licence_worksheet.md`)

Create this file with exactly this content, so people without a notebook open can follow on paper.

```markdown
# T1-04 licence worksheet

Answer with FOUND: §___ "quote", NOT FOUND, or NEED LINKED TERMS: ___.

## Part A: Llama 3.2 Community License Agreement (licences/llama-3.2/LICENSE)

1. May we use it, and is there a separate rule for commercial or government use?
2. May we fine-tune it?
3. If we publish a fine-tuned model, what must we do?
4. Is there a user limit?
5. Which uses are banned? Then, in the use policy: is military use covered?
6. Does it say what data trained the model?
7. Does Meta promise the outputs are correct?
8. Does the licence handle privacy for documents we feed it?
9. (Early finishers) Which courts?
10. (Early finishers) How could we lose the licence?

## Part B: label each scenario for each licence

Labels: permitted / permitted with obligations / permission required / prohibited / unclear - escalate

| Scenario | OLMo (Apache 2.0) | clause | Llama 3.2 | clause |
|---|---|---|---|---|
| S1 internal pilot, reviewed summaries | | | | |
| S2 public chatbot, weights stay on server | | | | |
| S3 publish "CivicDesk-Redact-1B" | | | | |
| S5 partner with 750M monthly users (Aug 2024) | | | | |

## Part C: one question you would send to counsel

______________________________________________
```

---

## 7. Optional deeper track: `tier1/deep/T1-04d_licences_deep.ipynb`

Create the folder if it does not exist. All cells `# [OPTIONAL]`, all offline, all through `licence_lab`. The notebook sits in `tier1/deep/`, so its first code cell does `import sys; sys.path.insert(0, "../day1"); import licence_lab as L`. Sections:

1. **Meta Llama 3 vs Llama 3.2.** Print §2 of both (`L.find("llama3_licence", "700 million")`). Same rule; the date differs (April 18, 2024 vs September 25, 2024), so the month counted differs (March 2024 vs August 2024). Then print §1.b.i of each: Llama 3 asks for “Built with Meta Llama 3” and a name starting “Llama 3”; Llama 3.2 asks for “Built with Llama” and a name starting “Llama”, and adds “or any outputs or results of the Llama Materials” to what triggers the naming rule. Then `L.find("llama3_licence", "improve any other large language model")`: Meta Llama 3's §1.b.v says “You will not use the Llama Materials or any output or results of the Llama Materials to improve any other large language model (excluding Meta Llama 3 or derivative works thereof).” Ask: what does the same search find in Llama 3.2? (Answer: NOT FOUND. The question for learners is what replaced it: the output-trained naming rule in §1.b.i.)
2. **The use policy moved.** Print item 1.e from `llama32_aup` and from `llama32_aup_2024`. Current: “without rights and consents required by applicable laws”. September 2024: “unless you have obtained the right to do so in accordance with applicable law”. The licence incorporates the policy at its URL, so the version that counts is the one in force when you rely on it. Lesson: record the date you read it.
3. **The vision exclusion.** S6 above, with `L.find("llama32_aup", "multimodal")` and `L.find("llama32_card", "text in/text out")`.
4. **Phi-4-mini: MIT plus notices.** `L.show("phi_licence", "MIT License")`; MIT's only condition is that “The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.” Then `L.find("phi_notice", "flash-attention")` (a third-party component with its own BSD 3-Clause terms) and `L.find("phi_card", "Trademarks")` (“Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship”).
5. **OLMo's fine-tuning data.** The OLMo card names the SFT set `allenai/tulu-3-sft-olmo-2-mixture-0225`; that data card states no licence (`L.find("tulu_olmo_card", "licen")` returns NOT FOUND). Its parent set's card says: “this collection is licensed under ODC-BY-1.0 license; different licenses apply to subsets of the data. Some portions of the dataset are non-commercial. We present the mixture as a research artifact.” Discuss: the model's Apache licence is not the data's licence. Data licences matter if you retrain on that data; whether they reach the model's weights is a legal question that is not settled here. Escalate if a project reuses the data.
6. **Is this open source AI?** Print the OSI definition's Data Information, Code and Parameters lines (`L.find("osaid", "Data Information")` and so on). Fill a three-row table for OLMo, Phi and Llama 3.2: what is published, under what terms. Do not conclude a verdict for OSI; note what you would need to check.

---

## 8. Acceptance checks (Cursor reports each as pass or fail with evidence)

1. `cd tier1/day1/licences && sha256sum -c SHA256SUMS` passes for every line, and the count matches the number of files in the folder minus `SHA256SUMS` itself.
2. `git diff --stat` shows no change to any file under `tier1/day1/licences/` after the copy (the files are added, never edited).
3. In the container, from `tier1/day1`, `python -c "import licence_lab as L; assert L.verify()"` prints "All N licence files match" with the real N.
4. Every `L.find` call in cells 6, 9 and 10 returns at least one paragraph, except `L.find("llama32_licence", "training data")` and `L.find("ai2_guidelines", "military")`, which must print NOT FOUND. List the call and its first returned line.
5. For each quotation in section 5 of this spec, `L.find` on a distinctive phrase from it returns a paragraph containing the whole quoted phrase. Report any that fail.
6. The notebook has 17 cells in the order of section 4. Code cells start with `# [RUN]`, `# [CHANGE]` or `# [OPTIONAL]`.
7. Run all cells top to bottom with nbclient on CPU, with no network, with blank answers: no errors; cell 7 prints the format problems; cell 11 prints the label problems; cells 2, 6 and 9 print file text.
8. Run again with a fake `logs/T1-03_scorecard.json` (OLMo 2, Phi 1): cell 2 prints "T1-03 winner on quality: OLMo (OLMo 2/2, Phi 1/2)". Delete the fake log afterwards.
9. `completed/T1-04_openness_licences_gpu.ipynb` runs end to end with the answer key filled, and cells 7 and 11 print "Format OK" and "Labels OK".
10. The GPU card cell (13) contains all six original questions word for word plus the 4-minute line; `cards/gpu_questions.md` is unchanged (`git diff` empty).
11. `build_day1_notebooks.py`'s T1-04 cell strings equal the notebook's cell sources (compare by loading both; do not run the generator to write files).
12. No other `.ipynb` changed (`git diff --stat -- '*.ipynb'` lists only the T1-04 notebook and its completed copy, plus the new deep notebook).
13. `docker build` includes `tier1/day1/licences/` in the image: list `/opt/civicdesk/tier1/day1/licences` inside the built container (the Dockerfile copies the repo with `COPY . /opt/civicdesk`; `.dockerignore` excludes only the root README.md, which does not touch `licences/README.md`).
14. Timing dry run: a person reading cells 0 to 16 aloud and running them, without answering, finishes in under 12 minutes, leaving the rest for the hunt, the pairs and the GPU card.
15. Search the new notebook text for the words "guarantee", "cleared", "legal advice" and "you are allowed to": only the one sentence in cell 0 ("This is practice in reading licences, not legal advice") may match.

---

## 9. Things this spec does not settle

- Whether the Ai2 Responsible Use Guidelines bind a user on top of Apache 2.0. The lab treats this as an open question for counsel.
- Whether a LoRA adapter shipped alone counts as "Llama Materials (or any derivative works thereof)" under Llama 3.2.
- Whether an internal staff tool is "made available" under Llama 3.2 §1.b.i.
- Whether licences on fine-tuning data reach the weights of a model trained on it.
- The gated Hugging Face copies of the Llama 3.2 licence and policy were not checked.
