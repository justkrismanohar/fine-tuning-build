# Day 3 quick card

Keep this on the desk. One page.

## Backend (every notebook)

```python
BACKEND = "olmo"  # "olmo" | "phi" | "demo"
```

Local OLMo is the default (`:8000`). Demo / no GPU = **RECORDED** files, not this session.

## Data ban

Same as Days 1–2. Frozen held-out cases in `heldout/cases.py` are a **test** set. The canary national ID and CivicDesk FT-08 / FT-09 must never enter a real train split. Never edit the 40-document redaction test file. Hunt answers are in `train_issues_key_v1.json` — do not open it before scoring yourself.

## Labels

**Criteria (headline):** `meets` / `does_not_meet` / `human_review`. Silence is `human_review`, never `does_not_meet`.

**Redaction:** per document **HOLD** or **PASS CHECKS**. Per run: **meets** or **does not meet** the example rule.

## Train → save → compare

```python
session = ft_train.TrainSession(task="criteria", targets=TARGETS, rank=RANK)
session.step(1)          # rerun continues
session.save("adapters/my_criteria_run")
model = ft_train.load_adapter(ADAPTER, task="criteria")
ft_train.compare_live(model, "criteria")   # base = disable_adapter()
```

Rollback = `disable_adapter()` or stop loading that directory.

An adapter is **not** RAG and **not** the register.

## Burst vs standing

Burst = training job, then stop the extra GPU.  
Standing = chat API that stays up (`:8000` / `:8001`).

## Bounded agency

ALLOWED: draft a ticket, quote a handbook, draft a redacted copy (a person releases it).  
BANNED: reset password, write GLPI, award, scrape for negotiation, hire, publish a grade, release to panel, auto-release if PASS CHECKS.

Unknown tool → banned until listed.

## Policy line

AI assists. HR validates. Authorized officers decide.

## Transfer

`cards/transfer_card.md` — first **safe** next step, not a pilot.

## If stuck

Load `completed/` for **this** notebook only. Use RECORDED compares if the GPU is down. Do not reuse briefing-note percentages as this machine's score.
