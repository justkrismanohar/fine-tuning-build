# Architecture card — Day 3

Keep beside the Day 1 card.

```
input text
    → tokenizer
    → embedding
    → transformer block × N     ← a LoRA adapter may sit here as a small extra file
    → language-model head
    → next token, repeat
```

| Word | Today |
|---|---|
| **Frozen** | OLMo/Phi weights do not update. Same files as Day 1. |
| **Adapter / LoRA** | A small extra file. Can be swapped or rolled back. Not a database. |
| **SFT row** | Instruction + input + desired output. Fiction only. |
| **Burst** | A training job on a bigger GPU, then stop. |
| **Standing** | The chat API that stays up (`:8000` / `:8001`). |
| **Canary** | Planted PII. Must not be in a real train split. If the model quotes it, fail. |
