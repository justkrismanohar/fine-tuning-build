"""Run Day 2 and Day 3 notebooks; save executed copies under each day's completed/."""
from __future__ import annotations

import io
import json
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DAYS = [ROOT / "day2", ROOT / "day3"]


def cell_source(cell: dict) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src or ""


def stream(name: str, text: str) -> dict:
    return {"output_type": "stream", "name": name, "text": text}


def error_output(exc: BaseException) -> dict:
    return {
        "output_type": "error",
        "ename": type(exc).__name__,
        "evalue": str(exc),
        "traceback": traceback.format_exc().splitlines(),
    }


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
            if text_out:
                outputs.append(stream("stdout", text_out))
            if text_err:
                outputs.append(stream("stderr", text_err))
            outputs.append(error_output(exc))
            cell["outputs"] = outputs
            raise RuntimeError(f"{path.name} cell {count} failed:\n{src[:400]}\n{exc}") from exc
        text_out, text_err = out_buf.getvalue(), err_buf.getvalue()
        if text_out:
            outputs.append(stream("stdout", text_out))
        if text_err:
            outputs.append(stream("stderr", text_err))
        cell["outputs"] = outputs
    nb.setdefault("metadata", {})
    nb["metadata"]["civicdesk_executed"] = True
    return nb


def main() -> None:
    written = []
    for day in DAYS:
        sys.path.insert(0, str(day))
        completed = day / "completed"
        completed.mkdir(exist_ok=True)
        names = sorted(p.name for p in day.glob("T1-*.ipynb"))
        for name in names:
            src = day / name
            print("executing", src.relative_to(ROOT))
            old_cwd = Path.cwd()
            try:
                import os

                os.chdir(day)
                executed = execute_notebook(src)
            finally:
                os.chdir(old_cwd)
            dest = completed / name
            for cell in executed.get("cells", []):
                if cell.get("cell_type") != "markdown":
                    continue
                src = cell.get("source", "")
                if isinstance(src, list):
                    cell["source"] = [line.replace("(images/", "(../images/") for line in src]
                elif isinstance(src, str):
                    cell["source"] = src.replace("(images/", "(../images/")
            dest.write_text(json.dumps(executed, indent=1, ensure_ascii=False), encoding="utf-8")
            written.append(dest)
            print("  saved", dest.relative_to(ROOT))
        if str(day) in sys.path:
            sys.path.remove(str(day))
    print("done", len(written), "notebooks")


if __name__ == "__main__":
    main()
