# Tier 1 Day 2 — retrieve before you change weights

Retrieve from an approved CivicDesk set, cite it, refuse when the source is missing. Instruction is in the notebooks. No slide deck.

Day 1 started the model. This day does **not** train. Default path needs no GPU (`civicdesk_rag.py` uses word-overlap retrieval and canned cite/abstain). Same notebooks on the [Colab track](../../colab/README.md) — Days 2–3 never called a live model.

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

`civicdesk_rag.py`, `data/`, `images/`, `cards/`, `completed/`, `day2_quick_card.md`.

If you are stuck, load `completed/` for **this** notebook only and mark it as loaded from reference.
