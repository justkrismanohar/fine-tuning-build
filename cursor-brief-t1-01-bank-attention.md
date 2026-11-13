# Cursor brief: T1-01 first call, context, attention and instructions

This brief tells Cursor how to add one teaching exercise to `tier1/day1/T1-01_first_call.ipynb` in `justkrismanohar/fine-tuning-build`. The exercise follows the way Kris explains it in class: run a first call, compare two unfinished "bank" sentences, look at tokens and embeddings, explain attention as spotlights, connect the weights to training, then rerun the same sentences under a banking-only system instruction to show that instructions steer outputs without changing weights, and that the model may not comply.

Scope is Day 1 only. Detailed layer names, LoRA target modules and adapter work stay in Day 3.

## Ground truth (checked against the repo, commit 0bb94f9, 12 Nov 2026)

- **Notebook to edit:** `tier1/day1/T1-01_first_call.ipynb`, 19 cells, nbformat 4.5, every cell has an `id`.
- **Do not run `tier1/day1/build_day1_notebooks.py`.** Its T1-01 section is out of date: only 9 of the 19 cells in the committed notebook match what it generates (it still has the old "comparison pad" cells). Running it would overwrite the current T1-01 and the other Day 1 notebooks.
- **Call path:** notebooks call `civicdesk_lab.chat(messages, model=...)`. It posts to `{url}/chat/completions` with `temperature: 0.0` and `max_tokens: 256` hard-coded in `_post_chat`. There is no `max_tokens` argument yet.
- **Backends:** `demo` returns canned text from `_demo_reply`. Today the two bank sentences would fall through to the generic reply ("CivicDesk reply: I can draft from the text you sent..."), which would be misleading.
- **Cloud container:** `Dockerfile` installs CPU torch, `transformers` and `accelerate`, and bakes OLMo and Phi into `/models/olmo` and `/models/phi` (`HF_HOME=/models/hf-cache`, `CIVICDESK_MODELS_DIR=/models`). `environment/docker-entrypoint.sh` starts `hf_openai_server.py` for each model on :8000 and :8001 and writes `logs/endpoint.json` with backend `local`. So in the container the servers already hold the weights; the notebook kernel must not load them again.
- **`hf_openai_server.py`** serves only `/v1/chat/completions` and `/v1/models`. It always applies the chat template and decodes greedily. It has no raw `/v1/completions` route and returns no token probabilities, so top-k next-token probabilities are not cheap in the container and are out of scope here.
- **OLMo facts read from `allenai/OLMo-2-0425-1B-Instruct` config.json:** 16 transformer blocks, 16 attention heads per block, 2,048 numbers per token vector, vocabulary of 100,352 tokens, about 1.49 billion parameters.
- **Tokenizer check (real OLMo tokenizer, `add_special_tokens=False`):** " bank" is token ID 6201 in both sentences. The money sentence is 15 tokens, the river sentence 16. "I" at the start (ID 40) and " I" mid-sentence (ID 358) are different tokens.
- **Neighbouring notebook:** `T1-02_tokens_and_transformer.ipynb` already has a stand-in tokenizer (`lab.naive_tokens`) and the architecture card (tokenizer, embedding, transformer block × N with attention then feed-forward, language-model head). Reuse that vocabulary. Do not edit T1-02 in this change.

### One test run of the prompts (evidence, not a promise)

I ran the repo's own `hf_openai_server.generate` (the function the container serves) on OLMo-2-0425-1B-Instruct, CPU, greedy, transformers 5.22.2 and torch 2.15. These are not the container's exact versions, because the Dockerfile does not pin them.

- Continue-the-sentence system text: money sentence gave "deposit it."; river sentence gave "catch some fish for dinner." About 2 seconds each for a short reply.
- Banking-only system text: river sentence was politely flagged as outside banking. The money sentence got a hedged half-refusal ("While I can't assist with your visit to the bank, I can certainly help answer questions you might have about check deposits..."), which is itself a useful compliance lesson. About 11 seconds each at a 40-token cap.

