# Cursor brief: T1-05 worked résumé-redaction canvas, frozen baseline benchmark, gold-pair exercise

Repo: https://github.com/justkrismanohar/fine-tuning-build, read at `main`, commit `0bb94f9` (12 November 2026). Nothing was changed or pushed.
Target notebook: `tier1/day1/T1-05_usecase_canvas.ipynb`.
Slot: 14:20 to 14:55 (35 minutes, group), then overnight 20 to 30 minutes. Both unchanged.

This brief is for Cursor. It says which files to add, which cells to keep, edit or insert and in what order, the exact text, the learner exercise, the instructor answer key, the Day 3 handoff and the checks to report. Appendices A to D hold reference code and data that were run and tested while writing this brief. Copy them as given.

---

## 0. What this change does, and what it must not claim

T1-05 stays a group canvas exercise. Three things are added around it.

1. **A worked example.** The instructor fills the same canvas for a fictional CivicDesk task, redacting personal data from synthetic CVs before an internal shortlisting panel sees them. Every canvas line is filled.
2. **A baseline benchmark run.** The instructor runs the prompted, frozen OLMo on a frozen, held-out set of 40 synthetic CVs. The answer key comes from code, not from a model. Day 3 reuses the identical set, scorer and rule to measure what fine-tuning changed. The run is a measurement, not a demonstration that OLMo is good enough. Day 3 may show better, worse or mixed results.
3. **A gold-pair exercise.** Learners draft contrasting pairs: text that should trigger the action beside a near miss that should not. This is their roadmap for later data preparation.

For learners, the whole block is a **thought exercise in experimental design, not a live build**. They need no dataset of their own today. They design the experiment and pin down the metrics.

It must not claim any of the following:

- That T1-03 measured résumé redaction. T1-03 scored GO/BLOCK screening of CivicDesk draft replies. GO and BLOCK are T1-03's labels. T1-05 never uses them. Per document it uses **HOLD** and **PASS CHECKS**. Per run it uses **meets the rule / does not meet the rule**.
- That OLMo is the chosen model. It is the model already served, licence-checked in T1-04 and sized in the GPU card. That makes it the provisional thing to measure, nothing more.
- That a synthetic pass is production clearance, or that any output may be released outside the room.
- That fine-tuning will improve the score.

---

## 1. Ground rules for Cursor

1. **Edit the notebook directly, then align the generator.** `tier1/day1/build_day1_notebooks.py` writes every Day 1 notebook from strings in the script. I checked it in a scratch copy: T1-05's 6 cells currently match the script exactly. But T1-01 matches only 6 of its 19 cells, so a full run would overwrite hand edits in T1-01. **Do not run the script.** Edit the `.ipynb` JSON with a short one-off Python script (`json` or `nbformat`), then delete it. After that, replace the T1-05 block in the generator (it starts at the `# T1-05` comment, around line 901, and runs to the end of the `write("T1-05_usecase_canvas.ipynb", ...)` call) with the new cell sources. Do not run the script to test this. Load both and assert the cell sources are identical. If the `--only` option from the T1-02 spec already exists, you may use it for T1-05 alone.
2. **Do not touch any other notebook**, including Day 3. Section 7 defines the Day 3 contract. Building Day 3 is separate work.
3. **No new model loads.** Use the backend the container already serves through `civicdesk_lab.chat()` (the link-to-container pipeline). Do not load weights in the notebook. The token count loads only the tokenizer files from the model folder already in the image.
4. **Learners do not run the 40-document benchmark.** Each learner's container would send 40 requests, and the result is the same at temperature 0. The instructor runs it live once. Learners load the committed, measured baseline file.
5. **Synthetic data only.** No real CVs, names, IDs or EOI attachments anywhere in the repo, logs or outputs. All names, addresses and numbers in Appendices A and B are fictional. They use `example.invalid/org/net` domains and 555 phone numbers.
6. **Do not commit `logs/*.json`.** `.dockerignore` already excludes them. Keep them out of git too. The `baselines/` folder (synthetic outputs only) is committed on purpose.

---

## 2. Files to add

The container copies the whole repo to `/civicdesk` (`COPY . /opt/civicdesk`, then `cp -a` in the entrypoint), so a new top-level `tier1/shared/` folder ships with no Dockerfile change.

```
tier1/shared/resume_redaction/
  README.md                       (section 7: the Day 1 / Day 3 contract)
  build_teaching_set.py           (Appendix A: policy + 7 worked documents)
  build_benchmark.py              (Appendix B: 40-document held-out test split)
  redaction_eval.py               (Appendix C: scorer, checks, stop rule, rule check, live runner)
  data/teaching_set_v1.json       (generated by A)
  data/resume_redaction_test_v1.json   (generated by B)
  data/illustrative_outputs_teaching_v1.json   (Appendix D, copy verbatim)
  baselines/olmo_baseline_v1.json (measured in the container, section 3)
tier1/day1/cards/t1_05_release_and_rollout.md   (section 6: optional reading)
tier1/day1/completed/T1-05_gold_pairs_example.md (section 5.3)
```

Generate the data files by running `python build_teaching_set.py` then `python build_benchmark.py` from `tier1/shared/resume_redaction/`. The output must match what I got:

- Teaching set: 7 documents, 26 spans, sha256 `39c0e0ea82d2ef8783bc9ffa4e145c0803a7d5b394c2af57adad65bef059e7f2`.
- Benchmark: 40 documents, 165 spans (PERSON 50, EMAIL 45, PHONE 45, ADDRESS 15, DOB 5, ID 5), sha256 `c299eb39a169f639fd72b48963fe1154d7c9b4a0786eb4a87354dcd3ccbdd370`.

The benchmark has 5 documents in each of 8 categories, fixed before any run: standard, referee_dob_id, first_name_in_prose, family_business_employer, obfuscated_email, inline_prose_third_party, repeated_identifiers, no_pii. If a hash differs, stop and report it. Do not edit the data to make it match.

### How the labels are made (why there is no self-judging)

Each document is rendered from listed fictional field values. Its spans are every exact occurrence of each value. Where values overlap, the longer one wins, so an email containing a surname is one EMAIL span. The expected output replaces each span with its placeholder. The builders also assert that every `keep` anchor (job line, duty, qualification, reference number) survives in the expected output. No model writes or checks any label. If a later version uses a model to draft the CV prose, the labels must still come from the inserted values, and a person must review the rendered texts before the hash is frozen.

### Redaction policy (`T1-05-policy-v1`, in Appendix A)

- **Redact:** PERSON (applicant, referees, any other private person named), EMAIL (including spelled-out forms), PHONE, ADDRESS (home or postal), DOB, ID (national or personal ID numbers).
- **Keep:** employer and institution names, even when they contain a family name. Also keep job titles, duties, employment dates, qualifications, skills, numbers about the work, and vacancy or document reference numbers.
- **Out of scope, routed to manual:** photographs, scans, non-English text, documents over the token budget.

The family-business case ("Hosein & Sons Hardware Ltd") is a deliberate policy question. The name identifies the person in a small place, but the policy keeps it. A real project's policy owner must rule on it. In the classroom it shows that the answer key encodes a policy decision, not a fact.

---

## 3. The measured baseline (instructor, before class)

I could not run OLMo while writing this. Only its tokenizer is on my machine, not its weights. **There are no measured model outputs in this brief.** The only outputs here are the illustrative ones in Appendix D: I wrote them by hand, and the file says so.

