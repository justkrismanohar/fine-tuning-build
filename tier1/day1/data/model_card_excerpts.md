# Model card excerpts (classroom copy)

Frozen for this course. Always read the live model card before a later project. These lines are enough for T1-04.

## allenai/OLMo-2-0425-1B-Instruct (primary)

- **Revision used in this course:** 48d788eca847d4d7548f375ad03d3c9312f6139e.
- **Licence as stated on the card:** "OLMo 2 is licensed under the Apache 2.0 license." The model repo has no separate LICENSE or NOTICE file, so `licences/apache-2.0/LICENSE-2.0.txt` is the text.
- **Also on the card:** "OLMo 2 is intended for research and educational use. For more information, please see our Responsible Use Guidelines." Those guidelines are a separate document (`licences/olmo-2-0425-1b-instruct/`).
- **What Ai2 publishes:** weights, code, training data mixtures and recipes. That lets you audit what went in. It does not let you explain why the model wrote one particular sentence.
- **Openness:** an open-weight model under an OSI-approved licence, with training data published. Whether the whole system meets the OSI Open Source AI Definition is a separate check (data information, code and parameters, each under OSI-approved terms), not something the word "Apache" settles.
- **Use in class:** default chat model on vLLM.

## microsoft/Phi-4-mini-instruct (comparison)

- **Revision used in this course:** cfbefacb99257ffa30c83adab238a50856ac3083.
- **Licence:** MIT (LICENSE file in the repo). NOTICE.md lists a third-party component (flash-attention, BSD 3-Clause). The card's Trademarks section limits use of Microsoft marks.
- **Openness:** open-weight under a permissive licence. Training data is described in the card, not published as a dataset you can download.
- **Use in class:** comparison only. Same prompt, same CivicDesk text.

## Closed products named in the wider programme (not called in this lab)

ChatGPT, Claude, Grok as a *service*: you see the output. You do not get weights or training data. Metered, often in foreign currency. Fine for a draft that is not a record. Not the CivicDesk endpoint.

## meta-llama/Llama-3.2-1B-Instruct (licence comparison only, not run in class)

- **Revision checked:** 9213176726f574b556790deb65791e0c5aa438b6 (gated on Hugging Face: you accept Meta's terms before download).
- **Licence:** Llama 3.2 Community License Agreement plus the Llama 3.2 Acceptable Use Policy, which the licence incorporates by reference. Not an OSI-approved licence.
- **Text only:** the model card describes the 1B and 3B models as "text in/text out".
- **Use in class:** the licence you read in the scavenger hunt.

## Families you will hear about (not extra labs)

Mistral, Gemma, Llama, Qwen each publish several models, and the licence can differ by model and by version inside one family. Always read the licence for the exact model and revision. Ollama and vLLM are runtimes, not models: they have their own software licences and do not change the model's licence.
