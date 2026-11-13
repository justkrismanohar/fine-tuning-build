---
dataset_info:
  features:
  - name: id
    dtype: string
  - name: messages
    list:
    - name: content
      dtype: string
    - name: role
      dtype: string
  - name: source
    dtype: string
  splits:
  - name: train
    num_bytes: 2575519262
    num_examples: 866138
  download_size: 1265029737
  dataset_size: 2575519262
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
---

Used to train OLMo 2 32B. From the [blog post](https://allenai.org/blog/olmo2-32B):
> Filtered out instructions from the SFT dataset and the chosen responses of the preference data that included mentions of a date cutoff from the synthetic data generation process. This resulted in a new version of the instruction dataset, Tulu 3 SFT Mixture 0225, and preference dataset, OLMo-2-32B-pref-mix-0325.
> We use majority voting to improve the quality of answers to our synthetic math questions. For our Persona MATH and Grade School Math datasets from Tülu 3, we only include prompts and completions where the model reaches a majority vote over 5 completions. New versions of the math and grade school math datasets are available.


Created with `open-instruct` data tools:
```
python scripts/data/filtering_and_updates/update_subsets.py \
    --base_ds allenai/tulu-3-sft-olmo-2-mixture-filter-datecutoff \
    --remove_sources ai2-adapt-dev/personahub_math_v5_regen_149960 allenai/tulu-3-sft-personas-math-grade \
    --add_ds allenai/tulu-3-sft-personas-math-filtered allenai/tulu-3-sft-personas-math-grade-filtered \
    --remove_keys prompt dataset \
    --push_to_hub \
    --repo_id allenai/tulu-3-sft-olmo-2-mixture-0225
```
