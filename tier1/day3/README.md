# Tier 1 Day 3 — prove the prompt fails, then train and compare live

A well-prompted 1B OLMo still fails on frozen CivicDesk cases. Learners re-run that baseline on this machine, inspect training data, train a real LoRA with `TrainSession`, save an adapter, and compare base vs adapter live (`disable_adapter`).

Each notebook starts with:

```python
BACKEND = "olmo"  # "olmo" | "phi" | "demo"
```

Default is **local OLMo** (`:8000`). Phi is `:8001`. **demo** uses RECORDED files only — not scored as this session.

## Order of play

| File | When |
|---|---|
| `T1-11_dataset_and_frozen.ipynb` | 9:00–10:30 AM pre-flight → hunt → train → load → see the difference |
| `T1-12_base_vs_adapter.ipynb` | 10:45 AM–12:00 PM full criteria scoreboard + redaction |
| `T1-12b_risk_cells.ipynb` | 12:45–1:30 PM risk cells citing this session's artifacts |
| `T1-13_agentic_boundary.ipynb` | 1:30–2:15 PM ticket train + score + tool gate |
| `T1-14_defence_and_transfer.ipynb` | 2:15–2:55 PM policy, minutes stretch, transfer card |

## What is scored

| Task | Priority | Labels / output | Held-out |
|---|---|---|---|
| Résumé **criteria** | headline | `meets` / `does_not_meet` / `human_review` | 18 items on 7 CVs |
| IT **tickets** | Track A | category / action / urgency | 9 tickets |
| Résumé **redaction** | aligned with T1-05 | HOLD / PASS CHECKS | 40-document Day 1 file |
| **Minutes** | stretch | actions / not_agreed / deferred | 4 excerpts (no adapter) |

## Machinery

- `ft_train.py` — `TrainSession`, `load_adapter`, `compare_live`, scoreboards
- `train_adapter.py` — thin CLI for instructor bake
- `civicdesk_ft.py` — inspect, pre-flight, hunt, tool gate, redactor wrapper
- `write_day3_notebooks.py` — regenerates the five notebooks
- `adapters/` — prebuilt LoRA folders after GPU bake (see `adapters/README.md`)
- `logs/recorded/` — measured fallback compares (see `logs/recorded/README.md`)

Redaction data: `../shared/resume_redaction/`. Measured base: `baselines/olmo_baseline_v1.json`. Measured adapter run: `baselines/olmo_adapter_v1.json` (after bake).

Do not run `build_day3_notebooks.py`. Image already pins `peft==0.14.0`.
