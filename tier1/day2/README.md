# Tier 1 Day 2 — retrieve before you change weights

Retrieve from an approved CivicDesk set, cite it, refuse when the source is missing. Instruction is in the notebooks. No slide deck.

Day 1 started the model. This day does **not** train. Normal operation sends retrieved text through the Day 1 client (`civicdesk_lab.chat`). If the backend is demo or down, notebooks continue with a labelled local cite-or-abstain helper; those replies are **not scored as model performance**. Download this folder and run it locally before the workshop if the hosted notebook can lose its host.

## Order of play

| File | When |
|---|---|
| `T1-06_intervention_map.ipynb` | 09:00–09:20 (group) label prompt / RAG / integration / fine-tune / none |
| `T1-07_data_classification.ipynb` | 09:20–10:30 INDEX vs NEVER |
| `T1-08_build_rag.ipynb` | 10:45–12:00 retrieve, then generate |
| `T1-09_prompt_vs_rag.ipynb` | 12:45–13:45 invented circular vs cited paragraph vs abstain |
| `T1-10_access_and_governance.ipynb` | 13:45–14:20 (group) hit ≠ permission |
| `T1-10b_decision_card.ipynb` | 14:20–14:55 (group) + overnight cite-or-abstain card |

## Other files

`civicdesk_rag.py`, `data/`, `images/`, `cards/`, `completed/`, `day2_quick_card.md`, `make_replays.py`, `logs/replay/`.

Required offline path: Python 3 with the Day 1 helper (`../day1/civicdesk_lab.py`), the files in this folder, and no API key, GPU, vector service or OCR install. Set `CIVICDESK_MODE=demo` (the Day 1 default). A Colab or JupyterHub tab is not a substitute for this package if that host disappears.

If you are stuck, load `completed/` for **this** notebook only and mark it as loaded from reference.
