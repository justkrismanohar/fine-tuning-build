# Own environment — when the course Docker image is the wrong object

The **default** is the course container (`Dockerfile` / `docker compose up --build`). Use this page only if that path does not fit the machine, the policy, or the network.

If you only need the **learnings** and not a live model, use the [Colab track](colab/README.md) instead of building a local stack.

You are still on **CivicDesk fiction**. You still open the same notebooks. You are **not** building a ministry production stack.

## 1. Decide in one minute

| Your situation | What to do | Live OLMo/Phi? |
|---|---|---|
| No Docker, need the **ideas** only | [Colab track](colab/README.md) — CPU runtime | No — scripted `[OLMo demo]` replies |
| Docker works, enough RAM | Stay on the [course README](README.md) Docker path | Yes (`BACKEND=local`) |
| Docker works, RAM is tight | Same image, load OLMo only: `CIVICDESK_LOAD_MODELS=olmo` | OLMo only |
| Docker bind-mount emptied `/civicdesk` | Run **without** `-v`. Copy the folder off OneDrive if you must edit | Yes |
| No Docker, no GPU, Windows laptop | **Path A** then **Path B**. T1-01a `ENGINE='skip'` | No — `BACKEND=demo` or facilitator **shared** URL |
| No Docker, need a live model on CPU | **Path C** (`--engine hf`). Slow. Fine for a smoke test | Yes, slow |
| Linux (or WSL2) + NVIDIA GPU, no course image | **Path D** vLLM in a venv | Yes |
| Ministry VM / MEA Azure / approved GPU workspace (e.g. NVIDIA Brev) | **Path E** — still the same Dockerfile if Docker is allowed there | Yes |
| Facilitator already hosts `:8000` | T1-01 `BACKEND=shared` | Yes, on their box |
| You already have an OpenAI-compatible `/v1` | T1-01 `BACKEND=custom` | Whatever that server is |

Days **2 and 3** (RAG, classification, adapter literacy) run with **no GPU** on every path. Only Day 1 live calls need a server.

## 2. What you are aiming at

Same contract as the container:

```
notebook  →  http://127.0.0.1:8000/v1   (OLMo)
          →  http://127.0.0.1:8001/v1   (Phi)
```

Official publisher ids (do not swap in a Hub fork):

- `allenai/OLMo-2-0425-1B-Instruct`
- `microsoft/Phi-4-mini-instruct`

Write what you actually ran in the table at the end of this page (source, version, date). That is the classroom provenance record.

## 3. Host sizes (classroom, not a quote)

| Path | RAM | Disk | GPU | Notes |
|---|---|---|---|---|
| Notebooks + `BACKEND=demo` | 4 GB | 1 GB for the `course/` folder | None | Completes the pedagogy; not evidence of a live model |
| Jupyter + HF CPU servers | ~16 GB to load **both**; ~8–10 GB OLMo only | + several GB for weights | None | Replies are slow. Expected. |
| vLLM on GPU | 16 GB system RAM | + weights | ~8 GB+ VRAM for these small Instruct models at classroom context | Linux + CUDA. Two “8 GB” cards are not interchangeable (T1-04). |
| Course Docker with both models | Docker engine ~16 GB | Image several GB | Optional | Default classroom |

Network: Hugging Face Hub for first weight download (or copy a cache the facilitator supplies). No public chatbot.

## Path A — stay in the room with no local model

Use this if IT will not allow Docker or large downloads.

1. Prefer the **[Colab track](colab/README.md)** if you only need the ideas (CPU, no Docker, scripted replies). Prep Colab (`prep/`) is still not Day 1.
2. Or get the `course/` folder (USB, approved share, or git clone) and open `tier1/` however you can: course Docker on another machine, or facilitator Jupyter.
3. In T1-01a set `ENGINE = "skip"`.
4. In T1-01 set `BACKEND = "demo"`. If the facilitator pastes a URL, use `BACKEND = "shared"` instead.
5. Run Day 2–3 as written. They do not need `:8000`.

You practised the **path**. You did not prove a live local model. Say that on the transfer card.

## Path B — Python venv, notebooks only (no serve)

Windows, macOS, or Linux. Python **3.11 or 3.12**.

**Windows PowerShell** (from the `course/` folder, on a **local disk**, not OneDrive if you can help it):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r environment\requirements.txt
jupyter lab
```

If execution policy blocks the activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
jupyter lab
```

Open the URL Jupyter prints. Open `tier1/day1/T1-01_first_call.ipynb`. Set `BACKEND = "demo"` until Path C or D is up.

Do **not** `pip install -r environment/requirements-gpu.txt` on a CPU-only laptop. That file is Linux+CUDA (vLLM).

## Path C — live models on CPU (`hf` engine)

Same venv as Path B, then add the CPU runtime:

```powershell
python -m pip install torch transformers accelerate sentencepiece protobuf huggingface_hub
```