In the course container, with the OLMo backend live (`lab.use_backend("local")` or `"brev"`), run from `tier1/day1`:

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path("..") / "shared" / "resume_redaction"))
import civicdesk_lab as lab, redaction_eval as R
lab.use_backend("local")            # whatever T1-01 uses in class
b = R.load_benchmark()
run = R.run_live(b, "olmo")
assert run["measured"], run["notes"]   # demo or fallback replies are never saved as a baseline
run["hardware"] = lab.gpu_note()    # or the GPU name from nvidia-smi
run["model_revision"] = "<revision pinned in the image>"
R.save_run(run, "olmo_baseline_v1")
```

Then:

- Run it a second time and diff the outputs. At temperature 0 on the same image they should be identical. Report any difference. Do not hide it.
- Report the wall time for all 40 documents. If it is over about 4 minutes, the instructor starts the live run before 14:20 (end of T1-04) and the notebook shows the committed file while it runs.
- Do not change the prompt (`redact-prompt-v1` in Appendix C) after seeing results. A prompt change is a new prompt version and a new baseline file. The old file stays.
- `civicdesk_lab.chat()` sends `max_tokens: 256`. The longest expected output in the benchmark is 102 OLMo tokens (I measured this with the OLMo tokenizer, transformers 5.22.2), so 256 leaves room. A truncation is still recorded as a failure.

Token figures: the course server returns no `usage` field today. If the T1-03 server change that adds `usage` is in, `run_live` saves it under `usage_from_server`. Otherwise call `R.count_tokens()`, which loads only the tokenizer from `/models/olmo` (or `CIVICDESK_TOKENIZER_DIR`). For reference, with this system prompt and OLMo's chat template, the 7 teaching documents come to 148 to 207 input tokens each. The 40 benchmark texts alone total 3,810 tokens, 143 at most per document.

---

## 4. Notebook: cell by cell

Final order. "Keep" means byte-identical to the current cell. Current cells are numbered 0 to 5. Time marks are for the instructor and appear only in the title cell.

| New # | Source | Type | In-class minutes |
|---|---|---|---|
| 0 | current 0, edited | md | |
| 1 | new: design, not build | md | 14:20 to 14:22 |
| 2 | current 1, keep | md | |
| 3 | new: what Day 1 already gave us | md | 14:22 to 14:24 |
| 4 | new: worked canvas | code | 14:24 to 14:28 |
| 5 | new: quality target vs stop trigger | md | |
| 6 | new: teaching set replay | code | 14:28 to 14:31 |
| 7 | new: reading the replay | md | |
| 8 | new: baseline benchmark | code | 14:31 to 14:35 |
| 9 | new: what the baseline does and does not say | md | |
| 10 | current 2, edited | code | 14:35 to 14:48 group canvas |
| 11 | current 3, edited | md | |
| 12 | new: gold pairs | code | 14:48 to 14:52 first pair |
| 13 | new: pairs as a data roadmap | md | |
| 14 | current 4, edited | code | 14:52 to 14:55 save |
| 15 | current 5, edited | md | overnight |
| 16 | new [OPTIONAL]: release and rollout | md | overnight optional |
| 17 | new [OPTIONAL]: calculators | code | overnight optional |

Trade-off for Kris: the group canvas gets 13 minutes in class instead of most of the 35. That works because the worked example shows a finished canvas first, and the overnight block (unchanged at 20 to 30 minutes) finishes it. If the room is slow, skip cell 6's discussion and go straight to cell 8.

### Cell 0 (edit)

Change only the first two lines after the title. Everything from "**Notebook learning outcomes**" down stays as it is, except the outcomes paragraph:

```
**Time:** 14:20–14:55, then overnight 20–30 min &nbsp;|&nbsp; **Evidence:** canvas (`cards/usecase_canvas.md`) + gold pairs (logged)
```

Replace the outcomes paragraph with:

```
Write a testable use case a domain person can verify. Frame the *type* of problem in the EOI, not a live system. Watch one worked canvas get measured, then design your own experiment: what you would measure, what counts as good enough, and what stops a document.
```

### Cell 1 (new markdown)

```
## This block is design, not build

This is a thought exercise in **experimental design**. Nobody builds a system here.

- You do **not** need your own dataset today. Do not fetch one.
- Your job is to design the experiment and pin down the metrics: who checks the output, what "wrong" looks like, how you would count it, what number is good enough (written down **before** any run), and what makes a single document stop.
- The instructor's worked example runs a real measurement so you can see what your design turns into later. You copy the *shape*, not the task.
```

### Cell 2: keep (current cell 1, Ministry link and overnight readers)

### Cell 3 (new markdown)

```
## Worked example: what Day 1 already gave us, and what it did not

The instructor's example is a fictional CivicDesk HR task: **remove personal data from CVs before an internal shortlisting panel reads them**, so the panel judges qualifications, not identity. Every CV is synthetic.

What the morning gave this project:

- **T1-01 first call:** we can send text to OLMo through the course pipeline and get text back. That is plumbing, not quality.
- **T1-02 tokens:** we can count what a CV costs in tokens, so latency and cost questions have a unit.
- **T1-03 model comparison:** we learned how to measure on a frozen, rule-labelled set. Its GO/BLOCK labels scored draft-reply screening, a **different task**. It says nothing about redaction.
- **T1-04 licence and GPU gates:** OLMo passed "may we" and "can we" for classroom use. That makes it the *provisional* model to measure, not the chosen one.

What we do not know yet: whether a prompted OLMo redacts CVs well enough. Only a measurement on this task can say.
```

### Cell 4 (new code): the worked canvas

Same keys as the learner canvas (cell 10), plus the design keys this brief adds. Paste exactly:

```python
# [RUN] the instructor's worked canvas. Fictional CivicDesk names only.
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
    print(f"{k}: {v}\n")
```

### Cell 5 (new markdown)

```
### Teaching note: a quality target is not a stop trigger

Two different things sit on the canvas.

- **Acceptance rule (quality target):** a pass mark for a *batch*, checked once on the frozen test set. It needs the answer key. It answers "is this good enough to continue to the next stage?"
- **Stop condition (per-document trigger):** checked on *every* document at run time, with no answer key. It answers "may this one output go to the panel, or does it wait for a person?" If the email check fires, that CV is held and routed to the authorised verifier. It is not released.

The checks have false alarms (a reference number that looks like a phone number) and misses (an email spelled out in words). **No alert does not mean safe.**
```

### Cell 6 (new code): teaching set replay

```python
# [RUN] seven worked CVs, scored against the answer key, then through the stop rule.
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
    print(f"   run-time stop rule: {r['reasons'] or 'nothing fired'} -> {r['decision']}\n")
```

I ran this logic. The decisions it must print are:

- R01 passes checks (correct output).
- R02 HOLD (referee phone and email caught by pattern).
- R03 HOLD (first name caught only by the known-name check; the 30% to 40% edit is caught by nobody at run time, only by the answer key).
- R04 passes checks although over-redacted (employer masked).
- R05 passes checks although the spelled-out email leaked: the silent leak.
- R06 HOLD (truncation).
- R07 HOLD although correct: the vacancy reference trips the phone pattern, a false hold.

### Cell 7 (new markdown)

```
### Reading the replay

- **R05 is the lesson.** The email leaked and no check fired. A quiet run is not a safe run.
- **R07 is the cost.** A correct output was held. Every false hold is a person's time.
- **R03's 30% → 40%** is invisible to every run-time check. Only the answer key catches it, which is why you measure on a labelled set *before* trusting run-time checks.
- **R04** passed the checks and still harmed the candidate (the employer vanished). Over-redaction is an error with a cost, not a safe default.
- **R06** cut off mid-sentence. Span recall would count the cut-off name as "removed", so read recall beside truncation.

Adding a second detector or a second model does not automatically fix this. Two systems trained on similar text tend to miss the same spelled-out email.
```

### Cell 8 (new code): baseline benchmark

```python
# [RUN] the frozen 40-CV benchmark for prompted OLMo.
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
print("Meets the example rule:", verdict["meets_rule"])
```

### Cell 9 (new markdown)

```
### What the baseline says, and what it does not

- It is a **measurement of one prompt on one model on 40 synthetic CVs**. It is the number Day 3 has to beat, and the same 40 CVs, scorer and rule come back on Day 3 unchanged.
- If it **meets** the rule, the honest conclusion is that a prompt may be enough for this classroom task. Fine-tuning would need another reason.
- If it **does not**, Day 3 tests whether one adapter closes the gap. It may help, it may not, and it may fix one category and break another. Nobody knows until it is measured.
- Either way, **meeting the rule is not permission to release anything.** It is synthetic, classroom evidence. Real CVs need a real test set, an authorised environment and the owner's decision.
- 40 documents is small. Zero failures in 40 is consistent with a true failure rate up to about 7% (one-sided 95% bound, and only for documents like these). Differences of one or two documents between runs are noise-sized.
- The rule was written **before** the run. Changing it after seeing the result is a new experiment, not a pass.
```

### Cell 10 (edit current cell 2): the learner canvas

Keep every existing key and its default. Change the first comment and add two keys after `success_measure`:

```python
# [CHANGE] fill as a group. Fictional CivicDesk names only. Design only: no dataset needed today.
```

```python
    "acceptance_rule": "write the pass mark BEFORE any run, as numbers",
    "test_set_plan": "how many examples, which categories, who labels them, how it stays frozen",
```

### Cell 11 (edit current cell 3, teaching note)

Keep the existing text. Insert this paragraph after its first paragraph:

```
Compare your canvas with the worked one, line for line. Yours does not need data, only a design: each measure should be something you could count, with a pass mark you would accept or reject before seeing a result, and a stop condition that works on one document at run time without an answer key.
```

Also add `acceptance_rule` and `test_set_plan` lines to `cards/usecase_canvas.md`, after "Success measure:":

```
- Acceptance rule (numbers, written before any run):
- Test set plan (size, categories, who labels, how it stays frozen):
```

### Cell 12 (new code): gold pairs

```python
# [CHANGE] Gold pairs: for YOUR use case, write text that SHOULD trigger the action beside a near miss that
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
    print(f"pair {i}: " + ("complete" if not empty and not same else f"to finish: {empty or 'the two texts are identical'}"))
