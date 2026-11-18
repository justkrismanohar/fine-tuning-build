# Adapters (instructor bake)

Commit these folders after a real `TrainSession` run on a course T4:

| Folder | Training data |
|---|---|
| `olmo-criteria-lora-v1/` | `../data/criteria/train_v1.json` |
| `olmo-tickets-lora-v1/` | `../data/tickets/train_v1.json` |
| `olmo-resume-redact-lora-v1/` | `../../shared/resume_redaction/data/train_clean_v1.json` |

Each folder needs adapter weights, `adapter_config.json`, and a measured `training_report.json` (`status: trained`).

Bake:

```bash
python train_adapter.py --task criteria --max-steps 40 --out adapters/olmo-criteria-lora-v1
python train_adapter.py --task tickets --max-steps 30 --out adapters/olmo-tickets-lora-v1
python train_adapter.py --task redact --max-steps 40 --out adapters/olmo-resume-redact-lora-v1
```

Until these exist, `load_adapter("prebuilt")` raises a clear error and notebooks fall back to RECORDED files under `logs/recorded/` when present.
