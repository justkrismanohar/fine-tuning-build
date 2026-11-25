# Tier 1 Day 3

Prove that a careful prompt still fails, inspect training data, train a small LoRA, then compare base vs adapter.

```python
BACKEND = "olmo"  # "olmo" | "phi" | "demo"
```

Default is local OLMo on `:8000`. Use `demo` when there is no GPU / no server — notebooks fall back to RECORDED files when those exist.

## Main path

| File | Topic |
|---|---|
| `T1-11_dataset_and_frozen.ipynb` | Pre-flight → hunt → train → load → see the difference |
| `T1-12_base_vs_adapter.ipynb` | Full criteria scoreboard + redaction |
| `T1-12b_risk_cells.ipynb` | Risk cells tied to this session’s artifacts |

## Optional (same day, if time)

| File | Topic |
|---|---|
| `optional/T1-13_agentic_boundary.ipynb` | Ticket train + score + tool gate |
| `optional/T1-14_defence_and_transfer.ipynb` | Policy line, minutes stretch, transfer card |

## Helpers

- `ft_train.py` — `TrainSession`, `load_adapter`, `compare_live`
- `train_adapter.py` — instructor bake CLI
- `civicdesk_ft.py` — inspect, pre-flight, hunt, tool gate
- `write_day3_notebooks.py` — regenerates the notebooks
- `adapters/` — prebuilt LoRAs after a GPU bake
- `logs/recorded/` — measured fallback compares

Redaction data lives under `../shared/resume_redaction/`. Do not run `build_day3_notebooks.py`.
