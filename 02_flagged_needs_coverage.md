# How Tier 1 meets the flagged training items

Honest read of what is **built** (prep + three contact days + five aux workshops). CivicDesk fiction only. The awarded workplan described six days; only this three-day path exists in the notebooks.

**Headline:** the course teaches a repeatable classroom path (start two approved small models, keep work files out, retrieve-and-cite, refuse when access or source is missing, inspect not train). It does **not** yet make a ministry able to select, evaluate against a cloud baseline, or maintain open-source AI without the provider.

| Flagged need | Verdict | What is actually in the materials |
|---|---|---|
| Sensitive docs (CVs, Cabinet notes) | Partial | CivicDesk stand-in + INDEX/NEVER + access gate. Live files stay out by design. |
| Select an SLM | Partial | Two pre-chosen models compared (T1-03). No Hub search, no benchmark sheet, no task-to-model criteria lab. |
| Deploy locally | Meets (classroom) | T1-01a + Docker image + `BACKEND` local/demo/shared. Not a ministry production deploy. |
| Configure | Partial | System prompt, `BACKEND`, `WHICH_MODEL`, RAG k/role. No serving/quantisation runbook. |
| Evaluate vs cloud baseline | Partial | T1-03 now scores OLMo and Phi on a frozen GO/BLOCK set. Hosted API is optional and fictional-only; not a Ministry baseline. |
| Maintain without the trainer | Partial | T1-14 is a next workshop, not an ops SOP. No SBOM, patch, or model-update drill. |
| Guardrails + logging | Partial | Data ban, cite-or-abstain, tool allowlist, request logs. No adversarial/prompt-injection lab. |
| Official vs community models | Named only | T1-04 licences (OLMo/Phi/Llama/ChatGPT). No Hub-fork vs publisher-org exercise. |
| Trusted channels + provenance | **Gap** (for learners) | Pinned in `download_models.py` for the consultant. Participants do not keep a source/version register. |
| Data cleaning + metadata | Partial (literacy) | [prep/data_cleaning_and_metadata.md](prep/data_cleaning_and_metadata.md) + PREP-02b: INDEX/NEVER/**HOLD**, Dublin Core labels on a chunk, dataset card vs model card. T1-07 is still policy classification, not a cleaning factory. |
| Paper to softcopy | Partial (awareness) | Tesseract quality page (headings only) + HOLD for image-only / OCR junk. No Tesseract install, no real scans. |
| Terminology / SLM vs LLM / local vs cloud | Meets | Prep + T1-02/03/04 + intervention map. |
| Docker specs (incl. Brev) | Partial / gap on Brev | README has RAM/CPU/GPU notes. No Brev (or other GPU-cloud) spin-up sheet. |
| Own environment if Docker unfit | Meets (classroom runbook + Colab demo) | [03_own_environment.md](03_own_environment.md) for a live stack; [colab/](colab/README.md) for the ideas with scripted replies (not a deploy). |

## Do not over-claim

**Safe:** after Tier 1 a participant can run the approved classroom image, keep ministry files out, and apply cite-or-abstain and human-review rules to a synthetic desk.

**Unsafe:** they can independently select, harden, evaluate, and maintain an open-source SLM on Cabinet or recruitment data.
