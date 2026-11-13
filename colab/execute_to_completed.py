"""Run Colab-track notebooks; save executed copies under each day's completed/."""
from __future__ import annotations

import io
import json
import os
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAYS = ["day1", "day2", "day3"]


def cell_source(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else (src or "")


def execute_notebook(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    env: dict = {"__name__": "__main__"}
    count = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        count += 1
        cell["execution_count"] = count
        src = cell_source(cell)
        out_buf, err_buf = io.StringIO(), io.StringIO()
        outputs: list[dict] = []
        try:
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                exec(compile(src, str(path), "exec"), env, env)
        except Exception as exc:
            text_out, text_err = out_buf.getvalue(), err_buf.getvalue()
            tb = traceback.format_exc()
            raise RuntimeError(
                f"{path.name} cell {count} failed:\n{src[:500]}\n{exc}\n{tb}"
            ) from exc
        if out_buf.getvalue():
            outputs.append({"output_type": "stream", "name": "stdout", "text": out_buf.getvalue()})
        if err_buf.getvalue():
            outputs.append({"output_type": "stream", "name": "stderr", "text": err_buf.getvalue()})
        cell["outputs"] = outputs
    nb.setdefault("metadata", {})
    nb["metadata"]["civicdesk_executed"] = True
    nb["metadata"]["civicdesk_track"] = "colab-demo"
    return nb


def main() -> None:
    os.environ["CIVICDESK_COLAB"] = "1"
    os.environ["CIVICDESK_MODE"] = "demo"
    written = []
    old = Path.cwd()
    try:
        for day in DAYS:
            folder = HERE / day
            completed = folder / "completed"
            completed.mkdir(exist_ok=True)
            for src in sorted(folder.glob("T1-*.ipynb")):
                print("executing", src.relative_to(HERE))
                os.chdir(folder)
                executed = execute_notebook(src)
                dest = completed / src.name
                for cell in executed.get("cells", []):
                    if cell.get("cell_type") != "markdown":
                        continue
                    src_txt = cell.get("source", "")
                    if isinstance(src_txt, list):
                        cell["source"] = [line.replace("(images/", "(../../tier1/" + day + "/images/") for line in src_txt]
                    elif isinstance(src_txt, str):
                        cell["source"] = src_txt.replace("(images/", "(../../tier1/" + day + "/images/")
                dest.write_text(json.dumps(executed, indent=1, ensure_ascii=False), encoding="utf-8")
                written.append(dest)
                print("  saved", dest.relative_to(HERE))
                # Drop imported helpers so the next notebook re-imports with cwd/bootstrap
                for mod in list(sys.modules):
                    if mod.startswith("civicdesk") or mod in {"build_llms"}:
                        del sys.modules[mod]
    finally:
        os.chdir(old)
    print("done", len(written), "notebooks")


if __name__ == "__main__":
    main()
