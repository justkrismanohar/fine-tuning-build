"""Set up OLMo and Phi from scratch: check host, fetch weights, start an OpenAI-compatible API.

This is deploy-and-serve, not pre-training.

    python build_llms.py check
    python build_llms.py download
    python build_llms.py serve --engine vllm
    python build_llms.py serve --engine hf
    python build_llms.py serve --engine docker
    python build_llms.py health
    python build_llms.py all --engine vllm
    python build_llms.py stop

Notebook equivalent: T1-01a_build_from_scratch.ipynb (same functions).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)
PIDS = LOGS / "server_pids.json"
ENDPOINT = LOGS / "endpoint.json"

OLMO = "allenai/OLMo-2-0425-1B-Instruct"
PHI = "microsoft/Phi-4-mini-instruct"
BAKED = Path(os.environ.get("CIVICDESK_MODELS_DIR", "/models"))


def model_src(key: str) -> str:
    """Local folder from the course image, else the Hugging Face id."""
    local = BAKED / key
    if local.is_dir() and any(local.iterdir()):
        return str(local)
    return {"olmo": OLMO, "phi": PHI}[key]


def check() -> dict:
    """What this machine can actually run."""
    info: dict = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "nvidia_smi": None,
        "docker": bool(shutil.which("docker")),
        "vllm_import": False,
        "transformers_import": False,
        "note": "",
    }
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode == 0:
            info["nvidia_smi"] = r.stdout.strip()
    except Exception:
        pass
    try:
        import vllm  # noqa: F401

        info["vllm_import"] = True
        info["vllm_version"] = getattr(vllm, "__version__", "?")
    except Exception:
        pass
    try:
        import transformers  # noqa: F401

        info["transformers_import"] = True
    except Exception:
        pass

    if sys.platform.startswith("win") and not info["nvidia_smi"]:
        info["note"] = (
            "Windows without a visible NVIDIA GPU: use BACKEND='demo' in the notebooks, "
            "or run this script in WSL2/Docker with a GPU. vLLM is a Linux+CUDA runtime."
        )
    elif sys.platform.startswith("win") and info["nvidia_smi"]:
        info["note"] = (
            "GPU is visible from Windows, but vLLM still wants Linux. Use Docker Desktop "
            "(Linux engine + GPU) or WSL2, or --engine hf with transformers (slow on CPU)."
        )
    elif info["vllm_import"]:
        info["note"] = "vLLM import works. python build_llms.py serve --engine vllm"
    elif info["docker"]:
        info["note"] = "No vLLM in this Python. Use --engine docker, or pip install vllm on Linux+CUDA."
    elif info["transformers_import"]:
        info["note"] = "No vLLM. You can try --engine hf (transformers). Fine for a smoke test, not the classroom default."
    else:
        info["note"] = "No GPU runtime here. Continue the day with BACKEND='demo' or the shared course URL."
    return info


def download(models: list[str] | None = None) -> dict:
    """Fetch weights from Hugging Face into the local cache. Does not start a server."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise SystemExit("pip install huggingface_hub") from exc
    wanted = models or ["olmo", "phi"]
    out = {}
    for key in wanted:
        baked = BAKED / key
        if baked.is_dir() and any(baked.iterdir()):
            print("already in image", baked)
            out[key] = str(baked)
            continue
        repo = {"olmo": OLMO, "phi": PHI}[key]
        print("downloading", repo)
        path = snapshot_download(repo_id=repo)
        out[key] = path
        print(" ", path)
    return out


def _serve_cmd_vllm(model: str, port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        model,
        "--port",
        str(port),
        "--host",
        "0.0.0.0",
    ]


def _serve_cmd_hf(model: str, port: int) -> list[str]:
    return [sys.executable, str(HERE / "hf_openai_server.py"), "--model", model, "--port", str(port)]


def _docker_cmd(model: str, port: int, name: str) -> list[str]:
    image = os.environ.get("CIVICDESK_VLLM_IMAGE", "vllm/vllm-openai:latest")
    return [
        "docker",
        "run",
        "--gpus",
        "all",
        "-d",
        "--rm",
        "--name",
        name,
        "-p",
        f"{port}:8000",
        image,
        "--model",
        model,
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]