On Linux/macOS the same packages. If `torch` has no wheel, use the CPU index:  
`https://download.pytorch.org/whl/cpu`

From `course/tier1/day1/`:

```powershell
python build_llms.py check
python build_llms.py download
python build_llms.py serve --engine hf
python build_llms.py wait
python build_llms.py health
```

`check` is allowed to say “no GPU”. That is an honest result.

In T1-01: `BACKEND = "local"`. Leave `FALLBACK_TO_DEMO = True` so a dead port still shows canned text plus the error.

Stop:

```powershell
python build_llms.py stop
```

OLMo only if RAM is tight:

```powershell
python build_llms.py download --models olmo
python build_llms.py serve --engine hf --models olmo
```

## Path D — Linux or WSL2 + NVIDIA, vLLM, no course image

vLLM is a **Linux+CUDA** runtime. On Windows: Docker Desktop with a Linux engine **or** WSL2. Native Windows Python will not run `--engine vllm`.

1. NVIDIA driver + CUDA that your `nvidia-smi` reports.
2. Path B venv **inside WSL2 or Linux** (not the Windows venv).
3. `python -m pip install -r environment/requirements-gpu.txt`  
   (installs vLLM; this can fail on unsupported GPU/driver — then use Path C or the course Docker with `--gpus all`).
4. From `tier1/day1/`:

```bash
python build_llms.py check
python build_llms.py download
python build_llms.py serve --engine vllm
python build_llms.py wait
```

5. T1-01 `BACKEND = "local"`.

You can also skip venv vLLM and run the **upstream vLLM containers** via `python build_llms.py serve --engine docker` if Docker + GPU is allowed but the course image is not.

## Path E — ministry VM, MEA Azure, or approved GPU workspace

If the policy is “no Docker on laptops” but a **controlled Linux host** is allowed:

1. Copy `course/` onto that host (or clone the approved git ref).
2. Prefer **the same Dockerfile** there. That is still “own environment”; it is not a second curriculum.

```bash
docker build -t civicdesk-course .
docker run --rm -it --gpus all -p 8888:8888 -p 8000:8000 -p 8001:8001 civicdesk-course
```

3. If Docker is forbidden on that VM too, use Path D on the VM and SSH/port-forward `8888`, `8000`, `8001` only on a private network.
4. **NVIDIA Brev / similar:** create a GPU instance the ministry has approved, clone or upload `course/`, run the commands above. Confirm region, identity, and that CivicDesk-only still applies. Brev is a **host**, not a different set of notebooks.
5. Do not point `BACKEND=custom` at a public ChatGPT endpoint for this course.

## Path F — shared classroom or a custom door

In T1-01:

- `BACKEND = "shared"` and paste the facilitator `SHARED_URL` (OpenAI-compatible `/v1`).
- `BACKEND = "custom"` and set `CUSTOM_OLMO_URL` / `CUSTOM_PHI_URL` to servers **you** control.

`WHICH_MODEL` is still `"olmo"` or `"phi"`. It does not change the host.

## 4. Record (fill by hand)

| Item | Write what you used |
|---|---|
| Date | |
| Machine (laptop / WSL / ministry VM / GPU cloud) | |
| Path letter (A–F) | |
| Python version (`python --version`) | |
| How notebooks started (Docker / venv Jupyter / shared) | |
| Engine (`skip` / `hf` / `vllm` / `docker` / none) | |
| Model ids and where they came from (HF official org vs cache copy) | |
| `BACKEND` in T1-01 | |
| Live call? (`mode: live` vs `demo`) | |

Keep this next to the T1-04 licence notes. Do not invent a circular; do not invent a model id.

## 5. If it fails

| Symptom | Likely cause | What to do |
|---|---|---|
| `/civicdesk` empty in Docker | Bind-mount of OneDrive / “Other computers” | Drop `-v`; copy `course` to `C:\civicdesk` |
| Container killed on start | RAM | `CIVICDESK_LOAD_MODELS=olmo`; raise Docker memory |
| `vllm` import fails on Windows | vLLM is Linux+CUDA | WSL2, course Docker, or `--engine hf` |
| `health` fails | Server still loading, or CPU OOM | Wait; `wait` script; OLMo only; or `BACKEND=demo` |
| Hugging Face download blocked | Ministry proxy | Facilitator cache, or Path A + shared URL |
| `Activate.ps1` error | Execution policy | `Set-ExecutionPolicy -Scope Process Bypass` |
| Port 8888 in use | Another Jupyter | `-p 8890:8888` or stop the other process |

## 6. What this page is not

- Not approval to run OLMo on Cabinet minutes or CVs.
- Not a production Dockerfile (non-root, SBOM, signed digest — consultant/workplan items, not this classroom path).
- Not a reason to `pip install` random Hub models. Stay on the two official ids above unless MPAAI names another.

When Docker **is** suitable, ignore this file and use the [course README](README.md).
