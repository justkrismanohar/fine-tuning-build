# CivicDesk SLM course notebooks

Hands-on materials for **UNDP-TTO-00212** (open-source SLM/LLM training for GoRTT / MPAAI). Instruction lives in the notebooks. There is no slide deck for the labs.

This folder is packaged like a classroom image: a `Dockerfile`, an `environment/` with Python deps, and the notebooks. The layout follows the same idea as the [NVIDIA DLI Fundamentals of Deep Learning course content](https://github.com/NVDLI/fundamentals-of-deep-learning/tree/main/course_content) — build once, open JupyterLab, run the labs — adapted for CivicDesk (synthetic ministry-style tickets, not MNIST).

**CivicDesk only.** No real CVs, Cabinet/EDMS exports, case files, health records, burgess applications, patrol notes, passwords, or live GLPI/GIS extracts go in a cell.

**Two tracks**

| Track | Use when | Live model? |
|---|---|---|
| **Docker / local** (`tier1/`) | Classroom machine, or [own environment](03_own_environment.md) | Yes, if you start OLMo/Phi |
| **Colab demo** ([`colab/`](colab/README.md)) | No Docker, no GPU | No — scripted `[OLMo demo]` replies |

## Repository contents

```text
.
├── Dockerfile
├── docker-compose.yml
├── environment/
│   ├── entrypoint.sh             # local Jupyter
│   ├── docker-entrypoint.sh      # seed notebooks, load OLMo/Phi, start lab
│   ├── download_models.py        # used at image build to bake weights
│   ├── requirements.txt          # Jupyter + demo path (no GPU)
│   └── requirements-gpu.txt      # optional vLLM / transformers
├── 00_common_needs_from_eois.md
├── 01_tier1_day_by_day_plan.md
├── prep/                         # no-code Colab pre-work (2–3 evenings)
├── colab/                        # Tier 1 Colab mirror (demo replies, no Docker/GPU)
├── auxiliary/                    # self-taught workshops (no GPU)
└── tier1/
    ├── day1/                     # start a model
    ├── day2/                     # retrieve, cite or abstain
    ├── day3/                     # inspect a dataset and a pretend adapter
    └── data_cleaning/            # optional Colab: INDEX / NEVER / HOLD, government gotchas
```



### `Dockerfile`

Builds a JupyterLab environment from `python:3.11-slim`, installs PyTorch (CPU) and transformers, and **downloads OLMo and Phi into `/models` during `docker build`**. On start it loads those weights and serves:

- Jupyter on `:8888`
- OLMo on `:8000/v1`
- Phi on `:8001/v1`

In T1-01 set `BACKEND = "local"`. First build needs network and several GB of disk. Loading **both** models on CPU wants roughly 16 GB RAM for the Docker engine; to load OLMo only: `CIVICDESK_LOAD_MODELS=olmo`.

### `environment/`

- `requirements.txt` — JupyterLab and the packages the demo notebooks import.
- `requirements-gpu.txt` — extra packages for `build_llms.py serve --engine vllm` on Linux+CUDA.
- `entrypoint.sh` — JupyterLab startup script (Docker and local `sh`).



### `tier1/day1/`

Day 1 labs. Open them in order. Each notebook has the teaching text; do not paste ministry files.


| File                                 | When        | What they do                                                                                      |
| ------------------------------------ | ----------- | ------------------------------------------------------------------------------------------------- |
| `T1-00_opening.md`                   | 09:00–09:15 | Data ban, pre-test                                                                                |
| `T1-01a_build_from_scratch.ipynb`    | 09:15–09:50 | Check host; fetch OLMo/Phi weights; start an OpenAI-compatible API — **or** skip and stay on demo |
| `T1-01_first_call.ipynb`             | 09:50–10:30 | `BACKEND` + `WHICH_MODEL`; system vs user; one CivicDesk request                                  |
| `T1-02_tokens_and_transformer.ipynb` | 10:45–12:00 | Tokens and the architecture card                                                                  |
| `T1-03_slm_vs_llm.ipynb`             | 12:45–13:45 | Two small models, frozen screening set, scorecard + cost                                          |
| `T1-04_openness_licences_gpu.ipynb`  | 13:45–14:20 | Licence scavenger hunt (Llama 3.2 vs Apache), scenario labels, GPU card                           |
| `T1-05_usecase_canvas.ipynb`         | 14:20–14:55 | Worked redaction canvas, frozen baseline, group experiment design + gold pairs                    |


### `tier1/day2/`

Retrieve from an approved CivicDesk pile. No GPU. Open in order: T1-06 (intervention map) → T1-07 (index vs never) → T1-08 (RAG) → T1-09 (prompt vs RAG) → T1-10 (access) → T1-10b (decision card). Executed reference copies live in `day2/completed/`.

### `tier1/day3/`

Inspect an SFT set and a pretend adapter. Do **not** train. Open in order: T1-11 → T1-12 → T1-12b → T1-13 → T1-14. Executed copies in `day3/completed/`.

### `prep/`

Optional **no-code** pre-work (about 4–5 hours over two or three evenings). Google Colab; no Python install. Start at [`prep/README.md`](prep/README.md). PREP-00 is how to click Run; **PREP-00b** is the very basic Python needed to follow a `# [CHANGE]` line; **PREP-02b** is cleaning/metadata literacy (INDEX / NEVER / HOLD). Send with the repo: [`prep/data_cleaning_and_metadata.md`](prep/data_cleaning_and_metadata.md). Readings (Hugging Face ch. 1, OSI, Dublin Core, dataset cards, optional OWASP/NIST/Tesseract headings) are in [`prep/readings.md`](prep/readings.md). People who already use notebooks can skip PREP-00; skip 00b only if you already read Python.

Auxiliary workshops are in `auxiliary/` and are self-taught (no GPU).

## Run with Docker

From **this** directory (`course/`):

```bash
docker build -t civicdesk-course .
```

Start JupyterLab **and** the two model servers:

```bash
docker run --rm -it -p 8888:8888 -p 8000:8000 -p 8001:8001 civicdesk-course
```

Then open:

```text
http://localhost:8888/lab
```

The file browser root is `/civicdesk`. Open `tier1/day1/T1-01_first_call.ipynb` and set **`BACKEND = "local"`**. The container already loaded the weights that were baked in at build.

Wait until the logs say `olmo is up on :8000` (and Phi on `:8001`) before you send a live call. First start can take several minutes while the models load into RAM.

**Do not bind-mount** a OneDrive / “Other computers” path over `/civicdesk`. Docker Desktop often mounts that as an empty folder, which hides the notebooks that were copied into the image. Compose no longer mounts by default. If `/civicdesk` looks empty, rebuild and run **without** `-v`.

To edit live, copy the `course` folder to a local disk Docker can share (for example `C:\civicdesk`) and then:

```bash
docker run --rm -it -p 8888:8888 -v "C:/civicdesk:/civicdesk" civicdesk-course
```

If that mount is still empty, the container copies the baked-in files from `/opt/civicdesk` into `/civicdesk` at start. The copy runs only when `/civicdesk/tier1/day1/civicdesk_lab.py` is missing, so an older mounted checkout keeps its helper and `hf_openai_server.py` instead of the image copies.

PowerShell (no mount — use the files in the image):

```powershell
docker build -t civicdesk-course .
docker run --rm -it -p 8888:8888 -p 8000:8000 -p 8001:8001 civicdesk-course
```

Give Docker Desktop enough memory (Settings → Resources). Both models on CPU need a large engine; OLMo-only is lighter:

```powershell
docker run --rm -it -e CIVICDESK_LOAD_MODELS=olmo -p 8888:8888 -p 8000:8000 civicdesk-course
```

If port `8888` is already in use, map another local port:

```bash
docker run --rm -it -p 8890:8888 civicdesk-course
```

Then open `http://localhost:8890/lab`.

### Compose (same thing)

```bash
docker compose up --build
```

Stop with `Ctrl+C`, then `docker compose down`.

If Docker is the **wrong object** (no Docker on the laptop, Windows without WSL, ministry VM, approved GPU cloud, RAM too small, or a server you already host), use **[03_own_environment.md](03_own_environment.md)** — decision table, pip/venv, CPU `hf` serve, WSL/vLLM, shared/custom URL, and a provenance row to fill.

## Run locally with `pip`

Python 3.11+ recommended. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
```

Start JupyterLab:

```bash
jupyter lab
```

or:

```bash
sh environment/entrypoint.sh
```

Jupyter prints a local URL. Open it, then open `tier1/day1/`.

Windows without Docker: this pip path is the usual option. `build_llms.py check` will say if there is no NVIDIA GPU. Stay on `BACKEND='demo'` or use the course shared URL. Full decision tree and GPU/VM steps: [03_own_environment.md](03_own_environment.md).

## Live models

The course image **already contains** OLMo and Phi (`/models/olmo`, `/models/phi`). You do not run `build_llms.py download` inside it unless you skipped that layer.

On start the entrypoint loads those folders with `hf_openai_server.py` (CPU; GPU if the container sees CUDA). T1-01a is still there so learners can see the steps; if `/models/olmo` exists, `download` reports “already in image”.

`BACKEND='demo'` still works (canned text, no model). For a real call in this image use `BACKEND='local'`.

Faster GPU serve (Linux + NVIDIA + nvidia-container-toolkit), after the image is built:

```bash
docker run --rm -it --gpus all -p 8888:8888 -p 8000:8000 -p 8001:8001 civicdesk-course
```

Then in a lab terminal you can stop the CPU servers and use vLLM if you installed `environment/requirements-gpu.txt`. The classroom default in this Dockerfile is the baked HF servers, not vLLM.


| Engine                  | Use when                                                                       |
| ----------------------- | ------------------------------------------------------------------------------ |
| skip + `BACKEND='demo'` | Canned replies; no need to wait for :8000 / :8001                              |
| `vllm`                  | Linux+CUDA, vLLM installed                                                     |
| `docker`                | GPU + Docker, no local vLLM pip (`python build_llms.py serve --engine docker`) |
| `hf`                    | `hf_openai_server.py`; smoke test; slow on CPU                                 |
| `BACKEND='shared'`      | Facilitator pastes the course workspace URL                                    |


OLMo is served on port **8000**, Phi on **8001**. Primary id: `allenai/OLMo-2-0425-1B-Instruct`. Comparison: `microsoft/Phi-4-mini-instruct`.

## Data ban

If it came from a ministry system, it does not go in a cell. Use the CivicDesk fiction in `tier1/day1/data/`. A planted secret in a prompt is a fail for the exercise.

## Notes

- `docker build` downloads OLMo + Phi into the image. That layer is several GB and needs Hugging Face network access. **Notebook-only edits do not re-download** — the weights layer sits *before* `COPY . /opt/civicdesk`. You still run `docker compose up --build`; Docker reuses `/models` and only copies the new notebooks. You re-download only if `download_models.py`, the pip lines, or the base image change.
- Loading both models on CPU is RAM-heavy. If the container is killed on start, use `CIVICDESK_LOAD_MODELS=olmo` or raise Docker Desktop memory.
- CPU replies are slow. That is expected. vLLM on a GPU is the faster classroom path later.
- Stop JupyterLab with `Ctrl+C` in the terminal where it is running.
- Git is not required in the room. If stuck, load `tier1/day1/completed/` for **that** notebook only and mark it as loaded from reference.