```

### Cell 13 (new markdown)

```
### Teaching note: pairs are your data roadmap

A model learns a boundary from examples on both sides of it. A near miss is where a system usually fails. Your pairs are the start of a data-preparation plan:

1. **Freeze the test set first.** Before anyone writes training examples, set aside held-out examples nobody trains on or tunes against.
2. **Each pair names a category** the test set must cover, and a category the training data must cover.
3. **Labels come from your policy, checked by your verifier,** not from a model marking its own work.
4. **Don't copy test items into training.** If a pair came from a failure you saw in the test set, write a new example of that *kind*. Never reuse the test text.
5. The column "what real data you would need" is your shopping list for the real project, and the list of what must stay out.
```

### Cell 14 (edit current cell 4)

```python
# [RUN] save whatever you have. Empty strings are allowed at 14:55; overnight fills them.
import civicdesk_lab as lab
lab.save_log("T1-05_canvas_draft", canvas)
lab.save_log("T1-05_gold_pairs", {"pairs": gold_pairs})
print("draft and pairs saved — finish overnight in cards/usecase_canvas.md")
```

### Cell 15 (edit current cell 5)

Keep the existing two paragraphs. Change "Finish the canvas. Three remaining questions for Day 2." to:

```
Finish the canvas, including the acceptance rule and test set plan. Write six gold pairs (at least two near misses that a careless system would get wrong). Three remaining questions for Day 2.
```

Add at the end:

```
If you loaded a reference file, also see `completed/T1-05_gold_pairs_example.md`. Optional reading: `cards/t1_05_release_and_rollout.md` (how a stop rule becomes a safe rollout).
```

### Cell 16 (new markdown, optional)

```
## [OPTIONAL] After the canvas: release safety and rollout

For those who want more. Not needed for Day 2. Read `cards/t1_05_release_and_rollout.md`. Short version: a per-document hold protects one CV; a sampled audit estimates how often misses happen across many; a canary limits how many people one bad version can reach. None of them is permission to release, and none can un-send a CV that already leaked.
```

### Cell 17 (new code, optional)

```python
# [OPTIONAL] Two calculators. Every input is your own assumption, not a measured price or rate.
for n in (7, 40, 100, 300):
    print(f"0 failures in {n:>3} random audits -> true rate could still be up to {R.upper_bound_95(0, n):.1%} (one-sided 95%)")
print("(Valid only if the audited documents are a random sample of the documents you care about.)\n")

# Scoped cost per acceptable answer for the benchmark run in cell 8: compute + review of held docs only.
print(R.cost_per_acceptable(rows, compute_cost_per_doc=0.0,      # [CHANGE] your figure
                            review_minutes_per_hold=5,           # [CHANGE] your figure
                            reviewer_cost_per_hour=0.0))         # [CHANGE] your figure
```

Cell 17 reuses `rows` from cell 8 (the benchmark). The defaults are zero on purpose, so the notebook never shows a price nobody measured. I ran cells 4, 6, 8 (on a stand-in baseline made from the answer key, not a model run), 12 and 17 from this brief against the reference files; they ran without errors.

---

## 5. Learner exercise and instructor answer key

### 5.1 What groups hand in

- **By 14:55:** a canvas draft with at least problem, owner, verifier and one measure, plus one gold pair.
- **Overnight:** the full canvas including `acceptance_rule` and `test_set_plan`, six gold pairs, and three questions for Day 2.

### 5.2 Marking guide (instructor only; not shipped in the container)

A good design canvas:

- Names a **verifier by role** who is authorised to see the inputs and can mark an output wrong.
- Has a **baseline that is the current non-AI process**, with "not yet measured" allowed but a plan to measure it.
- Has **measures you can count**, split by error direction. For redaction that means missed PII, over-redaction and altered text. For criteria: a false "meets" vs a false "does not meet". For retrieval: wrong citation vs abstain. For a service desk: a forbidden tool call vs a missed triage.
- Has an **acceptance rule in numbers, written before any run**, labelled as the group's own example.
- Has a **per-document stop condition** that works without an answer key and routes to a person. A service-level pause is a bonus.
- Has an **excluded-data line** that is specific.
- Keeps the **intervention provisional** (T1-06 decides).

Common weak answers:

- "Accuracy above 90%": one number hides which way it fails.
- "Human reviews everything": not affordable. Ask what is routed and why.
- "Model confidence above 0.9": the probability of the generated words is not the probability that the decision is right.
- "Test on the training examples."
- No rule written before the result.

### 5.3 `completed/T1-05_gold_pairs_example.md` (ship this)

```
# Example gold pairs (loaded from reference)

Fictional CivicDesk text. If you loaded this file, write "loaded from reference" and replace each pair with your own cluster's.

| Cluster | Should trigger | Near miss: should not | Why |
|---|---|---|---|
| Résumé redaction | Referee: Gail Ramsaran, 868-555-0177 | Vacancy ref: CD-2024-117-3302 | A phone number vs a reference number with the same shape |
| Résumé redaction | rajiv dot persaud at example dot invalid | Data Entry Clerk, CivicDesk Permits Office | Spelled-out email vs ordinary words; pattern checks miss the first |
| A Criteria | "Diploma in library studies, 2019" → Human review required (C2 equivalence) | "Diploma in records management, 2019" → meets C2 | Equivalent-not-identical needs a person |
| B Retrieval | Question answered by HB-ATTACH-04 → cite it | Question outside the approved corpus → abstain | Cite vs abstain |
| C Service desk | "Reset my password" → refuse, route to IT | "How do I reset my password?" → give the published steps | Doing an action vs explaining it |
| D Local control | Cabinet note text → never leaves the box | Published circular → may use a hosted tool | Same format, different custody |
```

---

## 6. `cards/t1_05_release_and_rollout.md` (optional reading; ship this text)

```
# From stop rule to safe rollout (optional, T1-05)

Fictional CivicDesk résumé redaction. Classroom guidance, not a release procedure.

## Three different jobs

- **Per-document hold.** Checks run on every output. If one fires (residual email or phone, a name from the application form, an ID pattern, empty or much shorter output, timeout, out-of-scope input), that document is held and routed to the authorised verifier. It is not released. This protects that one document, and only against what the checks can see.
- **Sampled audit.** A person checks a random sample of outputs that passed the checks. This estimates how often misses happen across the batch. It does not protect the documents nobody looked at, and it does not authorise sending any of them outside the approved environment.
- **Service pause.** Stop the whole run when the batch looks wrong: an audit finds a leak above your threshold, holds jump, outputs come back malformed or empty in a burst, inputs change (new layout, language, scans), or the model, prompt or check version changed without a new measurement. Contain (stop sending), escalate to the owner, roll back to the last known-safe version or the manual process, reassess, and re-measure before restarting.

## What the numbers can and cannot say

- Zero failures in a small sample is not zero risk. With 40 random audits and no failures, the true miss rate could still be about 7% (one-sided 95% bound). With 300, about 1%. The bound holds only for documents like the ones sampled.
- Checks have false alarms and misses. A second detector or a second model is not automatically better; they often miss the same things.
- Confidence from generated-token probabilities is not confidence that a span is PII. Route on what the checks find and on document risk (new layout, unusual language, high-sensitivity role), not on the model sounding sure.

## Human capacity

You cannot review everything. Size the review queue from the measured hold rate and the audit sample. If the queue backs up, documents wait in the approved environment, or the work falls back to the manual process. They are never released unreviewed to clear the queue.

## Safe rollout, in stages

1. **Offline, synthetic:** the frozen benchmark, in the authorised environment.
2. **Shadow:** real inputs, outputs stored but sent to nobody new. Compare against the manual process.
3. **Canary:** one versioned model + prompt + checks, a small share of work, outputs only to staff already authorised to see the originals. No automatic external or public release of unreviewed redactions.
4. Before each stage: a written baseline, monitoring, stop thresholds, an accountable owner who decides, and a tested rollback to the known-safe manual workflow.

A canary limits how many people one bad version can reach. It is not proof of privacy. Rollback stops future harm; it cannot un-disclose a CV that already leaked.

## Logs

