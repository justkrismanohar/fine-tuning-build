# Licence files for T1-04

Classroom copies of publisher texts. Not legal clearance. Recheck the live card and linked policy on the day you decide.

The spec’s `t1-04-licence-files/` pack was not attached with the brief. Files below were retrieved from the publishers on **13 November 2026** and checksummed in `SHA256SUMS`. If you later receive the original pack, replace this folder byte-for-byte and keep `SHA256SUMS` from that pack.

## Pins and sources

| Path | Source | Retrieved |
|---|---|---|
| `apache-2.0/LICENSE-2.0.txt` | https://www.apache.org/licenses/LICENSE-2.0.txt | 2026-11-13 |
| `olmo-2-0425-1b-instruct/MODEL_CARD_README.md` | Hugging Face `allenai/OLMo-2-0425-1B-Instruct` revision `48d788eca847d4d7548f375ad03d3c9312f6139e` | 2026-11-13 |
| `olmo-2-0425-1b-instruct/AI2_RESPONSIBLE_USE_GUIDELINES_2026-11-12.txt` | Extracted from https://allenai.org/responsible-use (“Last Updated: June, 2024”) | 2026-11-13 |
| `olmo-2-0425-1b-instruct/TULU3_SFT_MIXTURE_DATASET_CARD.md` | Hugging Face `allenai/tulu-3-sft-mixture` | 2026-11-13 |
| `olmo-2-0425-1b-instruct/TULU3_SFT_OLMO2_MIXTURE_0225_DATASET_CARD.md` | Hugging Face `allenai/tulu-3-sft-olmo-2-mixture-0225` | 2026-11-13 |
| `llama-3.2/LICENSE` | GitHub `meta-llama/llama-models` `models/llama3_2/LICENSE` (main, 2026-11-13) | 2026-11-13 |
| `llama-3.2/USE_POLICY_github_2024-09-25.md` | GitHub `models/llama3_2/USE_POLICY.md` | 2026-11-13 |
| `llama-3.2/USE_POLICY_llama.com_current_2026-11-12.txt` | llama.com use-policy page is a JS shell; this copy is the GitHub text until an extracted web version is supplied | 2026-11-13 |
| `llama-3.2/MODEL_CARD.md`, `MODEL_CARD_VISION.md` | GitHub `llama-models` | 2026-11-13 |
| `meta-llama-3/LICENSE`, `USE_POLICY.md` | GitHub `models/llama3/` | 2026-11-13 |
| `phi-4-mini-instruct/*` | Hugging Face `microsoft/Phi-4-mini-instruct` revision `cfbefacb99257ffa30c83adab238a50856ac3083` | 2026-11-13 |
| `osaid-1.0/OSAID_1.0_text_2026-11-12.txt` | Extracted from https://opensource.org/ai/open-source-ai-definition | 2026-11-13 |
| `source-snapshots/*.html` | Raw HTML of the web pages used | 2026-11-13 |

## Differences found

- **Llama 3.2 Hugging Face repo is gated.** These copies are from GitHub `llama-models`, not from `meta-llama/Llama-3.2-1B-Instruct` revision `9213176726f574b556790deb65791e0c5aa438b6`. If you have accepted the gate, compare `LICENSE.txt` and `USE_POLICY.md` at that revision before class and note the result here.
- **llama.com AUP/licence pages** did not return extractable policy text (client-rendered). The GitHub 25 September 2024 AUP is what `L.find("llama32_aup", …)` searches. The deep-track “policy moved” comparison will not show a wording change until a later web extract is dropped in.
- **OLMo-specific Tülu 3 SFT 0225 card** still states no dataset licence in the body (`L.find("tulu_olmo_card", "licen")` is NOT FOUND). The parent mixture card states ODC-BY-1.0 with some non-commercial portions.

## How to check

From `tier1/day1`:

```text
python -c "import licence_lab as L; assert L.verify()"
```