The notebook text must not quote these as expected outputs. Learners read their own replies.

## The teaching thread to preserve

Kris's explanation, kept in his framing, with the corrections the notebook must carry:

1. **First call.** Send a prompt, get text back.
2. **Two unfinished sentences.** "I need to deposit my check, so I'm going to the bank to" and "I've got my fishing rod, so I'm heading to the river bank to". Same ending, different continuations. The model used the earlier words.
3. **Tokens and embeddings.** Text becomes token IDs. Each ID picks a row from a learned table (the embedding). " bank" starts as the same row in both sentences.
4. **Attention as spotlights.** At each position the model shines spotlights back over the words available so far and mixes in what they light up. Many spotlights (heads) work at once, and the block repeats (16 times in OLMo), so the representation of "bank" and of the last position gets refined layer by layer. By the end, the internal representation at the last position is different in the two sentences, so the scores for the next token differ.
5. **Weights and training.** The spotlights, the mixing and the embedding table are all weights. Training adjusted those weights to reduce the average error in predicting the next token over a large body of text. That is how the model picked up general ways of combining context. Nobody wrote a rule that says "river near bank means riverbank." Task-specific work may need adaptation (Day 3: keep the base frozen, train a small add-on, which Kris describes as "shifting the beams").
6. **Instructions.** Rerun the same two sentences with a system instruction: answer only financial-banking questions, politely flag anything else. The reply changes, but no weight changed. The instruction is more context for the same spotlights. Compliance is not guaranteed.

Corrections the text must state, briefly and in plain words:

