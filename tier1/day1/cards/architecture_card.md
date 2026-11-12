# Architecture card — introduced T1-02, reused Day 3 and T2-07

```
input text
    → tokenizer                 text to token IDs
    → embedding                 IDs to vectors
    → transformer block × N     attention, then feed-forward
    → language-model head       vector to next-token scores
    → chosen token appended; repeat until stop
```

| Method | What moves | What is added |
|---|---|---|
| Prompting or RAG | Nothing (all frozen) | Extra text, or retrieved chunks in the prompt |
| Instruction tuning | Already done on the Instruct models they receive | They do not repeat this |
| Full-weight fine-tuning | Embedding, all blocks, head | Nothing detachable. Usually refused in this course |
| LoRA / PEFT | Base frozen; small adapter beside attention; head frozen | A small adapter file, kept separate from the base |

**Day 1:** shade nothing. Everything is frozen. This is inference.

**Day 3:** shade LoRA. Mark burst GPU (train, then stop) vs standing inference (this chat).
