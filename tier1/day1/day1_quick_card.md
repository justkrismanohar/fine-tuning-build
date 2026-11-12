# Day 1 quick card — commands and the data ban

Keep this on the desk. One page.

## Data ban

No real CVs, Cabinet/EDMS exports, case files, health or LMS submissions, burgess applications, patrol/radar notes, passwords, API keys, live GLPI/GIS/asset extracts.

CivicDesk fiction only.

## Stack (say it once)

Notebook → OpenAI-compatible API → vLLM (or hf server / demo) → tokenizer → OLMo or Phi weights.

T1-01a starts the door. T1-01 talks through it.

## Backend in T1-01

`BACKEND = "demo"` | `"local"` | `"shared"` | `"custom"`

## Commands

```text
python build_llms.py check
python build_llms.py serve --engine vllm
python build_llms.py wait
nvidia-smi
```

No GPU: leave BACKEND as demo. Shared room: paste the facilitator URL.

## Models today

- Primary: `allenai/OLMo-2-0425-1B-Instruct`
- Comparison: `microsoft/Phi-4-mini-instruct`
- Not today: ChatGPT, Llama install, Ollama, fine-tune

## If stuck

Load `completed/` for **this** notebook only. Mark “loaded from reference.” A day done entirely from completed copies is not evidence.

## Overnight

Finish the T1-05 canvas. 20–30 minutes. No GPU. No ministry files.
