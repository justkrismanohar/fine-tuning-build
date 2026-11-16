import json
from pathlib import Path

p = Path(__file__).with_name("completed") / "T1-08b_pdf_vector_rag.ipynb"
nb = json.loads(p.read_text(encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    if i < 18:
        continue
    src = "".join(c["source"])
    print("--- cell %d %s ---" % (i, c["cell_type"]))
    print(src)
    print()
