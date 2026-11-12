# Model card excerpts (classroom copy)

Frozen for this course, subject to UNDP / MPAAI confirmation. Read the live card before any later project. These lines are enough for T1-04.

## allenai/OLMo-2-0425-1B-Instruct (primary)

- **What you get:** weights, code, data mixtures (Dolma lineage), configs, checkpoints.
- **Size:** 1B-class instruct model. Small enough for a classroom LoRA in Tier 2.
- **Licence (weights/code as published by Ai2):** Apache-2.0. Confirm the card on the day.
- **Openness:** treated here as an **OSAID-style candidate** — you can inspect what went into training, not only the file you run.
- **Use in class:** default chat model on vLLM.

## microsoft/Phi-4-mini-instruct (comparison)

- **What you get:** weights and a model card. Training data is **not** a public replica of OLMo’s Dolma package.
- **Size:** compact; relevant where a ministry already lives on Microsoft / Azure.
- **Licence:** MIT for the model as published by Microsoft. Confirm the card on the day.
- **Openness:** **open-weight**. Not treated here as a complete-system OSAID model.
- **Use in class:** comparison only. Same prompt, same CivicDesk text.

## Closed products named in the wider programme (not called in this lab)

ChatGPT, Claude, Grok as a *service*: you see the output. You do not get weights or training data. Metered, often in foreign currency. Fine for a draft that is not a record. Not the CivicDesk endpoint.

## Families on the T1-04 licence card (not extra labs)

Mistral, Gemma, Llama, Qwen, Ollama — locate them (open-weight vs community licence vs toolkit). vLLM is the shared-server path in class. Ollama is a typical laptop path. Do not install them today.
