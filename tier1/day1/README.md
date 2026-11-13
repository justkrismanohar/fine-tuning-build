# Tier 1 Day 1 — materials for review

Start a model and see how it works. Instruction is in the notebooks. No slide deck.

**Two tracks:** this folder is the live Docker/local path. No Docker and no GPU → the [Colab mirror](../../colab/README.md) (scripted replies, same notebooks).

To spin up Jupyter for the whole course (Docker or local pip), use the parent [course README](../../README.md). From `course/`:

```text
docker build -t civicdesk-course .
docker run --rm -it -p 8888:8888 -v "$PWD:/civicdesk" civicdesk-course
```

Then open `http://localhost:8888/lab` and this folder. Default `BACKEND='demo'` needs no GPU.

**Facilitator:** the entrypoint copies `/opt/civicdesk` into `/civicdesk` only when `civicdesk_lab.py` is missing. A container started on an older bind-mounted checkout keeps that volume's helper and `hf_openai_server.py`, so temperature and the OLMo tokenizer will not match this image until the mount is updated or dropped.

## Order of play

| File | When |
|---|---|
| `T1-00_opening.md` | 09:00–09:15 facilitator + pre-test |
| `T1-01a_build_from_scratch.ipynb` | 09:15–09:50 stand up OLMo + Phi (**or** `python build_llms.py`) |
| `T1-01_first_call.ipynb` | 09:50–10:30 first CivicDesk call; **set BACKEND here** |
| `T1-02_tokens_and_transformer.ipynb` | 10:45–12:00 |
| `T1-03_slm_vs_llm.ipynb` | 12:45–13:45 |
| `T1-04_openness_licences_gpu.ipynb` | 13:45–14:20 |
| `T1-05_usecase_canvas.ipynb` | 14:20–14:55 (group) worked redaction canvas + gold pairs; overnight |

## From scratch (deploy, not pre-train)

```text
python build_llms.py check
python build_llms.py download
python build_llms.py serve --engine vllm    # or docker | hf
python build_llms.py wait
python build_llms.py stop
```

That writes `logs/endpoint.json`. T1-01 with `BACKEND='local'` reads it.

| Engine | Use when |
|---|---|
| `vllm` | Course image / Linux+CUDA |
| `docker` | GPU + Docker, no local vLLM pip |
| `hf` | `hf_openai_server.py` via transformers; smoke test; slow on CPU |
| skip + `BACKEND='demo'` | No GPU; overnight review of the path |
| `BACKEND='shared'` | Facilitator URL for the browser workspace |

Windows without WSL/Docker: `check` will say so. That is expected. Stay on demo or shared. If the course container is unsuitable for this machine, follow [../../03_own_environment.md](../../03_own_environment.md).

## Backend switch (T1-01 cell)

`lab.use_backend("demo"|"local"|"shared"|"custom", ...)`. Later notebooks keep using that kernel (or re-run the cell). `FALLBACK_TO_DEMO=True` means a dead server still returns canned text plus `error`.

## Other files

`civicdesk_lab.py`, `build_llms.py`, `hf_openai_server.py`, `data/`, `cards/`, `completed/`, `day1_quick_card.md`.
