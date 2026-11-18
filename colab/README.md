# Tier 1 — Colab track (no Docker, no GPU)

Two copies of the same course:

| Track | Where | Live OLMo/Phi? |
|---|---|---|
| **Docker / local** | [`tier1/`](../tier1/) + [course README](../README.md) | Yes, if you start the servers |
| **Colab (this folder)** | Open the badges below | No. Chat cells use **scripted** `[OLMo demo]` / `[Phi-4-mini demo]` replies |

Days 2–3 never needed a model. Day 1 hosting (T1-01a) is **walked through with simulated output** so you still see check → weights → API door, without downloading GB of weights.

**Runtime → CPU → Run all.** First cell clones this repo (or uses the folder if it is already on the machine).

Prep (Python literacy, Colab) is separate: [`../prep/README.md`](../prep/README.md). Optional government data-cleaning notebooks (self-run, CPU): [`../tier1/data_cleaning/README.md`](../tier1/data_cleaning/README.md).

## Open in Colab

### Day 1

| Notebook | Colab |
|---|---|
| T1-01a hosting picture (simulated) | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-01a_build_from_scratch.ipynb) |
| T1-01 first call | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-01_first_call.ipynb) |
| T1-02 tokens | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-02_tokens_and_transformer.ipynb) |
| T1-03 SLM vs LLM (scripted pair) | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-03_slm_vs_llm.ipynb) |
| T1-04 licences | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-04_openness_licences_gpu.ipynb) |
| T1-05 canvas | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-05_usecase_canvas.ipynb) |

### Day 2

| Notebook | Colab |
|---|---|
| T1-06 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day2/T1-06_intervention_map.ipynb) |
| T1-07 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day2/T1-07_data_classification.ipynb) |
| T1-08 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day2/T1-08_build_rag.ipynb) |
| T1-09 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day2/T1-09_prompt_vs_rag.ipynb) |
| T1-10 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day2/T1-10_access_and_governance.ipynb) |
| T1-10b | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day2/T1-10b_decision_card.ipynb) |

### Data cleaning (optional, not a contact-hour lab)

| Notebook | Colab |
|---|---|
| DC-01 Keep, throw, or send back | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/tier1/data_cleaning/DC-01_keep_or_throw.ipynb) |
| DC-02 Clean a page, then label it | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/tier1/data_cleaning/DC-02_clean_then_label.ipynb) |

### Day 3

| Notebook | Colab |
|---|---|
| T1-11 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-11_dataset_and_frozen.ipynb) |
| T1-12 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-12_base_vs_adapter.ipynb) |
| T1-12b | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-12b_risk_cells.ipynb) |
| T1-13 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-13_agentic_boundary.ipynb) |
| T1-14 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-14_defence_and_transfer.ipynb) |

Upload instead: [colab.research.google.com](https://colab.research.google.com/) → **File → Upload notebook**. The first cell still needs network to `git clone` unless the whole `course/` tree is already on the runtime.

Executed reference copies (scripted replies already filled in) live in each day’s `completed/` folder. If you are stuck, open **that** notebook only and mark it as loaded from reference.

## What you must not claim

You completed the **ideas**. You did **not** deploy OLMo. A live `/v1` on this laptop needs **Docker** (or the [own-environment](../03_own_environment.md) stack). Colab is not that.

## Rebuild (maintainers)

From this folder, after you change a `tier1/` notebook or `civicdesk_lab.py`:

```text
python build_colab_tier1.py
python execute_to_completed.py
```

Only Day 1 cells that would have called a model (or started vLLM) are rewritten. Days 2–3 are the same labs plus the Colab bootstrap cell.
