# Tier 1 Day 3 — fine-tune literacy (inspect, do not train)

Inspect a CivicDesk training set and a pretend adapter. Operating questions: burst vs standing, licence, rollback, bounded agency. Instruction is in the notebooks. No slide deck.

You do **not** run a LoRA job. No GPU required.

## Order of play

| File | When |
|---|---|
| `T1-11_dataset_and_frozen.ipynb` | 09:00–10:30 architecture (frozen vs adapter, burst vs standing) + SFT rows + canaries |
| `T1-12_base_vs_adapter.ipynb` | 10:45–12:00 same prompt, frozen base vs pretend adapter |
| `T1-12b_risk_cells.ipynb` | 12:45–13:30 rollback, licence inheritance, PII-in-train |
| `T1-13_agentic_boundary.ipynb` | 13:30–14:15 saying vs doing; allowlist |
| `T1-14_defence_and_transfer.ipynb` | 14:15–14:55 first safe next step, not a pilot |

## Other files

`civicdesk_ft.py`, `data/sft_rows.jsonl`, `data/adapter_stub.json`, `images/`, `cards/`, `completed/`, `day3_quick_card.md`.

Auxiliary workshops after this day: `course/auxiliary/` (no GPU).
