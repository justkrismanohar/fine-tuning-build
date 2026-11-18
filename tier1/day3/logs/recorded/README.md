# Recorded compare runs

Instructor bake writes measured files here (same code path as `ft_train.compare_live`):

- `criteria_compare_v1.json`
- `tickets_compare_v1.json`

Also write `../../shared/resume_redaction/baselines/olmo_adapter_v1.json` for the 40-document redaction benchmark.

Each file must include `date`, `gpu`, and `"measured": true`. Notebooks print:

`RECORDED run from <date> on <GPU>, not this session.`