def serve(engine: str = "vllm", models: list[str] | None = None, background: bool = True) -> dict:
    """Start one process/container per model. Writes logs/server_pids.json."""
    engine = engine.lower()
    wanted = models or ["olmo", "phi"]
    ports = {"olmo": int(os.environ.get("CIVICDESK_OLMO_PORT", "8000")), "phi": int(os.environ.get("CIVICDESK_PHI_PORT", "8001"))}
    started = {}
    for key in wanted:
        port = ports[key]
        model = {"olmo": OLMO, "phi": PHI}[key] if engine == "docker" else model_src(key)
        log_path = LOGS / f"{key}_{engine}.log"
        if engine == "vllm":
            cmd = _serve_cmd_vllm(model, port)
        elif engine == "hf":
            cmd = _serve_cmd_hf(model, port)
        elif engine == "docker":
            cmd = _docker_cmd(model, port, f"civicdesk-{key}")
        else:
            raise ValueError("engine must be vllm, hf, or docker")
        print("starting", key, "on", port)
        print(" ", " ".join(cmd))
        if engine == "docker":
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stderr)
                raise SystemExit(f"docker run failed for {key}")
            started[key] = {"engine": engine, "port": port, "model": model, "container": r.stdout.strip()}
        else:
            logf = open(log_path, "w", encoding="utf-8")
            proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)
            started[key] = {
                "engine": engine,
                "port": port,
                "model": model,
                "pid": proc.pid,
                "log": str(log_path),
            }
    PIDS.write_text(json.dumps(started, indent=2), encoding="utf-8")
    write_endpoint_json(engine, wanted, ports)
    if not background:
        print("foreground: Ctrl+C to stop. For class, use background=True and build_llms.py health")
    return started


def write_endpoint_json(engine: str, wanted: list[str], ports: dict[str, int]) -> Path:
    ids = {"olmo": OLMO, "phi": PHI}
    payload = {
        "backend": "local",
        "mode": "live",
        "engine": engine,
        "olmo": {
            "base_url": f"http://127.0.0.1:{ports['olmo']}/v1",
            "model": ids["olmo"],
            "port": ports["olmo"],
        },
        "phi": {
            "base_url": f"http://127.0.0.1:{ports['phi']}/v1",
            "model": ids["phi"],
            "port": ports["phi"],
        },
    }
    ENDPOINT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", ENDPOINT)
    return ENDPOINT


def health(timeout: float = 3.0) -> dict:
    """GET /v1/models on both ports from endpoint.json (or defaults)."""
    cfg = json.loads(ENDPOINT.read_text(encoding="utf-8")) if ENDPOINT.exists() else {
        "olmo": {"base_url": "http://127.0.0.1:8000/v1"},
        "phi": {"base_url": "http://127.0.0.1:8001/v1"},
    }
    out = {}
    for key in ("olmo", "phi"):
        url = cfg[key]["base_url"].rstrip("/") + "/models"
        try:
            with urlopen(url, timeout=timeout) as resp:
                out[key] = {"ok": True, "url": url, "body": json.loads(resp.read().decode("utf-8"))}
        except (URLError, OSError, json.JSONDecodeError) as exc:
            out[key] = {"ok": False, "url": url, "error": str(exc)}
    return out


def wait_healthy(seconds: int = 180) -> dict:
    deadline = time.time() + seconds
    last = {}
    while time.time() < deadline:
        last = health()
        if all(v.get("ok") for v in last.values()):
            print("both endpoints healthy")
            return last
        time.sleep(3)
        print("waiting...", {k: v.get("ok") for k, v in last.items()})
    print("timed out; last health:", json.dumps(last, indent=2)[:800])
    return last


def stop() -> None:
    if PIDS.exists():
        data = json.loads(PIDS.read_text(encoding="utf-8"))
        for key, meta in data.items():
            if meta.get("pid"):
                print("killing pid", meta["pid"], key)
                try:
                    if sys.platform.startswith("win"):
                        subprocess.run(["taskkill", "/PID", str(meta["pid"]), "/F"], check=False)
                    else:
                        os.kill(int(meta["pid"]), 15)
                except OSError as exc:
                    print(" ", exc)
            if meta.get("engine") == "docker":
                subprocess.run(["docker", "stop", f"civicdesk-{key}"], check=False)
        PIDS.unlink()
    else:
        for name in ("civicdesk-olmo", "civicdesk-phi"):
            subprocess.run(["docker", "stop", name], check=False, capture_output=True)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["check", "download", "serve", "health", "wait", "all", "stop"])
    p.add_argument("--engine", default="vllm", choices=["vllm", "hf", "docker"])
    p.add_argument("--models", default="olmo,phi", help="comma list: olmo,phi")
    args = p.parse_args(argv)
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    if args.command == "check":
        print(json.dumps(check(), indent=2))
    elif args.command == "download":
        print(json.dumps(download(models), indent=2))
    elif args.command == "serve":
        print(json.dumps(serve(args.engine, models), indent=2))
        print("next: python build_llms.py wait")
    elif args.command == "health":
        print(json.dumps(health(), indent=2))
    elif args.command == "wait":
        print(json.dumps(wait_healthy(), indent=2)[:2000])
    elif args.command == "all":
        print(json.dumps(check(), indent=2))
        download(models)
        serve(args.engine, models)
        print(json.dumps(wait_healthy(), indent=2)[:2000])
    elif args.command == "stop":
        stop()


if __name__ == "__main__":
    main()
