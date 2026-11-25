# CivicDesk SLM course

This is a three-day, notebook-first course on using a small open language model for desk work — without treating the model as a system of record. Over the week you stand up a local chat API (OLMo), send a first CivicDesk request, and get clear on tokens, licences, and what “open” actually means. You then decide when to use a prompt, retrieval (RAG), a system integration, or a fine-tune; classify what may enter an index and what must stay out; build a small retrieve-then-cite path; and practise abstaining when the handbook is missing or the role is not allowed to see the hit. On the last day you prove that a careful prompt still fails on frozen cases, inspect training data, train a small LoRA adapter, compare base vs adapter on held-out work, and write down the risks (overfitting, rollback, tools the model must never call). The teaching lives in the notebooks. There is no slide deck for the labs.

Everything here uses **CivicDesk fiction** (synthetic tickets, résumés, handbook chunks). Do not paste real CVs, case files, passwords, or live system extracts into a cell.

## Ways to run

| Track | Where | Live model? |
|---|---|---|
| **Brev (cloud GPU)** | [Launchable link](https://brev.nvidia.com/launchable/deploy?launchableID=env-3MJyQ68mgwiJAcIJraeobJF3GoB) | Yes — course image on a T4 |
| **Docker / local** | `tier1/` on your machine | Yes — OLMo on `:8000`, if you have a GPU |
| **Colab** | [`colab/`](colab/README.md) | Scripted demo replies on CPU. Free T4 can train on Day 3. |

No local GPU? Use **Brev** for the full live-model experience, or **Colab** for the ideas with demo replies. Have a GPU laptop? Use **Docker**.

### About the GPU

Running the live model needs a **GPU**.

- **Brev:** a cloud T4 is already part of the launchable. You pay for the instance while it is on (about **US$0.60 per hour** for that class of GPU — check Brev for the current rate).
- **Colab, no GPU:** you can still do the notebooks. Chat cells use scripted demo replies. You are not running OLMo from the Docker image inside Colab.
- **Docker, no GPU:** you can still open Jupyter and work through every notebook. Set `BACKEND = "demo"`. The labs run; you just are not talking to the live model.
- **Docker, with a GPU:** pull the Hub image, start the container, set `BACKEND = "local"`, and use OLMo on `:8000`.

So: no GPU on your laptop does not block the course. Use Brev for a live model in the cloud, or Colab/demo for notebooks without one.

---

## Run on Brev (cloud GPU)

If you do not have a GPU at home, you can still run the full course experience in the cloud. The Brev launchable is set up for a **T4** GPU and loads the same course stack you would get from the Docker image.

1. Create an account at [brev.nvidia.com](https://brev.nvidia.com/) and top it up with some credit (USD).
2. Log in, then open this launchable:  
   [Deploy CivicDesk Tier 1 on Brev](https://brev.nvidia.com/launchable/deploy?launchableID=env-3MJyQ68mgwiJAcIJraeobJF3GoB)
3. Wait while Brev provisions the machine. **First load can take about 15 minutes.** That is normal.
4. When it is ready, open Jupyter from the Brev console and work through `tier1/` as usual. Set `BACKEND = "local"` once OLMo is up.

Stop the instance when you are done so you are not charged while idle. Pricing is roughly **US$0.60 per hour** for this T4 setup; confirm the current rate on Brev before you leave it running.

---

## Install Docker (if you need it)

You need [Docker](https://docs.docker.com/get-docker/) installed and running.

- **Windows:** [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) (WSL 2 required; the installer walks you through it)
- **Mac:** [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
- **Linux:** [Engine install](https://docs.docker.com/engine/install/) (or Desktop)

After install, open Docker Desktop (Windows/Mac) and wait until it says it is running. Give it about **8 GB** memory under **Settings → Resources**.

---

## Run with Docker (easiest)

The course image is on Docker Hub:  
[unclekris/fine-tuning-course-t1](https://hub.docker.com/r/unclekris/fine-tuning-course-t1)

It already has JupyterLab, the notebooks, and **OLMo** baked in. You do not need to build from this repo unless you are changing the image.

A **GPU** is needed for the live model. Without one, still start the container and use the notebooks with `BACKEND = "demo"`.

**Pull and run:**

```bash
docker pull unclekris/fine-tuning-course-t1:v1

docker run --rm -it -p 8888:8888 -p 8000:8000 unclekris/fine-tuning-course-t1:v1
```

Then open:

```text
http://localhost:8888/lab
```

Start at `tier1/day1/T1-01_first_call.ipynb`. With a GPU, set `BACKEND = "local"` and wait until the logs say OLMo is up on `:8000`. Without a GPU, leave `BACKEND = "demo"` and keep going.

### Windows (PowerShell)

```powershell
docker pull unclekris/fine-tuning-course-t1:v1
docker run --rm -it -p 8888:8888 -p 8000:8000 unclekris/fine-tuning-course-t1:v1
```

### Compose

From this `course/` folder (uses the Hub image):

```bash
docker compose up
```

Stop with `Ctrl+C`, then `docker compose down`.

### Tips

- Port `8888` busy? Use `-p 8890:8888` and open `http://localhost:8890/lab`.
- **Do not bind-mount** a OneDrive / “Other computers” path over `/civicdesk` — Docker often mounts that empty and hides the notebooks. Prefer the image as shipped.
- To edit files live, copy `course` to a normal local folder (for example `C:\civicdesk`) and mount that:

```bash
docker run --rm -it -p 8888:8888 -p 8000:8000 -v "C:/civicdesk:/civicdesk" unclekris/fine-tuning-course-t1:v1
```

### Build from source (maintainers)

Only if you are changing the Dockerfile or baked weights:

```bash
docker build -t civicdesk-course .
docker run --rm -it -p 8888:8888 -p 8000:8000 civicdesk-course
```

The build downloads OLMo only (`allenai/OLMo-2-0425-1B-Instruct`). That layer is several GB and needs network the first time.

---

## Run in Colab

No Docker, or no GPU on your laptop? Use the Colab copies.

Colab does **not** run the Docker Hub image. On a CPU runtime you will not get a live local OLMo — chat cells use scripted demo replies, and that is fine for learning the ideas. For the live model from the image, use Docker on a machine that has a GPU.

1. Open [`colab/README.md`](colab/README.md).
2. Click an **Open in Colab** link for the notebook you want (Day 1–3 are listed there).
3. In Colab: **Runtime → Run all**. The first cell finds or clones the course.

What to expect:

- Day 1 chat cells use scripted demo replies on CPU.
- Day 2 does not need a model.
- Day 3 training needs a GPU. On free Colab those cells skip with a clear message, or switch **Runtime → T4** to train for real.

Prep notebooks: [`prep/`](prep/README.md). Optional data-cleaning labs: [`tier1/data_cleaning/`](tier1/data_cleaning/README.md).

---

## Run locally with pip (no Docker)

Python 3.11+ recommended. From this directory:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
jupyter lab
```

Open `tier1/day1/` and keep `BACKEND = "demo"` unless you have already started a local model server.

---

## What’s in the repo

```text
.
├── Dockerfile
├── docker-compose.yml
├── environment/          # Python deps, entrypoint, model download at build
├── prep/                 # short Colab pre-work
├── colab/                # Colab mirror of Tier 1
├── auxiliary/            # optional self-taught notes
└── tier1/
    ├── day1/             # start a model, tokens, licences, use-case canvas
    ├── day2/             # classify sources, RAG, access, decision card
    ├── day3/             # prove the prompt fails, train a LoRA, compare
    └── data_cleaning/    # optional INDEX / NEVER / HOLD practice
```

### Day 1 (`tier1/day1/`)

| File | Roughly | Topic |
|---|---|---|
| `T1-00_opening.md` | start | data ban, pre-test |
| `T1-01a_build_from_scratch.ipynb` | morning | check host / fetch weights / start API — or stay on demo |
| `T1-01_first_call.ipynb` | morning | first CivicDesk call (`BACKEND`) |
| `T1-02_tokens_and_transformer.ipynb` | mid | tokens and the architecture card |
| `T1-03_slm_vs_llm.ipynb` | afternoon | model size / scorecard |
| `T1-04_openness_licences_gpu.ipynb` | afternoon | licences and GPU questions |
| `T1-05_usecase_canvas.ipynb` | end | redaction canvas + gold pairs |

### Day 2 (`tier1/day2/`)

No GPU required. Order: T1-06 → T1-07 → T1-08 → T1-09 → T1-10 → T1-10b. Reference copies in `day2/completed/`.

### Day 3 (`tier1/day3/`)

Prove the base model fails on held-out cases, inspect training data, train a LoRA with `TrainSession`, save an adapter, compare base vs adapter. Main path: T1-11 → T1-12 → T1-12b. Optional if time: `optional/T1-13`, `optional/T1-14`. Needs a GPU for live training; otherwise notebooks fall back to RECORDED runs when those files exist.

### Model in the Docker image

- **OLMo** on **:8000** — `allenai/OLMo-2-0425-1B-Instruct`

`BACKEND = "demo"` still works anywhere (canned text, no model). For a live call in the image, use `BACKEND = "local"` or `BACKEND = "olmo"`.

---

## Data ban

If it came from a real workplace system, it does not go in a cell. Use the CivicDesk fiction under `tier1/`. A planted secret in a prompt is a fail for the exercise.

## If you get stuck

Load `completed/` for **that** notebook only and mark it as loaded from reference. Git is not required in the room.

CPU replies are slow. That is normal. Stop Jupyter with `Ctrl+C` in the terminal where it is running.
