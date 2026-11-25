# Colab track

Same CivicDesk labs as `tier1/`, set up so you can open them in Google Colab without Docker.

**GPU note:** Colab does not run the Docker Hub image. On a CPU runtime you still do the notebooks, but chat cells use scripted demo replies — you are not talking to a live local OLMo. Day 3 training needs a GPU (switch **Runtime → T4**, or those cells skip). For the live model from the image, use Docker on a machine that has a GPU — see the [course README](../README.md).

Day 2 does not need a model either way.

**Runtime → CPU (or T4) → Run all.** The first cell finds or clones the course.

Prep (how to click Run, a bit of Python): [`../prep/README.md`](../prep/README.md).  
Optional data-cleaning notebooks: [`../tier1/data_cleaning/README.md`](../tier1/data_cleaning/README.md).  
Full Docker / local path: [`../README.md`](../README.md).

## Open in Colab

### Day 1

| Notebook | Colab |
|---|---|
| T1-01a hosting picture | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-01a_build_from_scratch.ipynb) |
| T1-01 first call | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-01_first_call.ipynb) |
| T1-02 tokens | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-02_tokens_and_transformer.ipynb) |
| T1-03 SLM vs LLM | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day1/T1-03_slm_vs_llm.ipynb) |
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

### Day 3

| Notebook | Colab |
|---|---|
| T1-11 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-11_dataset_and_frozen.ipynb) |
| T1-12 | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-12_base_vs_adapter.ipynb) |
| T1-12b | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-12b_risk_cells.ipynb) |
| T1-13 (optional) | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-13_agentic_boundary.ipynb) |
| T1-14 (optional) | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/colab/day3/T1-14_defence_and_transfer.ipynb) |

### Optional data cleaning

| Notebook | Colab |
|---|---|
| DC-01 Keep, throw, or send back | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/tier1/data_cleaning/DC-01_keep_or_throw.ipynb) |
| DC-02 Clean a page, then label it | [Open](https://colab.research.google.com/github/justkrismanohar/fine-tuning-build/blob/main/tier1/data_cleaning/DC-02_clean_then_label.ipynb) |

You can also upload a notebook at [colab.research.google.com](https://colab.research.google.com/) → **File → Upload notebook**. The first cell still needs network to clone the repo unless `course/` is already on the runtime.

Stuck? Open that day’s `completed/` copy only, and mark it as loaded from reference.

## What Colab is not

You practised the ideas. You did not deploy OLMo on this laptop. For a live local API, use Docker — see the [course README](../README.md).

## Rebuild (maintainers)

From this folder, after you change a `tier1/` notebook:

```text
python build_colab_tier1.py
```