- Heads have no fixed, assigned jobs such as "the finance head." What a head does is learned and often mixed.
- Attention maps are not reliable explanations of why the model produced a word. The spotlight figure is an illustration, not a measurement.
- The prediction does not show what the model "means" by bank. It shows which next tokens scored high.
- Internal contextual representations (inside the blocks) are not the same thing as the final next-token probabilities (the head's output at the last position).
- Day 3 bridge only: an adapter such as LoRA can change attention projections, feed-forward projections or both, not only "redirect the beams." Which parts to adapt comes from tested recipes in Day 3, not guesses. Leaving a kind of example out of training does not guarantee the model fails on it; that has to be measured.
- Instruct models wrap your text in a chat template. That is why the first call tells the model to continue the sentence; it is not a raw text-completion call.

## Scope

In scope:

- New cells in T1-01 (listed below), two small edits to existing T1-01 cells, a write-up addition.
- Small, backward-compatible helpers in `tier1/day1/civicdesk_lab.py`.
- Four diagrams in `tier1/day1/images/` plus the script that draws them.
- A completed reference copy of T1-01 with real live outputs, if a live run is possible.
- A one-line warning comment in `build_day1_notebooks.py`.

Out of scope (leave for Day 3 or the deep track):

- Printing module names, listing `q_proj` / `qkv_proj` etc., or choosing LoRA targets.
- Loading model weights in the notebook kernel, loading OLMo and Phi together, or downloading anything new.
- Raw `/v1/completions`, logprobs or top-k probabilities (the container's server cannot do it).
- Attention maths (queries, keys, values, softmax formulas) and architecture design.
- Edits to T1-02 or any other notebook, the Dockerfile, the entrypoint or the server.

## Files to change

| File | Change |
|---|---|
| `tier1/day1/civicdesk_lab.py` | `max_tokens` pass-through, tokenizer and config helpers, demo branch |
| `tier1/day1/T1-01_first_call.ipynb` | 11 new cells, 3 edited cells |
| `tier1/day1/images/make_t1_01_context_diagrams.py` | New: draws the four PNGs (author machine only) |
| `tier1/day1/images/t1_01_*.png` | New: four diagrams |
| `tier1/day1/completed/T1-01_first_call.ipynb` | New: executed live copy (only if a live run works) |
| `tier1/day1/build_day1_notebooks.py` | One comment above the T1-01 section |

Nothing else changes.

## Helper changes in civicdesk_lab.py

Keep every existing default so other notebooks behave exactly as before.

1. **`max_tokens` pass-through.** Add `max_tokens: int = 256` to `chat()` and to `_post_chat()`, and send it in the request body instead of the literal 256. Temperature stays 0.0. Short continuations matter in the container because the servers run on CPU.

2. **`load_tokenizer()`**, tokenizer files only, never weights:
   - Try `AutoTokenizer.from_pretrained(<CIVICDESK_MODELS_DIR or /models>/olmo)` if that folder exists.
   - Else try `AutoTokenizer.from_pretrained(OLMO_ID, local_files_only=True)`.
   - Else return `(None, "stand-in")` so the notebook falls back to `naive_tokens` and says so.
   - Return `(tokenizer, source_label)`. Import `transformers` inside the function so `civicdesk_lab` still imports where transformers is missing.
   - Never call `AutoModel*` or `from_pretrained` on a model class anywhere in this change.

3. **`show_tokens(text, tok)`** prints a compact two-column list of token piece and ID (`add_special_tokens=False`, pieces via `tok.decode([id])` shown with `repr` so leading spaces are visible). With `tok=None`, print `naive_tokens(text)` and the label "stand-in tokenizer, not OLMo's; IDs not available".

4. **`model_shape()`** reads `config.json` as plain JSON from `<models dir>/olmo/config.json`, or from the Hugging Face cache with `local_files_only=True` via `huggingface_hub.hf_hub_download`. Return `num_hidden_layers`, `num_attention_heads`, `hidden_size`, `vocab_size` and the source path. If nothing is found locally, return the reference values from this brief with source `"reference values for OLMo-2-0425-1B-Instruct (config not found on this machine)"`. No download.

5. **Demo branch.** In `_demo_reply`, before the generic fallback and after the existing `unrestricted` / `always invent` checks, add a branch for user text containing `"bank to"`. It must not invent a continuation. Suggested text: `"[{model} demo] No live model on this backend, so there is no real continuation to read. Switch BACKEND to local or shared, or open completed/T1-01_first_call.ipynb for a recorded live run."`

## Notebook changes

### Edits to existing cells

- **Cell `543a6776` (title and outcomes):** add one outcome bullet: "See that the model uses earlier words (context) to continue text, name tokens, embeddings and attention in plain words, and see that a system instruction steers the reply without changing the weights."
- **Cell `e206042a` ("After you run"):** change the last line from "Next: **system vs user**, then `WHICH_MODEL`..." to "Next: your first real call, two "bank" sentences, then **system vs user** and `WHICH_MODEL` with your ministry request."
- **Cell `38a66ff6` (write-up):** add two questions after question 1:
  - "Both bank sentences end with the same words. What in the earlier words changed the continuation, and how would you explain that with the spotlight picture?"
  - "Under the banking-only instruction, did each reply do what the instruction asked? What changed in the model's weights between the two runs?" (Answer: nothing.)

Leave every other existing cell and its outputs untouched.

### New cells

Insert eleven cells, in this order, between cell `e206042a` and cell `a280644d` ("System text vs user text"). Give each a new unique 8-character hex `id`. Leave outputs empty in the student notebook. Tags follow the repo's convention: `# [RUN]`, `# [CHANGE]`, `# [OPTIONAL]`. Every code cell must run on all four backends; on `demo` it prints the demo label and a pointer to the completed copy.

**N1, markdown: "Your first real call: how does the model use context?"**
- Two or three sentences: the model continues text one token at a time; we give it two unfinished sentences that end the same way.
- Show both sentences in a quote block.
- Diagram: `images/t1_01_tokens_to_next_token.png` with alt text.
- One line: "Read what comes back. Do not expect a particular answer."

**N2, code `# [RUN]`: send the two sentences.**
- Define `BANK_MONEY`, `BANK_RIVER` (exact strings above) and `CONTINUE_SYSTEM = "Continue the user's unfinished sentence with a few words. Output only the continuation."`
- `model_id = lab.resolve_model(globals().get("WHICH_MODEL"))` (OLMo by default, matching cell `5537c22c`).
- For each sentence call `lab.chat([...system, user...], model=model_id, max_tokens=24)`.
- Print `mode`, `model`, `latency_ms`, the sentence and the reply. Store results in `bank_runs = {"money": ..., "river": ...}` for N10.
- If `mode` is not `live`, print: "Demo or fallback: this is not a model reply. Use local or shared, or the completed copy." If `error` is present, print it, as cell `d072bbf9` does.

**N3, markdown: "After you run: paired reflection"**
- Same last words, "the bank to". Different earlier words. Which earlier words do you think mattered most?
- Would a keyword filter for "bank" tell these two apart? What does the model have that the filter does not?
- Note: this wrapper uses temperature 0, so rerunning gives the same reply. To change the reply, change the input.
- Note: OLMo here is an instruct model. Your text was wrapped in a chat template, which is why the system line asks it to continue the sentence.

**N4, code `# [RUN]` with one `# [CHANGE]` line: tokens.**
- `tok, source = lab.load_tokenizer()`; print `source`.
- `lab.show_tokens(BANK_MONEY, tok)` and `lab.show_tokens(BANK_RIVER, tok)`.
- Compute (do not hard-code) the ID of " bank" in each and print "' bank' has ID X in the money sentence and Y in the river sentence". On the real tokenizer X equals Y.
- `MY_TEXT = "I sat on the bank of the river"  # [CHANGE] try your own sentence` then `lab.show_tokens(MY_TEXT, tok)`.
- With the stand-in tokenizer, print that IDs are not available and continue.

**N5, markdown: "Embeddings: the same starting point"**
- Each token ID picks one row from a learned table. For OLMo that table has one row per vocabulary entry, and each row is a list of numbers (N6 prints the sizes).
- " bank" starts as the same row in both sentences. The table has no idea which bank you mean.
- Small aside: "I" at the start and " I" in the middle are different tokens, so spaces matter.
- Diagram: `images/t1_01_same_id_same_start.png`.

**N6, code `# [RUN]`: the size of the machine, from the config file only.**
- `shape = lab.model_shape()`; print source, then plain lines: vocabulary size, numbers per token, transformer blocks, attention heads per block.
- Comment in the cell: `# Reads a small text file. Does not load the model.`
- No module listing, no parameter-by-layer printout.

**N7, markdown: "Attention: spotlights over the words so far"**
- The spotlight explanation from step 4 of the teaching thread, in Kris's words.
- Many spotlights per block (heads), and the block repeats: read the number from N6.
- Internal representation versus final scores: inside the blocks, every token's representation is updated with context; at the end, only the last position is turned into scores for the next token. That is where the two sentences part ways.
- Diagram: `images/t1_01_attention_spotlights.png` with the caption "Illustration. Not a measured attention map."
- A short "Careful with the picture" list: heads have no assigned jobs; attention pictures are not reliable explanations; a prediction does not show what the model means.

**N8, markdown: "Where the spotlights come from: weights and training"**
- The embedding table, the spotlights and the mixing are all weights, the numbers baked into the files T1-01a served.
- Training adjusted those numbers to reduce the average next-token error over lots of text. It learned general ways of combining context; nobody wrote a riverbank rule.
- Today nothing is trained. Everything is frozen.
- Day 3 preview, two sentences at most: for specialist work you can keep the base frozen and train a small add-on that changes how the model processes text ("shift the beams"). Which parts it changes, and whether it helps, is a Day 3 measurement.
- Diagram: `images/t1_01_input_vs_weights.png`.

**N9, markdown: "Same sentences, new standing instruction"**
- Set up the rerun: the system text now says the assistant handles financial-banking questions only and politely flags anything else.
- Ask learners to predict, before running, what each sentence should get.

**N10, code `# [CHANGE]`: rerun with a banking-only instruction.**
- `BANKING_ONLY_SYSTEM = ("You are a CivicDesk assistant for financial banking questions only. If the message is not about financial banking, say politely that it is outside what you can help with. Otherwise continue the user's unfinished sentence with a few words.")  # [CHANGE] edit and re-run`
- Send both sentences with `max_tokens=60`.
- For each, print the reply from N2 (`bank_runs`) and the new reply one under the other, with `mode` and `model`.
- Save evidence with `lab.save_log("T1-01_bank_pair", {...})`: backend config, model, both system texts, both sentences, all four replies, and `"followed_instruction": {"money": "", "river": ""}  # [CHANGE] yes / no / partly`.
- If N2 was skipped (`bank_runs` missing), print a one-line hint to run N2 first instead of raising.

**N11, markdown: "After you run: instructions steer, they do not retrain"**
- Between N2 and N10 no weight changed. The instruction is more context for the same spotlights, and it moved the replies.
- Compliance is not guaranteed. Check each reply: did it answer the banking sentence, did it flag the river sentence, was it polite? A partial refusal or a missed flag is a normal result, not a broken notebook.
- The river sentence contains the word "bank." Telling it apart needs context, which is the same lesson as N3.
- For a ministry desk, an instruction is one layer. Checks outside the model and a human reviewer still matter (Day 2 and Day 3).
- Bridge: "The next section does the same thing with CivicDesk rules: same visitor, different wall."

The existing "System text vs user text" section (`a280644d`) then follows unchanged.

## Diagrams

Draw them with `tier1/day1/images/make_t1_01_context_diagrams.py` (matplotlib, run once on the author's machine, PNGs committed). Do not add matplotlib to `environment/requirements.txt`. Projector-readable fonts, plain colours, no attention numbers that look measured.

1. `t1_01_tokens_to_next_token.png`: your text → tokens (IDs) → embeddings (table lookup) → transformer block × 16 (attention, then feed-forward) → scores for the next token → chosen token added, repeat. Use the same words as the T1-02 architecture card.
2. `t1_01_same_id_same_start.png`: both sentences tokenised, " bank" highlighted in each, both pointing to the same row (ID 6201) in one embedding table.
3. `t1_01_attention_spotlights.png`: the two sentences side by side; beams from "bank" / the last "to" back toward "deposit" and "check" in one, "fishing", "rod" and "river" in the other. Caption on the image: "Illustration. Not a measured attention map."
4. `t1_01_input_vs_weights.png`: two levers. Left: change the input (system text, user text), weights unchanged, used today. Right: change the weights (training, or a small adapter), Day 3.

## Completed reference copy

The notebook banner tells stuck learners to open the matching file in `completed/`, but `tier1/day1/completed/` has no T1-01 yet, and `tier1/execute_to_completed.py` only covers Days 2 and 3.

- In the cloud container (servers already up), set `BACKEND = "local"` in a scratch copy and run `jupyter nbconvert --to notebook --execute --output completed/T1-01_first_call.ipynb T1-01_first_call.ipynb` from `tier1/day1`, with `HF_HUB_OFFLINE=1`.
- Keep it only if the new cells show `mode: live` and the tokenizer source is the OLMo tokenizer. Do not hand-write or edit outputs. If a live run is not possible, skip this file and say so in the change summary.
- Do not change `execute_to_completed.py`.

## Builder warning

Above the `# T1-01` section of `build_day1_notebooks.py`, add: `# WARNING: T1-01_first_call.ipynb is maintained by hand and has moved past this section. Do not regenerate; it would overwrite the current notebook.` No other builder edits.

## Teacher script (for the facilitator notes in N7 and N11)

Keep Kris's analogy and voice; the bracketed lines are the corrections to say out loud.

> "Both sentences end with 'the bank to'. The model came up with different endings, so it must be using what came before. Here's how. First the words become tokens, numbers. ' bank' is the same number in both sentences, and it looks up the same starting row of numbers. So at the start, the model has no idea which bank.
>
> Then attention. Think of spotlights. At each word, the model shines spotlights back over everything so far and mixes in what they light up. In the money sentence the light can land on 'deposit' and 'check'. In the river sentence, on 'fishing rod' and 'river'. There are many spotlights at once, and this happens again and again, sixteen blocks deep in OLMo, so the picture of the sentence gets sharper each time. By the end, the last position looks different in the two sentences, and so do the scores for the next word.
>
> [This is a picture, not a measurement. No spotlight has a fixed job like 'the finance head', and you can't read the model's reasons off an attention map.]
>
> Where do the spotlights come from? Training. The model saw a huge amount of text and its weights were nudged to get better, on average, at predicting the next word. That's how it learned general ways of combining context. Nobody programmed a riverbank rule.
>
> [On Day 3 we'll see that a small adapter can shift the beams for a specialist task. It can change more than attention, and whether it helps is something we measure.]
>
> Now watch. Same two sentences, but I tell it: banking questions only, politely flag anything else. The replies change, and I haven't touched a single weight. The instruction is just more context. And look closely: did it actually follow it? It might not. That's why the instruction is one layer, not the whole safety plan."

## Acceptance checks

Cursor reports the result of each check in its change summary.

1. **Diff scope:** `git diff --stat` touches only the files in the table above. No other notebook, the Dockerfile, the entrypoint or `hf_openai_server.py` changed. The builder was not run.
2. **Notebook validity:** `nbformat.validate` passes on the edited notebook; all cell ids are unique; the 19 original cells are still present in order, with only `543a6776`, `e206042a` and `38a66ff6` edited.
3. **Demo run:** with `BACKEND = "demo"`, executing every cell top to bottom finishes without an exception. N2 and N10 print the demo label, never a made-up continuation.
4. **Live run in the container:** with `BACKEND = "local"`, N2 and N10 show `mode: live`, four non-empty replies, and `logs/T1-01_bank_pair.json` is written. N4 reports the OLMo tokenizer and prints the same ID for " bank" in both sentences (6201 on the OLMo-2-0425-1B-Instruct tokenizer), computed, not hard-coded.
5. **No downloads, no weights:** with `HF_HUB_OFFLINE=1` the tokenizer and config cells still work. A search of the new code and helpers finds no `AutoModel`, `from_config`, `init_empty_weights` or model `from_pretrained` calls.
6. **Backward compatibility:** `lab.chat(messages)` without `max_tokens` still sends 256; existing cells `5537c22c` and `d072bbf9` give the same demo output as before.
7. **No promised outputs:** no markdown cell states what the model will say. A search for phrases such as "will say", "should continue with" and "withdraw" in the new cells finds nothing.
8. **Day 3 boundary:** no new cell names `q_proj`, `k_proj`, `v_proj`, `o_proj`, `qkv_proj`, `gate_proj`, `target_modules` or prints the module tree.
9. **Diagrams:** all four PNGs render in JupyterLab from their relative paths, have alt text, and the spotlight image carries its "not a measured attention map" caption.
10. **Completed copy:** either present with real `mode: live` outputs, or absent with a line in the summary explaining why.
11. **Not pushed:** Cursor leaves the work as local changes or a branch for Kris to review.

## Decisions for Kris

- **Time:** the new section is roughly 20 minutes inside a 40-minute slot (09:50 to 10:30). In the cloud container the servers start on their own, so T1-01a can shrink to its health check to make room. Changing the times in the notebook header and the Day 1 README is your call; this brief leaves them alone.
- **Overlap with T1-02:** T1-01 now introduces real tokens, embeddings and attention, and T1-02 opens with the stand-in tokenizer and the same architecture card. T1-02 may want trimming later.
- **Default backend:** T1-01 defaults to `BACKEND = "demo"`, but the container's servers are already running. Learners in the container must switch to `local` to see real replies; you may want the facilitator to say this first, or change the default later.