Keep raw CVs and redacted outputs out of broad logs. Log versions (model, prompt, checks, data), counts, check names that fired and decisions. In this course everything is synthetic.
```

---

## 7. Day 3 contract (`tier1/shared/resume_redaction/README.md`)

Ship this as the README. Day 3's notebook is not part of this change.

```
# Résumé redaction benchmark: Day 1 baseline, Day 3 reuse

- Test split: data/resume_redaction_test_v1.json, sha256 c299eb39a169f639fd72b48963fe1154d7c9b4a0786eb4a87354dcd3ccbdd370. Frozen. Never used to train, tune prompts, choose examples or set thresholds.
- Scorer and rule: redaction_eval.py (evaluate, summary_table, check_rule with EXAMPLE_RULE). Day 3 uses the same file and the same rule. Changing either after seeing results starts a new comparison.
- Prompted baseline: baselines/olmo_baseline_v1.json (prompt redact-prompt-v1, measured in the container image).
- Day 3 adds one run file per variant (e.g. baselines/olmo_adapter_v1.json) with the same fields, plus the adapter name, base model revision and training-data version.
- Day 3 training and validation data must be built from different name, street and email pools than build_benchmark.py's TEST_POOLS, with a different seed, and must not copy any test text. Assert no PII value overlaps the test split. The test uses the same 7 layouts plus a no-PII category, so it measures generalisation to new people and values, not to new layouts. A held-out-layout set is a separate decision.
- Report both runs side by side: the rule criteria, recall by type, acceptable-as-is by category, and the documents where the two runs disagree (fixed by the adapter / broken by the adapter). With 40 documents, one- or two-document differences are noise-sized; say so.
- Possible outcomes are better, worse or mixed. None is assumed. A pass on this set is classroom evidence, not release permission.
- Teaching set (data/teaching_set_v1.json) is for the worked example only. It is neither benchmark nor training data.
```

---

## 8. Checks for Cursor to report

Report each with its actual result.

1. Both builders reproduce the two sha256 values in section 2. The benchmark category and span counts match.
2. `data/illustrative_outputs_teaching_v1.json` is byte-identical to Appendix D, and its `fixture_sha256` equals the teaching set's hash.
3. Cell 6 prints the seven decisions listed under it.
4. Run the scorer on the benchmark's own `expected` outputs: 0 missed, 0 over-redacted, 40 acceptable, rule met given latencies under 20 s. Run it on the raw inputs: 35 of 35 documents leaked, recall 0.0.
5. Run the stop rule on the 40 correct expected outputs. I got ten holds: the five family-business documents (known-name check on the employer) and the five vacancy notices (phone pattern on the reference number). Confirm the count. It is the false-hold cost of a perfect run, and the instructor uses it when the baseline is discussed.
6. `run_live` with the demo backend returns `measured: False` and is refused by cell 8. With a dead endpoint it records `demo-fallback`, not outputs. I tested both outside the container.
7. `baselines/olmo_baseline_v1.json` was produced live in the container: `measured: True`, the right hash, model, prompt version, hardware and revision filled in. Report the two-run reproducibility diff and the 40-document wall time.
8. Cell 8 runs in replay mode with the backend off.
9. Notebook runs top to bottom in replay mode in the container with no new model load. Check `nvidia-smi` memory before and after.
10. T1-05 cell sources in the generator equal the notebook (assert, without running the generator). No other notebook changed (`git diff --stat`).
11. No GO or BLOCK string appears in T1-05, the card or the shared folder, except the one sentence in cell 3 naming T1-03's labels.
12. `grep` for real-looking data: every email domain in the shared data is `example.invalid`, `example.org` or `example.net`, and every phone number has 555 as its middle three digits.
13. `logs/*.json` not committed. `baselines/` committed.

---

## Appendix A: `tier1/shared/resume_redaction/build_teaching_set.py`

```python
"""Deterministic builder for the T1-05 teaching set (7 worked documents) and the shared redaction policy.

Labels come from the listed field values, never from a model. Spans = every exact occurrence
of each listed value; longer values win where they overlap (an email that contains a name is
one EMAIL span). Expected output = original with each span replaced by its placeholder.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY = {
    "version": "T1-05-policy-v1",
    "redact": {
        "PERSON": "Name of the applicant, referees, or any other private individual named in the text",
        "EMAIL": "Any email address, including spelled-out forms such as 'name dot x at y dot z'",
        "PHONE": "Any phone number, in any format",
        "ADDRESS": "Home or postal address (street, lot, village or town line)",
        "DOB": "Date of birth",
        "ID": "National ID or other personal identification number",
    },
    "keep": [
        "Employer and institution names, even when they contain a family name",
        "Job titles, duties, dates of employment, qualifications, skills, numbers about the work",
        "Vacancy or document reference numbers",
    ],
    "placeholders": ["[PERSON]", "[EMAIL]", "[PHONE]", "[ADDRESS]", "[DOB]", "[ID]"],
    "out_of_scope": "Photographs, scanned images, non-English text, documents over the token budget: not processed, routed to manual.",
}

DOCS = [
    {
        "id": "R01",
        "layout": "standard headed CV",
        "text": (
            "# Anika Ramnarine\n"
            "Email: anika.ramnarine@example.invalid | Phone: 868-555-0142\n"
            "Address: 14 Cedar Grove Trace, Fictionville\n"
            "\n"
            "## Experience\n"
            "- Records Officer, CivicDesk Central Registry, 2019-2025: indexed 12,000 files a year.\n"
            "\n"
            "## Education\n"
            "- BSc Information Management, University of Fictionville, 2018\n"
            "\n"
            "## Skills\n"
            "Retention schedules, EDMS indexing, spreadsheets\n"
        ),
        "pii": [
            ["PERSON", "Anika Ramnarine"],
            ["EMAIL", "anika.ramnarine@example.invalid"],
            ["PHONE", "868-555-0142"],
            ["ADDRESS", "14 Cedar Grove Trace, Fictionville"],
        ],
        "keep": [
            "Records Officer, CivicDesk Central Registry, 2019-2025",
            "indexed 12,000 files a year",
            "BSc Information Management, University of Fictionville, 2018",
            "Retention schedules, EDMS indexing, spreadsheets",
        ],
        "form": {"name": "Anika Ramnarine", "email": "anika.ramnarine@example.invalid", "phone": "868-555-0142"},
        "tests": "Baseline case: every identifier on its own labelled line.",
    },
    {
        "id": "R02",
        "layout": "CV with date of birth, ID and a referee block",
        "text": (
            "# Curriculum vitae: Tevin Okonkwo-Sealy\n"
            "Date of birth: 03/07/1994\n"
            "National ID: CD-ID-1994-0377\n"
            "Email: tevin.os@example.org\n"
            "\n"
            "## Experience\n"
            "- Lands Clerk, CivicDesk Lands Office, 2017-2024: processed survey plan requests.\n"
            "\n"
            "## Referees\n"
            "- Gail Ramsaran, Former Supervisor, CivicDesk Lands Office, 868-555-0177, g.ramsaran@example.invalid\n"
        ),
        "pii": [
            ["PERSON", "Tevin Okonkwo-Sealy"],
            ["DOB", "03/07/1994"],
            ["ID", "CD-ID-1994-0377"],
            ["EMAIL", "tevin.os@example.org"],
            ["PERSON", "Gail Ramsaran"],
            ["PHONE", "868-555-0177"],
            ["EMAIL", "g.ramsaran@example.invalid"],
        ],
        "keep": [
            "Lands Clerk, CivicDesk Lands Office, 2017-2024",
            "processed survey plan requests",
            "Former Supervisor, CivicDesk Lands Office",
        ],
        "form": {"name": "Tevin Okonkwo-Sealy", "email": "tevin.os@example.org", "phone": "868-555-0190"},
        "tests": "Referee contact details at the end; DOB and ID lines.",
    },
    {
        "id": "R03",
        "layout": "short profile with the first name repeated in prose",
        "text": (
            "Name: Oyelaran Dookhie\n"
            "Contact: (868) 555 0119 / o.dookhie@example.org\n"
            "Address: LP 27, Branch Road, Fictionville Village\n"
            "\n"
            "## Profile\n"
            "Oyelaran built the service-desk queue dashboard and reduced average queue time by 30%.\n"
            "\n"
            "## Experience\n"
            "- ICT Support Officer, CivicDesk Trade Unit, 2020-2025\n"
        ),
        "pii": [
            ["PERSON", "Oyelaran Dookhie"],
            ["PERSON", "Oyelaran"],
            ["PHONE", "(868) 555 0119"],
            ["EMAIL", "o.dookhie@example.org"],
            ["ADDRESS", "LP 27, Branch Road, Fictionville Village"],
        ],
        "keep": [
            "built the service-desk queue dashboard",
            "reduced average queue time by 30%",
            "ICT Support Officer, CivicDesk Trade Unit, 2020-2025",
        ],
        "form": {"name": "Oyelaran Dookhie", "email": "o.dookhie@example.org", "phone": "868-555-0119"},
        "tests": "Unfamiliar first name used alone in prose; phone with brackets and spaces.",
    },
    {
        "id": "R04",
        "layout": "CV where the employer carries the applicant's family name",
        "text": (
            "# Keisha Ramdass\n"
            "Phone: +1 (868) 555-0161 | Email: keisha.r@example.invalid\n"
            "\n"
            "## Experience\n"
            "- Accounts Clerk, Ramdass & Sons Hardware Ltd, 2016-2021: reconciled supplier invoices.\n"
            "- Accounts Officer, CivicDesk Finance Unit, 2021-2025\n"
            "\n"
            "## Education\n"
            "- ACCA Applied Knowledge, 2019\n"
        ),
        "pii": [
            ["PERSON", "Keisha Ramdass"],
            ["PHONE", "+1 (868) 555-0161"],
            ["EMAIL", "keisha.r@example.invalid"],
        ],
        "keep": [
            "Accounts Clerk, Ramdass & Sons Hardware Ltd, 2016-2021",
            "reconciled supplier invoices",
            "Accounts Officer, CivicDesk Finance Unit, 2021-2025",
            "ACCA Applied Knowledge, 2019",
        ],
        "form": {"name": "Keisha Ramdass", "email": "keisha.r@example.invalid", "phone": "868-555-0161"},
        "tests": "Policy keeps employer names; a family business name is a quasi-identifier the policy owner must rule on.",
    },
    {
        "id": "R05",
        "layout": "informal contact line with a spelled-out email",
        "text": (
            "# Rajiv Persaud\n"
            "Reach me: rajiv dot persaud at example dot invalid, or 868 555 0133 (WhatsApp)\n"
            "\n"
            "## Experience\n"
            "- Data Entry Clerk, CivicDesk Permits Office, 2022-2025: keyed 300 permit forms a week.\n"
        ),
        "pii": [
            ["PERSON", "Rajiv Persaud"],
            ["EMAIL", "rajiv dot persaud at example dot invalid"],
            ["PHONE", "868 555 0133"],
        ],
        "keep": [
            "Data Entry Clerk, CivicDesk Permits Office, 2022-2025",
            "keyed 300 permit forms a week",
        ],
        "form": {"name": "Rajiv Persaud", "email": "rajiv.persaud@example.invalid", "phone": "868-555-0133"},
        "tests": "Obfuscated email: pattern checks and exact form matching both miss it.",
    },
    {
        "id": "R06",
        "layout": "cover-letter prose with inline address and a third person named",
        "text": (
            "My name is Sharleen Bisnath and I live at 9 Hillview Road, Fictionville. "
            "You can reach me on 868-555-0188.\n"
            "\n"
            "I have worked as a Health Records Assistant at CivicDesk District Clinic since 2021, "
            "where I maintain appointment registers for 4 clinics.\n"
            "\n"
            "My mentor, Dr. Imran Sookdeo, encouraged me to apply for this post.\n"
            "\n"
            "## Qualifications\n"
            "- Diploma in Health Information, Fictionville Technical Institute, 2020\n"
        ),
        "pii": [
            ["PERSON", "Sharleen Bisnath"],
            ["ADDRESS", "9 Hillview Road, Fictionville"],
            ["PHONE", "868-555-0188"],
            ["PERSON", "Imran Sookdeo"],
        ],
        "keep": [
            "Health Records Assistant at CivicDesk District Clinic since 2021",
            "maintain appointment registers for 4 clinics",
            "Diploma in Health Information, Fictionville Technical Institute, 2020",
        ],
        "form": {"name": "Sharleen Bisnath", "email": "s.bisnath@example.invalid", "phone": "868-555-0188"},
        "tests": "Identifiers inside sentences, not on labelled lines; a third party who is not a referee.",
    },
    {
        "id": "R07",
        "layout": "vacancy notice extract with no personal data",
        "text": (
            "# Vacancy notice extract\n"
            "Vacancy ref: CD-2024-117-3302\n"
            "Position: Records Assistant, CivicDesk Central Registry\n"
            "Requirements: diploma in records management or equivalent; two years' experience.\n"
        ),
        "pii": [],
        "keep": [
            "Vacancy ref: CD-2024-117-3302",
            "Records Assistant, CivicDesk Central Registry",
            "diploma in records management or equivalent",
        ],
        "form": None,
        "tests": "No PII at all: anything masked is over-redaction. The reference number looks like a phone number to a loose pattern.",
    },
]


def find_spans(text: str, pii: list[list[str]]) -> list[dict]:
    cands = []
    for typ, value in pii:
        start = 0
        found = False
        while True:
            i = text.find(value, start)
            if i < 0:
                break
            cands.append((i, i + len(value), typ, value))
            found = True
            start = i + 1
        if not found:
            raise ValueError(f"label value not in text: {value!r}")
    # longest first; drop any candidate overlapping an accepted span
    cands.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
    taken: list[tuple[int, int, str, str]] = []
    for c in cands:
        if all(c[1] <= t[0] or c[0] >= t[1] for t in taken):
            taken.append(c)
    taken.sort()
    return [{"type": t, "text": v, "start": s, "end": e} for s, e, t, v in taken]


def redact(text: str, spans: list[dict]) -> str:
    out = text
    for sp in sorted(spans, key=lambda s: -s["start"]):
        out = out[: sp["start"]] + f"[{sp['type']}]" + out[sp["end"] :]
    return out


def build() -> dict:
    docs = []
    for d in DOCS:
        spans = find_spans(d["text"], d["pii"])
        expected = redact(d["text"], spans)
        for k in d["keep"]:
            if k not in d["text"] or k not in expected:
                raise ValueError(f"{d['id']}: keep anchor lost by the answer key: {k!r}")
        docs.append({
            "id": d["id"], "layout": d["layout"], "tests": d["tests"], "text": d["text"],
            "spans": spans, "expected": expected, "keep": d["keep"], "form": d["form"],
        })
    body = {"policy": POLICY, "docs": docs}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {
        "fixture_version": "teaching-set-v1",
        "split": "teaching (worked example only; not the benchmark, never training data)",
        "provenance": "Synthetic. Written by the course author from fictional field values. Labels derived deterministically from those values, not by a model. No real person's data.",
        "sha256": digest,
        **body,
    }


if __name__ == "__main__":
    fx = build()
    (Path(__file__).resolve().parent / "data" / "teaching_set_v1.json").write_text(json.dumps(fx, indent=2, ensure_ascii=False), encoding="utf-8")
    for d in fx["docs"]:
        print(d["id"], len(d["spans"]), "spans", [s["type"] for s in d["spans"]])
    print("sha256", fx["sha256"][:12])
```

## Appendix B: `tier1/shared/resume_redaction/build_benchmark.py`

```python
"""Deterministic builder for the frozen, held-out resume-redaction benchmark (Day 1 baseline, Day 3 reuse).

Everything is fictional. Labels come from the field values used to render each document, never from a
model. Name, street and email pools are split: the 'test' pools below are reserved for this benchmark
and must never be used to build Day 3 training or validation data.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from build_teaching_set import POLICY, find_spans, redact

BENCH_VERSION = "resume-redaction-test-v1"
SEED = 20261112
N_PII_DOCS = 35  # 7 layouts x 5
N_NO_PII_DOCS = 5

# Reserved for the TEST split only.
TEST_POOLS = {
    "first": ["Anjali", "Darnell", "Ifeoma", "Kavita", "Marlon", "Nadira", "Quincy", "Renuka", "Shivon",
              "Tariq", "Umeko", "Vashti", "Wendell", "Yolanda", "Zahir", "Chiamaka", "Deoraj", "Esperanza"],
    "last": ["Balgobin", "Charles-Mohan", "Dass", "Gopaul", "Hosein", "Jaggernauth", "Lalla", "Maharaj-Pierre",
             "Nanan", "Okafor", "Rampersad", "Sankar", "Thomas-Ali", "Vialva", "Waithe", "Ying"],
    "street": ["Pommerac Lane", "Silk Cotton Drive", "Old Mission Road", "Calabash Street", "Sapodilla Trace",
               "Mango Rose Avenue", "Lagoon View Road", "Hibiscus Close"],
    "town": ["Fictionville", "Mockton", "Sampleton", "Placeholder Bay", "Testbridge"],
    "domain": ["example.invalid", "example.org", "example.net"],
    "employer_family": ["Gopaul", "Hosein", "Lalla", "Sankar"],
}

JOBS = [
    ("Records Officer", "CivicDesk Central Registry", "indexed 9,500 files a year"),
    ("Lands Clerk", "CivicDesk Lands Office", "processed 40 survey requests a month"),
    ("ICT Support Officer", "CivicDesk Trade Unit", "closed 85% of tickets within two days"),
    ("Accounts Officer", "CivicDesk Finance Unit", "reconciled 600 supplier invoices a quarter"),
    ("Health Records Assistant", "CivicDesk District Clinic", "maintained registers for 3 clinics"),
    ("Data Entry Clerk", "CivicDesk Permits Office", "keyed 250 permit forms a week"),
]
QUALS = ["BSc Information Management, University of Fictionville", "Diploma in Records Management, Mockton Technical Institute",
         "ACCA Applied Knowledge", "Associate Degree in Office Administration, Sampleton College"]


def _phone(r: random.Random, style: int) -> str:
    b = r.randint(1000, 9999)
    return [f"868-555-{b}", f"(868) 555 {b}", f"+1 (868) 555-{b}", f"868 555 {b}"][style % 4]


def _person(r, used):
    while True:
        n = f"{r.choice(TEST_POOLS['first'])} {r.choice(TEST_POOLS['last'])}"
        if n not in used:
            used.add(n)
            return n


def _email(r, name, obfuscate=False):
    f, l = name.lower().split(" ", 1)
    local = f"{f}.{l.replace('-', '')[:6]}"
    dom = r.choice(TEST_POOLS["domain"])
    if obfuscate:
        return f"{local.replace('.', ' dot ')} at {dom.replace('.', ' dot ')}", f"{local}@{dom}"
    return f"{local}@{dom}", f"{local}@{dom}"


def _addr(r):
    return f"{r.randint(2, 98)} {r.choice(TEST_POOLS['street'])}, {r.choice(TEST_POOLS['town'])}"


def _job(r):
    t, org, duty = r.choice(JOBS)
    y = r.randint(2012, 2020)
    return t, org, duty, f"{y}-{y + r.randint(2, 5)}"


def layout(i: int, r: random.Random, used: set) -> dict:
    k = i % 7
    name = _person(r, used)
    first = name.split(" ")[0]
    t, org, duty, yrs = _job(r)
    q = r.choice(QUALS)
    qy = r.randint(2008, 2019)
    phone = _phone(r, i)
    em, form_em = _email(r, name, obfuscate=(k == 4))
    job_line = f"{t}, {org}, {yrs}"
    keep = [job_line, duty, f"{q}, {qy}"]
    pii = [["PERSON", name], ["PHONE", phone], ["EMAIL", em]]
    if k == 0:  # standard headed
        ad = _addr(r)
        text = f"# {name}\nEmail: {em} | Phone: {phone}\nAddress: {ad}\n\n## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        pii.append(["ADDRESS", ad]); cat = "standard"
    elif k == 1:  # DOB, ID, referee
        ref = _person(r, used)
        rph = _phone(r, i + 1)
        rem, _ = _email(r, ref)
        by = r.randint(1975, 2000)
        dob = f"{r.randint(1, 28):02d}/{r.randint(1, 12):02d}/{by}"
        nid = f"CD-ID-{by}-{r.randint(100, 999)}"
        text = (f"# Curriculum vitae: {name}\nDate of birth: {dob}\nNational ID: {nid}\nEmail: {em} | Phone: {phone}\n\n"
                f"## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n\n## Referees\n- {ref}, Former Supervisor, {org}, {rph}, {rem}\n")
        pii += [["DOB", dob], ["ID", nid], ["PERSON", ref], ["PHONE", rph], ["EMAIL", rem]]
        keep.append(f"Former Supervisor, {org}"); cat = "referee_dob_id"
    elif k == 2:  # first name alone in prose
        ad = _addr(r)
        text = (f"Name: {name}\nContact: {phone} / {em}\nAddress: {ad}\n\n## Profile\n{first} {duty} as {t} at {org}.\n\n"
                f"## Experience\n- {job_line}\n\n## Education\n- {q}, {qy}\n")
        pii += [["PERSON", first], ["ADDRESS", ad]]
        keep = [job_line, f"{duty} as {t} at {org}", f"{q}, {qy}"]; cat = "first_name_in_prose"
    elif k == 3:  # employer carries family name (kept by policy)
        fam = r.choice(TEST_POOLS["employer_family"])
        name = f"{first} {fam}"
        used.add(name)
        em, form_em = _email(r, name)
        pii = [["PERSON", name], ["PHONE", phone], ["EMAIL", em]]
        y0 = int(yrs[:4])
        emp = f"Accounts Clerk, {fam} & Sons Hardware Ltd, {y0 - 4}-{y0}"
        text = f"# {name}\nPhone: {phone} | Email: {em}\n\n## Experience\n- {emp}: reconciled supplier invoices.\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        keep = [emp, job_line, duty, f"{q}, {qy}"]; cat = "family_business_employer"
    elif k == 4:  # spelled-out email
        text = f"# {name}\nReach me: {em}, or {phone} (WhatsApp)\n\n## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n"
        cat = "obfuscated_email"
    elif k == 5:  # cover-letter prose, third person
        ad = _addr(r)
        mentor = _person(r, used)
        text = (f"My name is {name} and I live at {ad}. You can reach me on {phone} or at {em}.\n\n"
                f"I have worked as {t} at {org} since {yrs[:4]}, where I {duty}.\n\nMy mentor, Dr. {mentor}, encouraged me to apply.\n\n"
                f"## Qualifications\n- {q}, {qy}\n")
        pii += [["ADDRESS", ad], ["PERSON", mentor]]
        keep = [f"{t} at {org} since {yrs[:4]}", duty, f"{q}, {qy}"]; cat = "inline_prose_third_party"
    else:  # repeated identifiers
        text = (f"# {name}\nEmail: {em}\nPhone: {phone}\n\n## Experience\n- {job_line}: {duty}.\n\n## Education\n- {q}, {qy}\n\n"
                f"## Contact\nFor references, write to {em} or call {phone}.\n")
        cat = "repeated_identifiers"
    return {"category": cat, "text": text, "pii": pii, "keep": keep,
            "form": {"name": name, "email": form_em, "phone": phone}}


def no_pii(i: int, r: random.Random) -> dict:
    t, org, duty, _ = _job(r)
    ref = f"CD-{r.randint(2019, 2026)}-{r.randint(100, 999)}-{r.randint(1000, 9999)}"
    text = (f"# Vacancy notice extract\nVacancy ref: {ref}\nPosition: {t}, {org}\n"
            f"Duties: {duty}.\nRequirements: {r.choice(QUALS)} or equivalent; two years' experience.\n")
    return {"category": "no_pii", "text": text, "pii": [], "keep": [f"Vacancy ref: {ref}", f"{t}, {org}", duty], "form": None}


def build() -> dict:
    r = random.Random(SEED)
    used: set = set()
    raw = [layout(i, r, used) for i in range(N_PII_DOCS)] + [no_pii(i, r) for i in range(N_NO_PII_DOCS)]
    docs = []
    for n, d in enumerate(raw, 1):
        spans = find_spans(d["text"], d["pii"])
        expected = redact(d["text"], spans)
        for k in d["keep"]:
            if k not in d["text"] or k not in expected:
                raise ValueError(f"B{n:02d}: keep anchor lost by the answer key: {k!r}")
        docs.append({"id": f"B{n:02d}", "category": d["category"], "text": d["text"], "spans": spans,
                     "expected": expected, "keep": d["keep"], "form": d["form"]})
    body = {"policy": POLICY, "docs": docs}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"benchmark_version": BENCH_VERSION, "split": "test (held out: never train, tune prompts or pick examples on it)",
            "seed": SEED, "provenance": "Synthetic, rendered from fictional field values; labels derived from those values, not by a model.",
            "sha256": digest, **body}


if __name__ == "__main__":
    b = build()
    (Path(__file__).resolve().parent / "data" / "resume_redaction_test_v1.json").write_text(json.dumps(b, indent=2, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print(len(b["docs"]), "docs", Counter(d["category"] for d in b["docs"]))
    print("spans", sum(len(d["spans"]) for d in b["docs"]), Counter(s["type"] for d in b["docs"] for s in d["spans"]))
    print("sha256", b["sha256"])
```

## Appendix C: `tier1/shared/resume_redaction/redaction_eval.py`

```python
"""Shared resume-redaction evaluation (Day 1 T1-05 baseline, Day 3 reuse).

Scores outputs against the synthetic answer key, runs the release checks, applies the per-document
stop rule, summarises, saves runs, and (for live runs) calls the existing chat backend through
civicdesk_lab. Stdlib only; civicdesk_lab and transformers are imported lazily.
"""
from __future__ import annotations

import difflib
import json
import math
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "data" / "teaching_set_v1.json"
BENCH_PATH = HERE / "data" / "resume_redaction_test_v1.json"
REPLAY_PATH = HERE / "data" / "illustrative_outputs_teaching_v1.json"
BASELINE_DIR = HERE / "baselines"
PROMPT_VERSION = "redact-prompt-v1"
PLACEHOLDER_RE = re.compile(r"\[(PERSON|EMAIL|PHONE|ADDRESS|DOB|ID)\]")

# --- release checks (deliberately simple; each has false positives and false negatives) -------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b")
ID_RE = re.compile(r"\b[A-Z]{2}-ID-\d{4}-\d{3,}\b")


def load_fixture(path: Path = FIXTURE_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_benchmark(path: Path = BENCH_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_replay(path: Path = REPLAY_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_run(run: dict, name: str) -> Path:
    """Save a run (synthetic text only). Never point this at real documents: it stores outputs verbatim."""
    BASELINE_DIR.mkdir(exist_ok=True)
    p = BASELINE_DIR / f"{name}.json"
    p.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def load_run(name: str) -> dict:
    return json.loads((BASELINE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def release_checks(output: str, form: dict | None) -> list[str]:
    """Return the names of checks that fired on a redacted output. Empty list is NOT proof of safety."""
    fired = []
    if output is None or not output.strip():
        return ["empty_output"]
    if EMAIL_RE.search(output):
        fired.append("email_pattern")
    if PHONE_RE.search(output):
        fired.append("phone_pattern")
    if ID_RE.search(output):
        fired.append("id_pattern")
    if form:
        low = output.lower()
        if form.get("email") and form["email"].lower() in low:
            fired.append("known_email")
        if form.get("phone") and _digits(form["phone"])[-7:] in _digits(output):
            fired.append("known_phone")
        if form.get("name"):
            parts = [p for p in re.split(r"[\s-]+", form["name"]) if len(p) >= 4]
            hits = [p for p in parts if re.search(rf"\b{re.escape(p)}\b", output)]
            if hits:
                fired.append("known_name_part:" + "/".join(hits))
    return fired


def score_doc(doc: dict, output: str | None) -> dict:
    """Compare one output with the answer key. Needs the key, so this is evaluation, not a live check."""
    out = output or ""
    missed = [s for s in doc["spans"] if s["text"] in out]
    lost_keep = [k for k in doc["keep"] if k not in out]
    n_ph_expected = len(PLACEHOLDER_RE.findall(doc["expected"]))
    n_ph_output = len(PLACEHOLDER_RE.findall(out))
    # unrelated edits: diff against the expected redaction, ignoring placeholder tokens
    a = PLACEHOLDER_RE.sub("§", doc["expected"]).split()
    b = PLACEHOLDER_RE.sub("§", out).split()
    edits = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        exp, got = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if any(m["text"] in got for m in missed) and "\u00a7" in exp:
            kind = "leak"
        elif got.count("\u00a7") > exp.count("\u00a7"):
            kind = "over_redaction"
        elif tag == "delete" and i2 == len(a):
            kind = "truncation"
        else:
            kind = "unrelated_edit"
        edits.append({"kind": kind, "expected": exp, "got": got})
    kinds = {e["kind"] for e in edits}
    return {
        "id": doc["id"],
        "spans_total": len(doc["spans"]),
        "spans_missed": [{"type": s["type"], "text": s["text"]} for s in missed],
        "leaked": bool(missed),
        "keep_lost": lost_keep,
        "extra_placeholders": max(0, n_ph_output - n_ph_expected),
        "over_redacted": n_ph_output > n_ph_expected or "over_redaction" in kinds,
        "truncated": "truncation" in kinds,
        "unrelated_edit": "unrelated_edit" in kinds,
        "edits": edits,
        "empty": not out.strip(),
        "acceptable": not (missed or lost_keep or edits or not out.strip()),
    }


def route(fired: list[str], output: str | None, doc: dict, latency_s: float | None = None,
          timeout_s: float = 30.0) -> tuple[str, list[str]]:
    """Per-document stop rule. Uses only what is available at run time (no answer key)."""
    reasons = list(fired)
    out = output or ""
    if not out.strip():
        reasons.append("empty_output")
    elif len(out) < 0.6 * len(doc["text"]):
        reasons.append("output_much_shorter_than_input (possible truncation)")
    if latency_s is not None and latency_s > timeout_s:
        reasons.append("timeout")
    return ("HOLD for authorised review" if reasons else "pass checks (not proof of safety)"), reasons


def evaluate(fixture: dict, outputs: dict[str, str], latencies: dict[str, float] | None = None) -> list[dict]:
    rows = []
    for doc in fixture["docs"]:
        out = outputs.get(doc["id"])
        sc = score_doc(doc, out)
        fired = release_checks(out, doc.get("form"))
        decision, reasons = route(fired, out, doc, (latencies or {}).get(doc["id"]))
        sc.update({"checks_fired": fired, "decision": decision, "reasons": reasons})
        rows.append(sc)
    return rows


def summary_table(fixture: dict, rows: list[dict]) -> dict:
    types: dict[str, dict[str, int]] = {}
    for doc, r in zip(fixture["docs"], rows):
        if r["empty"]:
            continue  # empty or failed outputs are reported as not scored, never as "nothing leaked"
        missed_texts = {(m["type"], m["text"]) for m in r["spans_missed"]}
        for s in doc["spans"]:
            t = types.setdefault(s["type"], {"total": 0, "missed": 0})
            t["total"] += 1
            t["missed"] += (s["type"], s["text"]) in missed_texts
    docs_with_pii = [r for r in rows if r["spans_total"] > 0 and not r["empty"]]
    held = [r for r in rows if r["decision"].startswith("HOLD")]
    leaked = [r for r in rows if r["leaked"]]
    total = sum(t["total"] for t in types.values())
    missed = sum(t["missed"] for t in types.values())
    return {
        "docs_not_scored (empty or failed)": [r["id"] for r in rows if r["empty"]],
        "spans_total": total,
        "spans_missed": missed,
        "span_recall": round((total - missed) / total, 3) if total else None,
        "recall_by_type": {k: f"{v['total'] - v['missed']}/{v['total']}" for k, v in sorted(types.items())},
        "docs_with_pii": len(docs_with_pii),
        "docs_leaked": len(leaked),
        "doc_leak_rate": f"{len(leaked)}/{len(docs_with_pii)}",
        "docs_over_redacted": [r["id"] for r in rows if r["over_redacted"]],
        "docs_truncated_or_empty": [r["id"] for r in rows if r["truncated"] or r["empty"]],
        "docs_with_unrelated_edits": [r["id"] for r in rows if r["unrelated_edit"]],
        "acceptable_as_is": [r["id"] for r in rows if r["acceptable"]],
        "held": [r["id"] for r in held],
        "silent_leaks (leaked but passed checks)": [r["id"] for r in leaked if not r["decision"].startswith("HOLD")],
        "false_holds (held, output was acceptable)": [r["id"] for r in held if r["acceptable"]],
        "note": "Span recall counts text that was cut off as removed. Read it beside truncation.",
    }


EXAMPLE_RULE = {
    "label": "EXAMPLE classroom acceptance rule, fixed before any run. Not a standard and not release permission.",
    "max_docs_with_contact_or_id_leak": 0,   # residual EMAIL, PHONE, ID or DOB in any document
    "max_docs_with_any_leak": 2,             # out of the documents that contain PII
    "max_docs_over_redacted_or_altered": 4,  # out of all documents
    "max_docs_empty_failed_or_truncated": 0,
    "max_p95_latency_s": 20.0,               # course GPU; replace with your own budget
}


def p95(values: list[float]) -> float | None:
    v = sorted(x for x in values if x is not None)
    if not v:
        return None
    return v[min(len(v) - 1, math.ceil(0.95 * len(v)) - 1)]


def check_rule(rows: list[dict], latencies: dict[str, float] | None, rule: dict = EXAMPLE_RULE) -> dict:
    """Apply a predeclared rule to one scored run. Returns each criterion with its value and verdict."""
    hard = {"EMAIL", "PHONE", "ID", "DOB"}
    contact = sum(any(m["type"] in hard for m in r["spans_missed"]) for r in rows if not r["empty"])
    anyleak = sum(r["leaked"] for r in rows if not r["empty"])
    altered = sum(r["over_redacted"] or r["unrelated_edit"] for r in rows)
    broken = sum(r["empty"] or r["truncated"] for r in rows)
    lat = p95(list((latencies or {}).values()))
    crit = [
        ("docs with residual email/phone/ID/DOB", contact, contact <= rule["max_docs_with_contact_or_id_leak"]),
        ("docs with any leaked span", anyleak, anyleak <= rule["max_docs_with_any_leak"]),
        ("docs over-redacted or altered", altered, altered <= rule["max_docs_over_redacted_or_altered"]),
        ("docs empty, failed or truncated", broken, broken <= rule["max_docs_empty_failed_or_truncated"]),
        ("p95 latency (s)", lat, lat is not None and lat <= rule["max_p95_latency_s"]),
    ]
    return {"rule": rule["label"], "criteria": crit, "meets_rule": all(c[2] for c in crit)}


def upper_bound_95(failures: int, n: int) -> float:
    """One-sided exact (Clopper-Pearson) 95% upper bound on a failure rate.
    Valid only if the n items are a random sample from the population you care about."""
    if n <= 0:
        raise ValueError("n must be positive")
    if failures >= n:
        return 1.0
    if failures == 0:
        return 1 - 0.05 ** (1 / n)

    def cdf(p: float) -> float:
        return sum(math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(failures + 1))

    lo, hi = failures / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) > 0.05:
            lo = mid
        else:
            hi = mid
    return hi


def cost_per_acceptable(rows: list[dict], *, compute_cost_per_doc: float,
                        review_minutes_per_hold: float, reviewer_cost_per_hour: float) -> dict:
    """Scoped cost per acceptable answer for ONE run: (compute + review time on held docs) / docs
    acceptable as-is. Every input is the caller's own figure; nothing here is a measured price.
    Leaves out engineering, data preparation, audits and the cost of a leak that got through."""
    n = len(rows)
    holds = sum(r["decision"].startswith("HOLD") for r in rows)
    ok = sum(r["acceptable"] for r in rows)
    total = n * compute_cost_per_doc + holds * review_minutes_per_hold / 60 * reviewer_cost_per_hour
    return {"docs": n, "held": holds, "acceptable_as_is": ok, "run_cost": round(total, 2),
            "cost_per_acceptable": round(total / ok, 2) if ok else None,
            "scope": "compute + review of held docs only; excludes build, audit and leak costs"}


# --- optional live run through the existing backend -----------------------------------------
SYSTEM_PROMPT = (
    "You redact personal data from CVs. Replace each of these with its placeholder: "
    "names of private individuals [PERSON], email addresses including spelled-out ones [EMAIL], "
    "phone numbers [PHONE], home addresses [ADDRESS], dates of birth [DOB], ID numbers [ID]. "
    "Keep employer and institution names, job titles, dates of employment, qualifications, skills "
    "and reference numbers exactly as written. Change nothing else. Return only the redacted text."
)


def run_live(fixture: dict, which: str = "olmo", timeout_s: float = 30.0) -> dict:
    """Send each synthetic doc to the backend chosen in T1-01. Only 'live' replies count as measured.

    civicdesk_lab.chat() falls back to canned demo text on errors; those replies are recorded as
    errors (empty output), never scored as model behaviour.
    """
    import civicdesk_lab as lab  # lazy on purpose: replay mode needs no backend

    model = lab.resolve_model(which)
    outputs, latencies, notes, usage = {}, {}, {}, {}
    for doc in fixture["docs"]:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": doc["text"]}]
        try:
            res = lab.chat(msgs, model=model, timeout=timeout_s)
        except Exception as exc:  # fallback_to_demo=False raises
            res = {"ok": False, "mode": "error", "text": "", "latency_ms": int(timeout_s * 1000), "error": str(exc)}
        if res.get("mode") != "live":
            outputs[doc["id"]] = ""
            notes[doc["id"]] = f"not measured: mode={res.get('mode')} {res.get('error', '')}".strip()
        else:
            outputs[doc["id"]] = res["text"]
            notes[doc["id"]] = "live"
            raw = res.get("raw") or {}
            if isinstance(raw, dict) and raw.get("usage"):
                usage[doc["id"]] = raw["usage"]  # present once the server returns usage (T1-03 spec)
        latencies[doc["id"]] = round(res.get("latency_ms", 0) / 1000, 2)
    return {
        "model": model,
        "backend": lab.endpoint_config()["backend"],
        "prompt_version": PROMPT_VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "benchmark_version": fixture.get("benchmark_version") or fixture.get("fixture_version"),
        "generation": "temperature 0, max_tokens 256 (civicdesk_lab defaults)",
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "usage_from_server": usage,
        "fixture_sha256": fixture["sha256"],
        "outputs": outputs,
        "latency_s": latencies,
        "notes": notes,
        "measured": all(v == "live" for v in notes.values()),
    }


def count_tokens(texts: dict[str, str], model_dir: str | None = None) -> dict[str, int] | None:
    """Count tokens with the OLMo tokenizer from the folder already in the image (no weights loaded).
    The course server returns no usage figures, so this is how tokens are measured. Returns None if
    transformers or the folder is unavailable."""
    try:
        from transformers import AutoTokenizer
    except Exception:
        return None
    import os

    path = model_dir or os.environ.get(
        "CIVICDESK_TOKENIZER_DIR", os.path.join(os.environ.get("CIVICDESK_MODELS_DIR", "/models"), "olmo"))
    try:
        tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
    except Exception:
        return None
    return {k: len(tok.encode(v or "", add_special_tokens=False)) for k, v in texts.items()}
```

## Appendix D: `tier1/shared/resume_redaction/data/illustrative_outputs_teaching_v1.json`

Hand-written outputs, not produced by any model. Copy verbatim.

```json
{
  "label": "ILLUSTRATIVE - author-written outputs, NOT produced by any model. Each shows one failure type so the scorer and stop rule have something to catch.",
  "fixture_sha256": "39c0e0ea82d2ef8783bc9ffa4e145c0803a7d5b394c2af57adad65bef059e7f2",
  "what_each_shows": {
    "R01": "correct",
    "R02": "referee phone and email left in (leak a pattern check catches)",
    "R03": "first name left in prose (leak only the known-name check catches) plus an unrelated edit: 30% became 40%",
    "R04": "over-redaction: employer name masked",
    "R05": "spelled-out email left in (silent leak: no check fires)",
    "R06": "output cut off mid-sentence (truncation)",
    "R07": "correct, but the reference number trips the phone pattern (false hold)"
  },
  "outputs": {
    "R01": "# [PERSON]\nEmail: [EMAIL] | Phone: [PHONE]\nAddress: [ADDRESS]\n\n## Experience\n- Records Officer, CivicDesk Central Registry, 2019-2025: indexed 12,000 files a year.\n\n## Education\n- BSc Information Management, University of Fictionville, 2018\n\n## Skills\nRetention schedules, EDMS indexing, spreadsheets\n",
    "R02": "# Curriculum vitae: [PERSON]\nDate of birth: [DOB]\nNational ID: [ID]\nEmail: [EMAIL]\n\n## Experience\n- Lands Clerk, CivicDesk Lands Office, 2017-2024: processed survey plan requests.\n\n## Referees\n- [PERSON], Former Supervisor, CivicDesk Lands Office, 868-555-0177, g.ramsaran@example.invalid\n",
    "R03": "Name: [PERSON]\nContact: [PHONE] / [EMAIL]\nAddress: [ADDRESS]\n\n## Profile\nOyelaran built the service-desk queue dashboard and reduced average queue time by 40%.\n\n## Experience\n- ICT Support Officer, CivicDesk Trade Unit, 2020-2025\n",
    "R04": "# [PERSON]\nPhone: [PHONE] | Email: [EMAIL]\n\n## Experience\n- Accounts Clerk, [PERSON] & Sons Hardware Ltd, 2016-2021: reconciled supplier invoices.\n- Accounts Officer, CivicDesk Finance Unit, 2021-2025\n\n## Education\n- ACCA Applied Knowledge, 2019\n",
    "R05": "# [PERSON]\nReach me: rajiv dot persaud at example dot invalid, or [PHONE] (WhatsApp)\n\n## Experience\n- Data Entry Clerk, CivicDesk Permits Office, 2022-2025: keyed 300 permit forms a week.\n",
    "R06": "My name is [PERSON] and I live at [ADDRESS]. You can reach me on [PHONE].\n\nI have worked as a Health Records",
    "R07": "# Vacancy notice extract\nVacancy ref: CD-2024-117-3302\nPosition: Records Assistant, CivicDesk Central Registry\nRequirements: diploma in records management or equivalent; two years' experience.\n"
  }
}
```
