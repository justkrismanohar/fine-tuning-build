# Tier 1 Day 3 — prove the prompt fails, then inspect extra practice

A well-prompted 1B OLMo still fails on frozen CivicDesk cases. Learners **re-run that baseline on this machine**, inspect what a LoRA would be taught, and compare a small add-on if one is on disk. They do **not** have to train. Instruction is in the notebooks.

Each notebook starts with:

```python
BACKEND = "olmo"  # "olmo" | "phi" | "demo"
```

Default is **local OLMo** (`:8000`). Phi is `:8001`. **demo** uses labelled stand-ins and run files — not scored as model performance.

If the live call fails, the notebook continues from the labelled CPU cards / run files and says so. Do not paste briefing-note percentages as this session's score.

## Order of play

| File | When |
|---|---|
| `T1-11_dataset_and_frozen.ipynb` | 9:00–10:30 AM architecture + pre-flight + three failures + criteria rows |
| `T1-12_base_vs_adapter.ipynb` | 10:45 AM–12:00 PM criteria floor + redaction 40-doc compare |
| `T1-12b_risk_cells.ipynb` | 12:45–1:30 PM rollback, licence, PII-in-train |
| `T1-13_agentic_boundary.ipynb` | 1:30–2:15 PM saying vs doing; ticket Track A |
| `T1-14_defence_and_transfer.ipynb` | 2:15–2:55 PM policy line, minutes stretch, first safe next step |

## What is scored

| Task | Priority | Labels / output | Held-out |
|---|---|---|---|
| Résumé **criteria** | headline | `meets` / `does_not_meet` / `human_review` | 18 items on 7 CVs |
| IT **tickets** | Track A | category / action / urgency | 9 tickets |
| Résumé **redaction** | aligned with T1-05 | HOLD / PASS CHECKS; run meets / does not meet the example rule | 40-document Day 1 file **and** 7-CV stress slice |
| **Minutes** | stretch | actions / not_agreed / deferred | 4 excerpts |

Train criteria and redaction as **separate** tasks. Combined JSON is not the classroom target.

## Other files

`civicdesk_ft.py`, `heldout/` (frozen `cases.py` — do not train on it), `build_criteria_set.py`, `build_tickets_set.py`, `train_adapter.py`, `data/` (including `data/demo/` for no-GPU), `cards/`, `completed/`, `day3_quick_card.md`.

Redaction inspect/clean/val JSON lives in `../shared/resume_redaction/data/`. The measured base run is `../shared/resume_redaction/baselines/olmo_baseline_v1.json`. A measured adapter run `olmo_adapter_v1.json` is added when the instructor LoRA exists; until then notebooks read `data/demo/olmo_adapter_demo_v1.json` and label it **not scored**.

Do not run `build_day3_notebooks.py`. Image change (`peft`, baked adapter) is for Kris to approve.

Auxiliary workshops after this day: `course/auxiliary/` (no GPU).
