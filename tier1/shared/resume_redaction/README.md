# Résumé redaction benchmark: Day 1 baseline, Day 3 reuse

- Test split: data/resume_redaction_test_v1.json, sha256 c299eb39a169f639fd72b48963fe1154d7c9b4a0786eb4a87354dcd3ccbdd370. Frozen. Never used to train, tune prompts, choose examples or set thresholds.
- Scorer and rule: redaction_eval.py (evaluate, summary_table, check_rule with EXAMPLE_RULE). Day 3 uses the same file and the same rule. Changing either after seeing results starts a new comparison.
- Prompted baseline: baselines/olmo_baseline_v1.json (prompt redact-prompt-v1, measured in the container image).
- Day 3 adds one run file per variant (e.g. baselines/olmo_adapter_v1.json) with the same fields, plus the adapter name, base model revision and training-data version.
- Day 3 training and validation data must be built from different name, street and email pools than build_benchmark.py's TEST_POOLS, with a different seed, and must not copy any test text. Assert no PII value overlaps the test split. The test uses the same 7 layouts plus a no-PII category, so it measures generalisation to new people and values, not to new layouts. A held-out-layout set is a separate decision.
- Report both runs side by side: the rule criteria, recall by type, acceptable-as-is by category, and the documents where the two runs disagree (fixed by the adapter / broken by the adapter). With 40 documents, one- or two-document differences are noise-sized; say so.
- Possible outcomes are better, worse or mixed. None is assumed. A pass on this set is classroom evidence, not release permission.
- Teaching set (data/teaching_set_v1.json) is for the worked example only. It is neither benchmark nor training data.
