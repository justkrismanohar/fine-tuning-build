# Example transfer card (classroom key)

Not a pilot. Load only if stuck; mark “loaded from reference.”

- Organisation / cluster: CivicDesk Labour screening / A
- Job: First-pass résumé criteria with human_review as the default for silence
- First intervention: inspect-adapter (after a live pre-flight on the frozen set)
- Rejected: prompt-only (the 1B model copied the example and still marked silence as a fail); RAG (no circular to retrieve); integration (not a register); none (the desk already gets CVs)
- Verifier: HR officer checks every `meets` / `does_not_meet` and every empty-evidence `human_review`
- Stop: Do not hire; do not turn silence into does_not_meet; do not release a redacted copy to a panel
- Data out: Real CVs, national IDs, tickets with real names, the frozen held-out cases as train rows
- Box: Course-controlled or ministry VPC (N7)
- Burst vs standing: Standing = chat API on :8000. Burst = LoRA job on criteria rows, then stop
- Tools never: reset_password, write_glpi, award_contract, release_to_panel, auto_release_if_pass_checks
- Audit: request id, prompt version, gold file sha256, predicted label, evidence substring check
- Question for MPAAI: Who owns the gold labels when a stricter unit would call an unrelated degree does_not_meet?
- First safe next step: Re-run the 18 held-out criteria on the classroom OLMo; keep the evidence floor; do not go live
- Policy for silence: human_review, never does_not_meet
