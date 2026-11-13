# Cursor spec: T1-02 with OLMo's real tokenizer and a working temperature demo

This spec tells Cursor how to rebuild `tier1/day1/T1-02_tokens_and_transformer.ipynb` in `justkrismanohar/fine-tuning-build`. The notebook should use OLMo's real tokenizer in place of the word-splitter, count a full chat request honestly, show a finance-only system instruction, and fix the temperature comparison so the setting actually reaches the model. It is grounded in the repo as it stood at commit `0bb94f9` (Thursday, November 12, 2026, 4:50 PM AST). Nothing in the repo has been changed or pushed; Cursor makes every change below.

Audience and setting stay as they are: Tier 1, mixed levels, people run ready cells and edit only `# [CHANGE]` lines. The course runs in a cloud-hosted container the learner opens from a link, with OLMo already serving on `:8000`. The notebook loads no model weights, starts no second model and downloads nothing.

## 1\. Ground rules for Cursor

- **Edit the generator, then regenerate only T1-02.** The notebooks are written by `tier1/day1/build_day1_notebooks.py`. Running that script as it stands rewrites every Day 1 notebook. The committed `T1-01_first_call.ipynb` has been hand-edited since the script last produced it (the text of cells 0, 1, 2, 7 to 10 and 13 to 18 differs from what the script writes), so a full run would overwrite that work. Add an `--only` filter (section 6\) and regenerate with `python build_day1_notebooks.py --only T1-02`. After regenerating, `git diff --stat` must show no change to any other notebook.  
- **No weights, no network, no second model.** The tokenizer is loaded from the files already baked into the image. Never call `AutoModel*`, never open `model.safetensors`, never call `snapshot_download` from a required cell.  
- **Print what the tokenizer did; don't assert what it should do.** Learner cells compute and print IDs, pieces and counts. No cell or teaching note may claim that "bank" is always one token or always the same ID. The reference numbers in section 3 are for the facilitator and the tests, not text for the notebook.  
- **Keep backward compatibility.** `lab.chat(messages)` and `lab.chat(messages, model=...)` are used in T1-01 and T1-03 and must send exactly what they send today. `naive_tokens` stays in the helper.  
- **Keep the useful parts.** That means the architecture card, the fictional ministry sentences A to D with their "stands in for" table, the N12 line, the context-window link to Day 2 chunking, the decoding note's Labour/Health/OPR versus Trade sentence, and the "what is frozen" question.

## 2\. What is there now

### The notebook (9 cells)

| \# | Type | Content today |
| :---- | :---- | :---- |
| 0 | md | Title, 10:45 to 12:00, outcomes, BANNER |
| 1 | md | Ministry link table (A to D), N12, overnight readers |
| 2 | md | Architecture card |
| 3 | code | Sentences A to D counted with `lab.naive_tokens` |
| 4 | md | Teaching note: "the classroom tokenizer is a stand-in" |
| 5 | code | `# [CHANGE]` probe, again `naive_tokens` |
| 6 | code | Temperature loop: labels temp 0 and 0.9, calls `lab.chat(messages)` with no temperature |
| 7 | md | Decoding note |
| 8 | md | Write-up (3 questions) |

The day plan lists the evidence as "token checkpoint \+ marked architecture card", but no cell saves a log. There is no `completed/T1-02` copy, although the BANNER tells stuck learners to load one.

### Why the temperature demo cannot work

The value is lost at three points:

1. **Notebook:** the loop never passes `temp` to `lab.chat`.  
2. **Helper:** `chat(messages, model=None, timeout=60.0)` takes no sampling arguments, and `_post_chat` hard-codes `"temperature": 0.0, "max_tokens": 256`. Demo mode returns canned text from `_demo_reply` whatever the setting.  
3. **Server in the container:** `environment/docker-entrypoint.sh` serves OLMo with `tier1/day1/hf_openai_server.py` and writes `"engine": "hf"`. That server reads only `messages` and `max_tokens`, always calls `generate(..., do_sample=False)`, and returns no `usage`. So in the click-a-link container, temperature would have no effect even if the helper sent it.

The vLLM path (`build_llms.py serve --engine vllm` or `--engine docker`) forwards the request body to vLLM unchanged, so fixing the helper is enough there. One more gap: `use_backend()` rewrites `logs/endpoint.json` without the `engine` field that `build_llms.py` and the entrypoint wrote, so the notebook can't currently tell which server it's talking to.

### Tokenizer files and environment

- `environment/download_models.py` runs `snapshot_download("allenai/OLMo-2-0425-1B-Instruct", local_dir="/models/olmo")`. The model repo holds `config.json`, `generation_config.json`, `merges.txt`, `model.safetensors`, `special_tokens_map.json`, `tokenizer.json`, `tokenizer_config.json` and `vocab.json`, so the image already has everything the tokenizer needs in `/models/olmo`. `build_llms.model_src("olmo")` already resolves that folder through `CIVICDESK_MODELS_DIR`.  
- The Dockerfile installs `transformers` without a version. `environment/requirements.txt`, used for a plain pip setup, has no `transformers` at all.  
- `tokenizer_config.json` sets no real `model_max_length` (it is the huge placeholder value), so it can't be used for the context window. `config.json` has `max_position_embeddings: 4096`.  
- The chat template (from `tokenizer_config.json`) is:

```jinja
{{ bos_token }}{% for message in messages %}{% if message['role'] == 'system' %}{{ '<|system|>\n' + message['content'] + '\n' }}{% elif message['role'] == 'user' %}{{ '<|user|>\n' + message['content'] + '\n' }}{% elif message['role'] == 'assistant' %}...{% endif %}{% if loop.last and add_generation_prompt %}{{ '<|assistant|>\n' }}{% endif %}{% endfor %}
```

&nbsp;

`bos_token` is `<|endoftext|>` (ID 100257). `<|system|>`, `<|user|>` and `<|assistant|>` are **not** single special tokens in this vocabulary: they tokenize as ordinary pieces (`<`, `|`, `system`, `|`, `>Ċ`), and the `>` merges with the newline after it.

- In transformers 5.x, `apply_chat_template(..., tokenize=True)` returns a `BatchEncoding`, while 4.x returned a list. Use `tokenize=False` and then tokenize the rendered string with `add_special_tokens=False`. That gives the same IDs on both versions and doesn't add a second BOS.

## 3\. Reference results from my check (facilitator and tests only)

I checked these with transformers 5.22.2, using tokenizer files downloaded from the model repo on November 12, 2026, loaded with `local_files_only=True`. Re-run them on the image's pinned version before relying on them.

**Bank prompts** (curly apostrophes, as in Day 1):

- `"I need to deposit my check, so I’m going to the bank to"`: 15 tokens. `’m` is one piece (4344).  `bank` is ID **6201** at position 13\.  
- `"I’ve got my fishing rod, so I’m heading to the river bank to"`: 16 tokens.  `river` is 15140, then  `bank` is ID **6201** at position 14\.  
- Both decode back to the exact input string.  
- Variants: `"bank"` (no leading space) is 17469, `" bank"` is 6201, `"Bank"` is 26913, `" Bank"` is 8715, `"banks"` is 80046, and `"bank."` is 17469 followed by 13\.

So in these two sentences the same piece with the same leading space gets the same ID. The same letters without the space, or capitalised, get a different ID. That's the observation the notebook should let people find for themselves.

**Chat accounting** using the finance-only system text in section 5, cell 12:

| Messages | Full chat tokens | System \+ user content counted alone | Difference |
| :---- | :---- | :---- | :---- |
| System \+ money prompt, with generation prompt | 77 | 45 \+ 15 \= 60 | 17 |
| System \+ river prompt, with generation prompt | 78 | 45 \+ 16 \= 61 | 17 |
| Money prompt only (no system), with generation prompt | 27 | 15 | 12 |
| System \+ money prompt, no generation prompt | 72 | 60 | 12 |

The user text's 15 IDs appear as one unbroken run inside the full sequence. The system text's IDs do not: its final `.` merges with the template's newline into one piece (`.Ċ`), so the last ID differs from the system text tokenized alone. That's why the difference shouldn't be treated as a fixed per-message cost that can be added on.

Loading the tokenizer alone raised peak memory by about 330 MB on my machine, most of it the `torch` import that transformers triggers. No weights were loaded. The `tokenizers` library loading `tokenizer.json` directly gave identical IDs for the money prompt.

## 4\. Helper changes: `tier1/day1/civicdesk_lab.py`

### 4.1 Tokenizer section (new)

Add a block after `naive_tokens`. Imports of `transformers` go inside functions so the module still imports on a machine without it.

```py
TOKENIZER_ENV = "CIVICDESK_TOKENIZER_DIR"
_tok_cache: dict[str, Any] = {}

class TokenizerUnavailable(RuntimeError):
    """Raised with a plain-English fix when OLMo's tokenizer files are not on this machine."""

def tokenizer_source() -> str:
    """First match wins: $CIVICDESK_TOKENIZER_DIR, $CIVICDESK_MODELS_DIR/olmo (default /models/olmo),
    then the Hugging Face cache for OLMO_ID (offline). Never downloads."""

def load_tokenizer():
    """AutoTokenizer.from_pretrained(source, local_files_only=True). Cached per kernel.
    Never loads weights. On failure raise TokenizerUnavailable naming the folder it looked in
    and what to do (ask the facilitator; open completed/T1-02 meanwhile)."""

def tokenizer_info() -> dict:
    """source, backend ('transformers' or 'tokenizers-only'), tokenizer class, vocab_size=len(tok),
    tokenizer_sha256 (first 12 hex of tokenizer.json), context_window from config.json
    max_position_embeddings (None if absent), transformers version, weights_loaded=False."""

def tokenize(text: str) -> list[dict]:
    """Rows {pos, id, piece, text}: piece = convert_ids_to_tokens (raw, e.g. 'Ġbank'),
    text = decode([id]) (e.g. ' bank'). add_special_tokens=False."""

def token_ids(text: str) -> list[int]: ...
def count_tokens(text: str) -> int: ...

def show_tokens(text: str, max_rows: int | None = None) -> None:
    """Print pos | id | decoded piece. In the display column only, show a leading space as '␠'
    and a newline as '↵' so whitespace is visible. Explain once that 'Ġ' in raw pieces means a space."""

def roundtrip(text: str) -> dict:
    """{'decoded': decode(ids), 'identical': decoded == text}."""

def find_token(text: str, word: str) -> list[dict]:
    """Rows from tokenize(text) whose decoded text, stripped, equals word (case-sensitive).
    Also return pieces when word is split: report every row that overlaps the word's character span.
    The notebook prints whatever comes back; it never assumes one row."""

def chat_tokens(messages: list[dict], add_generation_prompt: bool = True) -> dict:
    """rendered = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=...)
    ids = tok(rendered, add_special_tokens=False)['input_ids']
    Return {rendered, ids, count, per_message: [{role, content_tokens, appears_unbroken}],
            content_sum, difference=count-content_sum}.
    appears_unbroken = the content's own IDs occur as a contiguous run in ids.
    No constants: every number is measured."""
```

**Fallback (should, not must).** If `transformers` can't be imported but `tokenizers` can, load `tokenizer.json` with `tokenizers.Tokenizer.from_file` for `tokenize`, `count_tokens` and `roundtrip`. Render the chat template with `jinja2` from `tokenizer_config.json["chat_template"]` for `chat_tokens`. Set `backend="tokenizers-only"` so it shows in `tokenizer_info()`. If neither works, raise `TokenizerUnavailable`.

**Optional download helper** for the `deep/` track or a laptop without the image: `fetch_tokenizer_files(dest)` calls `snapshot_download(OLMO_ID, allow_patterns=["tokenizer*", "vocab.json", "merges.txt", "special_tokens_map.json", "config.json"])`. It must never fetch `model.safetensors` and must never be called from a required cell.

Keep `naive_tokens` exactly as it is, and update its docstring: "Word splitter kept for backward compatibility. T1-02 now uses OLMo's tokenizer (see tokenize)."

### 4.2 Sampling settings, end to end

```py
DEFAULT_TEMPERATURE = 0.0   # what every call has sent until now
DEFAULT_MAX_TOKENS = 256

def _chat_body(model, messages, *, temperature=None, max_tokens=None, top_p=None, seed=None) -> dict:
    """Pure function, unit-testable.
    temperature None -> DEFAULT_TEMPERATURE; max_tokens None -> DEFAULT_MAX_TOKENS.
    Include top_p and seed only when not None. Validate 0 <= temperature <= 2 (ValueError otherwise)."""

def _post_chat(url, model, messages, timeout, *, temperature=None, max_tokens=None, top_p=None, seed=None) -> dict:
    body = _chat_body(model, messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p, seed=seed)
    ...  # unchanged request code

def chat(messages, model=None, timeout=60.0, *, temperature=None, max_tokens=None, top_p=None, seed=None) -> dict:
```

The new arguments are keyword-only, so existing positional calls still work. With no new arguments, the body is byte-for-byte what it is today: `{"model", "messages", "temperature": 0.0, "max_tokens": 256}`.

**Add these keys to the dict `chat` returns.** Keep every existing key (`ok`, `mode`, `model`, `text`, `latency_ms`, `raw`, `url`, `error`).

- `requested`: `{temperature, max_tokens, top_p, seed}` as actually sent, with the defaults filled in.  
- `applied`: what the server says it used, from `payload["civicdesk"]` (the hf server, section 4.3). If the server reports nothing (vLLM, a shared or custom URL), use `{"temperature": <sent>, "note": "sent; server did not report what it applied"}`. For demo and demo-fallback use `{"temperature": None, "note": "canned reply; sampling settings not used"}`.  
- `engine`: `"demo"` in demo mode. Otherwise `"hf"` when `payload["id"] == "hf-civicdesk"` or `payload["civicdesk"]["engine"] == "hf"`, else the `engine` saved in `endpoint.json`, else `"unknown"`.  
- `canned`: True for `demo` and `demo-fallback`, False for live.  
- `usage`: `payload.get("usage")` or None.

**`use_backend()` and `endpoint_config()`.** When `name == "local"`, keep the `engine` from the saved `endpoint.json`. For shared or custom, set `"unknown"` unless a new optional `engine=` argument is given. Write `engine` back into `endpoint.json` and return it from `endpoint_config()`.

**`_demo_reply()`.** Add one branch for the finance-only system text (match `"finance questions only"` in the system text). It should return text that says plainly it's canned, for example: `"[<model> demo] Canned text. Demo mode cannot show whether OLMo follows a scope rule. Switch BACKEND to local or shared to test it."` Don't write a canned "perfect refusal": in demo mode it would look like evidence that the rule works.

### 4.3 Server: `tier1/day1/hf_openai_server.py`

This is what serves OLMo in the click-a-link container, so the temperature fix has to reach it.

- `generate(tok, model, messages, max_tokens=256, temperature=None, top_p=None, seed=None)` returns `(text, info)`.  
  - If temperature is None or ≤ 0, call `do_sample=False`, exactly as today. A request without a temperature behaves as before.  
  - If temperature \> 0, call `do_sample=True` with that `temperature`, `top_p=top_p if top_p is not None else 1.0` and `top_k=0`. In transformers 5.22.2 the top-k filter is only added when `top_k` is neither None nor 0, so `top_k=0` turns it off. Pass it explicitly because older transformers versions defaulted to 50\.  
  - If a seed is given, call `torch.manual_seed(seed)` (and `torch.cuda.manual_seed_all` when CUDA is present) just before generating. This seed is global to the process, so treat it as best effort.  
  - Wrap `model.generate` in a module-level `threading.Lock`. `ThreadingHTTPServer` can otherwise run two generations at once, which doubles memory and breaks the seed.  
  - Tokenize the rendered prompt with `add_special_tokens=False`. The template already starts with `<|endoftext|>`. With this tokenizer the default adds nothing anyway, but this makes it explicit and keeps `usage.prompt_tokens` equal to the notebook's `chat_tokens()["count"]`.  
  - `info = {"engine": "hf", "do_sample": bool, "temperature": float or None, "top_p": float or None, "top_k": 0 or None, "seed": int or None, "max_tokens": int}`.  
- In `do_POST`, read `temperature`, `top_p` and `seed` from the body. Parse them with `float()` and `int()`, and answer 400 with a JSON error if they are malformed. Add these to the response:  
  - `"usage": {"prompt_tokens", "completion_tokens", "total_tokens"}`  
  - `"civicdesk": info`  
  - Keep `"id": "hf-civicdesk"` and the rest of the response shape.  
- Set `finish_reason` to `"length"` when `completion_tokens == max_tokens`, otherwise `"stop"`.

The vLLM paths in `build_llms.py` need no change.

### 4.4 Environment

- `environment/requirements.txt`: add `transformers` and `jinja2`, pinned to the versions the image is built and tested with. Pinning matters here because `apply_chat_template`'s return type changed between 4.x and 5.x.  
- `Dockerfile`: pin the same `transformers` version in the `pip install ... transformers accelerate sentencepiece protobuf` line. Rebuilding only redoes the layers after the weights download, because the notebooks and server are copied in the later `COPY . /opt/civicdesk` layer.  
- The entrypoint copies `/opt/civicdesk` into `/civicdesk` only when `/civicdesk/tier1/day1/civicdesk_lab.py` is missing. A container started on an old mounted volume would keep the old helper and server. For the hosted image that's fine. Mention it in the facilitator notes.

## 5\. The notebook, cell by cell

The timing stays at 10:45 to 12:00. Rough split: tokenizer and bank, 15 minutes; ministry sentences and probe, 15; full chat request and scope rule, 20; temperature, 15; save and write-up, 10\. Mark cells `# [RUN]`, `# [CHANGE]` and `# [OPTIONAL]` as the BANNER describes. Optional cells go at the end, after the write-up's save cell, so the room never waits on them.

### Cell 0 (md): title, keep the BANNER

Keep the title, time and BANNER. Change the evidence line to `token checkpoint (logs/T1-02_tokens.json) + marked architecture card`. Replace the outcomes line with:

> - See OLMo's own token pieces and IDs for a sentence, and decode them back to the same text.  
> - Find where the same token ID appears in two different sentences, and say what still differs inside the model.  
> - Count a full chat request (system \+ user \+ role markers) against its content, and relate it to the context window.  
> - Run the same prompt at two temperatures, and say what changed, what didn't, and what you can't conclude.

### Cell 1 (md): ministry link, keep

Keep the table, the N12 paragraph and "Overnight readers". Change one sentence: "You are counting tokens, not retrieving classified files" becomes "You are counting OLMo's own tokens, not retrieving classified files."

### Cell 2 (md): architecture card, keep

Keep it as it is. Add one line under it: "Today you touch the first box (the tokenizer) directly on this machine. The rest you reach through the endpoint. Nothing is shaded today."

### Cell 3 (code, new): load the tokenizer

```py
# [RUN] load OLMo's own tokenizer from the course image. No weights, no download.
import civicdesk_lab as lab

try:
    info = lab.tokenizer_info()
    for k in ("source", "backend", "vocab_size", "context_window", "tokenizer_sha256", "weights_loaded"):
        print(f"{k:18} {info[k]}")
except lab.TokenizerUnavailable as exc:
    print(exc)
```

### Cell 4 (md, new): what the tokenizer is

> The tokenizer is a fixed list of text pieces, about the size printed above as `vocab_size`, and it was settled before OLMo was trained. The same text always gives the same IDs. This step is not the model thinking: it is a lookup that happens before the first block runs. In the next cell, a `␠` means the piece starts with a space.

### Cell 5 (code, new): the two bank sentences from this morning

```py
# [RUN] the two unfinished sentences from this morning, as OLMo sees them
bank_money = "I need to deposit my check, so I’m going to the bank to"
bank_river = "I’ve got my fishing rod, so I’m heading to the river bank to"

for label, text in [("money", bank_money), ("river", bank_river)]:
    print(f"== {label}: {text!r}   tokens={lab.count_tokens(text)}")
    lab.show_tokens(text)
    rt = lab.roundtrip(text)
    print("decoded back:", repr(rt["decoded"]), "| identical to input:", rt["identical"])
    print()
```

### Cell 6 (code, new): where does "bank" land?

```py
# [RUN] find "bank" in each sentence. Read what this tokenizer actually did.
found = {}
for label, text in [("money", bank_money), ("river", bank_river)]:
    rows = lab.find_token(text, "bank")
    found[label] = rows
    print(label, [(r["pos"], r["id"], repr(r["text"])) for r in rows])

ids_money = [r["id"] for r in found["money"]]
ids_river = [r["id"] for r in found["river"]]
if ids_money == ids_river:
    print("Observed: the same ID(s) for 'bank' in both sentences:", ids_money)
else:
    print("Observed: different IDs here:", ids_money, "vs", ids_river, "- check spacing and case.")

print("\nSame letters, small changes (observed, this tokenizer only):")
for s in ["bank", " bank", "Bank", " Bank", "banks"]:
    print(f"  {s!r:9} -> {lab.token_ids(s)}")
```

### Cell 7 (md, new): same ID, different meaning

> In these two sentences, check whether "bank" got the same ID. It does when the piece and its leading space match. Change the space or the capital letter and the ID changes, which is why we compare matching strings.

> The same ID means the same **starting** vector: the embedding step is a table lookup. On the way through the transformer blocks, each position mixes in the other tokens before it ("deposit… check" in one sentence, "fishing rod… river" in the other). By the time the head scores the next token, the vectors at "bank" are no longer the same. That's why the two sentences can be continued differently. We don't measure those inner vectors today, because that needs the weights loaded in this notebook. See the architecture card: the tokenizer and embedding are the same for both sentences, and the blocks are where they part.

> On your card, write your own guess for the next word in each sentence.

### Cell 8 (code, rewritten from old cell 3): ministry sentences A to D with real tokens

Keep the `sentences` dict exactly as it is. Replace the loop:

```py
# [RUN] the four fictional ministry sentences, counted with OLMo's tokenizer
for k, s in sentences.items():
    rows = lab.tokenize(s)
    pieces = [r["text"] for r in rows]
    print(f"{k}  words={len(s.split()):3d}  tokens={len(rows):3d}  {pieces[:12]}{'...' if len(pieces) > 12 else ''}")
```

### Cell 9 (md, rewritten from old cell 4): after the counts

> These are OLMo's real pieces now, not a stand-in. Notice that tokens and words aren't the same count, and that the gap depends on the kind of text: codes like "C2", dates and numbers split differently from ordinary words.

> The **context window** printed in the first cell is a budget in tokens, not words. The system rules, the user turn, any retrieved chunks and the reply all share it. A long Cabinet pack (Finance) or a 2,000-application batch (Labour) can overrun it even when a person could skim it. That's one reason Day 2 retrieves *chunks*, not whole EDMS filings.

> `# [CHANGE]` below: take sentence B or C and add one word. Watch the count move. Then try `I'm` against `I’m`, or a place name.

### Cell 10 (code, rewritten from old cell 5): the probe

```py
# [CHANGE] edit this string, re-run, write the new count on the architecture card
probe = "Criterion C2: the applicant must hold a recognised diploma in records management or equivalent."
print("tokens:", lab.count_tokens(probe), "| decodes back identically:", lab.roundtrip(probe)["identical"])
lab.show_tokens(probe)
```

### Cell 11 (md, new): what the model actually receives

> In T1-01 you sent a `system` message and a `user` message. The model doesn't receive two neat boxes. The runtime pastes them into one string using OLMo's **chat template**: a start marker, a `<|system|>` label, your rules, a `<|user|>` label, your text, and finally `<|assistant|>` to say "your turn" (the **generation prompt**). Then it tokenizes that whole string. The next cell shows the string and counts it.

> The system text below is a scope rule: finance questions only. It is only more tokens in the window. It changes **no weights**, and the model may still not follow it, so it has to be tested, not assumed.

### Cell 12 (code, new): full chat count against content count

```py
# [RUN] count the full chat request, then the content alone
FINANCE_ONLY = (
    "CivicDesk finance assistant. Answer only questions about CivicDesk finance procedures: "
    "budgets, payment vouchers, purchase orders and expense claims. "
    "If a request is about anything else, reply exactly: Out of scope: finance questions only."
)
cases = {
    "finance rule + money sentence": [{"role": "system", "content": FINANCE_ONLY}, {"role": "user", "content": bank_money}],
    "finance rule + river sentence": [{"role": "system", "content": FINANCE_ONLY}, {"role": "user", "content": bank_river}],
    "money sentence, no system":     [{"role": "user", "content": bank_money}],
}
acct = {}
for name, msgs in cases.items():
    a = lab.chat_tokens(msgs)
    acct[name] = a
    parts = " + ".join(f"{m['role']} {m['content_tokens']}" for m in a["per_message"])
    print(f"{name:32} full={a['count']:3d}  content={parts} = {a['content_sum']}  difference={a['difference']}")

first = acct["finance rule + money sentence"]
print("\nThe string the model receives (first case):")
print(repr(first["rendered"]))
print("\nContent tokens still in one unbroken run inside the full request?")
for m in first["per_message"]:
    print(f"  {m['role']:6} {m['appears_unbroken']}")

window = lab.tokenizer_info()["context_window"]
REPLY_BUDGET = 256  # what lab.chat asks for by default
if window:
    print(f"\nWindow {window} - request {first['count']} - reply budget {REPLY_BUDGET} = "
          f"{window - first['count'] - REPLY_BUDGET} tokens left for retrieved chunks (Day 2).")
```

**Wording note for Cursor:** the system text above is what I used for the reference counts. If Kris settled on different finance-only wording, use his and let the counts change; the cell measures them.

### Cell 13 (md, new): the wrapper isn't free, and it isn't fixed

> The full request is longer than the content: the start marker, role labels, newlines and the generation prompt all cost tokens. Compare the differences across the three cases. They aren't one fixed number per message, and where your text meets the template, the tokenizer can merge characters differently than it does when the text stands alone. For example, a final full stop can merge with the newline after it. The "unbroken run" check shows where this happens. So measure with the real template. Don't estimate a request by adding a constant to your word count.

> The scope rule costs those tokens on every call, and it doesn't change OLMo. The next cell tests whether this model follows it on this backend.

### Cell 14 (code, new): test the scope rule

```py
# [RUN] does OLMo keep to the finance-only rule? Two questions, temperature 0, short replies.
scope_tests = [
    ("in scope",     "What should be attached to a CivicDesk payment voucher before approval?"),
    ("out of scope", bank_river),
]
scope_runs = []
for label, q in scope_tests:
    r = lab.chat([{"role": "system", "content": FINANCE_ONLY}, {"role": "user", "content": q}],
                 temperature=0.0, max_tokens=60)
    scope_runs.append({"label": label, "question": q, "mode": r["mode"], "engine": r["engine"], "text": r["text"]})
    print(f"[{label}] mode={r['mode']} engine={r['engine']}")
    print("   ", r["text"][:300])
if any(x["mode"] != "live" for x in scope_runs):
    print("\nDEMO / FALLBACK: canned text. This shows nothing about whether OLMo follows the rule.")
else:
    print("\nJudge it yourself: did the out-of-scope reply say exactly the refusal line? One test is not a guarantee.")
```

### Cell 15 (md, new): temperature, before you run it

> At every step the head gives a score to every possible next token. **Temperature** rescales those scores before one token is picked. At 0 the top-scoring token is always taken (greedy). Higher values flatten the choice, so lower-ranked tokens get picked more often. It acts only at inference: OLMo's weights are the same at every setting.

> Low temperature makes a reply **more repeatable**, not more correct. A wrong answer can be repeated perfectly. The next cell prints which backend you're on, and whether the server reports applying the setting.

### Cell 16 (code, rewritten from old cell 6): the fixed temperature comparison

```py
# [RUN] same CivicDesk prompt, two temperatures, repeated samples
cfg = lab.endpoint_config()
print("backend:", cfg["backend"], "| engine:", cfg.get("engine"), "| model:", cfg["model"])

messages = [
    {"role": "system", "content": "CivicDesk classroom. One short sentence. No invented citations."},
    {"role": "user", "content": "In one sentence: should a missing diploma be Meets, Does not meet, or Human review required?"},
]
SETTINGS = [(0.0, 2), (0.9, 3)]  # [CHANGE] (temperature, how many samples)
runs = []
for temp, repeats in SETTINGS:
    for k in range(repeats):
        r = lab.chat(messages, temperature=temp, max_tokens=60)
        runs.append(r)
        print(f"requested={r['requested']['temperature']}  applied={r['applied'].get('temperature')}  "
              f"mode={r['mode']}  engine={r['engine']}  sample {k + 1}")
        print("   ", r["text"][:240])

if any(r["canned"] for r in runs):
    print("\nDEMO / FALLBACK: canned replies. Temperature was not applied, so identical text tells you nothing.")
else:
    for temp, _ in SETTINGS:
        texts = [r["text"] for r in runs if r["requested"]["temperature"] == temp]
        print(f"temperature {temp}: {len(set(texts))} different repl{'y' if len(set(texts)) == 1 else 'ies'} out of {len(texts)}")
    print("Write down what you saw. A few samples can match or differ at either setting; neither proves the answer is right.")
```

The 60-token cap keeps five calls short on a CPU-served OLMo. The demo prompt asks for one sentence anyway.

### Cell 17 (md, rewritten from old cell 7): decoding

Keep the opening and the Labour/Health/OPR versus Trade sentence. Change the rest to:

> Temperature is not "creativity." It is how sharply the head picks among next tokens. For **Labour / Health / OPR** criteria work you want the boring setting (low temperature) plus a quote. For a Trade ticket draft you might tolerate more variation, but it's still not a password reset. A repeatable answer still needs its quote checked by a person.

> **Training vs inference:** nobody in this room is updating OLMo's blocks today. The scope rule and the temperature are both settings on a call. Neither changes a weight.

### Cell 18 (code, new): save the checkpoint

```py
# [RUN] save the evidence. This is the token checkpoint.
log_path = lab.save_log("T1-02_tokens", {
    "tokenizer": lab.tokenizer_info(),
    "bank": {k: [{x: r[x] for x in ("pos", "id", "text")} for r in v] for k, v in found.items()},
    "probe": {"text": probe, "tokens": lab.count_tokens(probe)},
    "chat_accounting": {k: {x: v[x] for x in ("count", "content_sum", "difference")} for k, v in acct.items()},
    "scope_test": scope_runs,
    "temperature_runs": [{x: r.get(x) for x in ("mode", "engine", "canned", "requested", "applied", "usage", "text")} for r in runs],
    "backend": lab.endpoint_config(),
})
print("saved", log_path)
```

### Cell 19 (md, rewritten from old cell 8): write-up

> 1. Mark the architecture card: tokenizer, embedding, blocks, head.  
> 2. Did " bank" get the same ID in both sentences? Even so, what differs inside the model by the time it picks the next word?  
> 3. Your finance-rule request: full count, content count, difference. Why can't you estimate it by adding a constant?  
> 4. Using the context-window number, why might Finance *not* paste a whole minute pack into this window?  
> 5. What did temperature change on **your** backend? What was `mode`? If it was `demo`, what can you not conclude?  
> 6. One sentence: what is frozen right now? Did the scope rule change any of it?

### Cell 20 (code, optional): Day 2 preview

```py
# [OPTIONAL] how big are Day 2's handbook chunks, in OLMo tokens?
import json
from statistics import median
chunks = json.loads((lab.HERE.parent / "day2" / "data" / "handbooks.json").read_text(encoding="utf-8"))["chunks"]
sizes = sorted(lab.count_tokens(c["text"]) for c in chunks if c.get("index_ok"))
print(f"{len(sizes)} indexable chunks: min {sizes[0]}, median {median(sizes)}, max {sizes[-1]} tokens")
```

The repo's `handbooks.json` has 12 chunks, 11 of them marked `index_ok`.

### Cell 21 (code, optional): let OLMo continue the bank sentences

```py
# [OPTIONAL] send each bank sentence to the OLMo already running. One short request each.
for label, text in [("money", bank_money), ("river", bank_river)]:
    r = lab.chat([{"role": "user", "content": text}], temperature=0.0, max_tokens=12)
    print(f"{label}: mode={r['mode']} -> {r['text']!r}")
```

Add a one-line note under it: "This is an Instruct model behind a chat template, so it may answer like an assistant rather than finish your sentence. That's the chat format at work."

If there's room, a third optional item for the deep track is to print the raw pieces (`Ġbank`) next to the decoded ones and explain byte-level BPE. Keep it out of the required path.

## 6\. Build script and completed copy

- In `build_day1_notebooks.py`, make `write()` skip notebooks not named by an `--only` argument (prefix match, so `--only T1-02` works). With no argument it behaves as now. Replace the T1-02 block with the cells in section 5, and update the T1-02 line in `01_tier1_day_by_day_plan.md` from "two decoding settings" to "OLMo tokenizer, chat-template count, scope rule, temperature with repeats".  
- `tier1/execute_to_completed.py` covers only Days 2 and 3\. Produce `tier1/day1/completed/T1-02_tokens_and_transformer.ipynb` by running the notebook inside the built container with `BACKEND="local"`, so its outputs show the real tokenizer and a live hf backend. The saved outputs carry the `mode` and `engine` lines, so a reader can see what produced them.

## 7\. Acceptance checks

Put the automated checks in `tier1/day1/tests/test_t1_02.py` (pytest, no GPU). Run the notebook checks inside the built image.

**Offline tokenizer**

1. In the image, run with `docker run --network none` and `HF_HUB_OFFLINE=1`. `tokenizer_info()["source"]` is `/models/olmo` (or `$CIVICDESK_TOKENIZER_DIR`), `weights_loaded` is False, and nothing tries to reach the network.  
2. `grep -n "AutoModel\|safetensors\|snapshot_download" civicdesk_lab.py` finds only the optional `fetch_tokenizer_files`. The kernel's memory rises by well under 1 GB after the tokenizer cells.  
3. With `CIVICDESK_TOKENIZER_DIR` pointed at an empty folder, cell 3 prints the `TokenizerUnavailable` message and doesn't throw a traceback.

**Round trip and bank**

4. `roundtrip(s)["identical"]` is True for both bank sentences, sentences A to D and the probe.  
5. Every row from `find_token(text, "bank")` decodes to text containing "bank". The test asserts this reporting behaviour, not specific IDs. As a pinned-version regression check only, the observed values in section 3 (15 and 16 tokens,  `bank` \= 6201\) should match the image. If they don't, update section 3, not the notebook text.  
6. No markdown cell contains "always one token", "always the same ID" or similar wording.

**Context accounting**

7. For each case in cell 12, `chat_tokens(m)["count"]` equals `len(tok(tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True), add_special_tokens=False)["input_ids"])`. It also equals the length from `apply_chat_template(..., tokenize=True, return_dict=True)`.  
8. `difference == count - content_sum` for every case, and the code contains no hard-coded overhead constant.  
9. Against the live hf server in the container, `usage.prompt_tokens` equals `chat_tokens(messages)["count"]` for the cell 16 prompt. On vLLM, compare it when `usage` is present and report any mismatch rather than failing, since a server can apply its own template.

**Temperature propagation**

10. `_chat_body(model, msgs)` equals `{"model", "messages", "temperature": 0.0, "max_tokens": 256}` exactly. That's today's body, so T1-01 and T1-03 are unchanged.  
11. `_chat_body(..., temperature=0.9, max_tokens=60)` carries 0.9 and 60\. `top_p` and `seed` appear only when given. `temperature=2.5` raises `ValueError`.  
12. Run a throwaway local `http.server` that records request bodies, point `use_backend("custom", olmo_url=...)` at it and call `lab.chat(msgs, temperature=0.9)`: the recorded body has 0.9.  
13. Against `hf_openai_server.py` (the real OLMo in the container): with temperature 0 or no temperature, `civicdesk.do_sample` is False; with 0.9, it is True, `temperature` is 0.9 and `top_k` is 0\. `lab.chat(...)["applied"]["temperature"]` shows the server's reported value. Don't assert that samples differ.

**Demo honesty**

14. In demo mode, every result has `canned` True and `applied["temperature"]` None. Cell 16 prints the DEMO banner and no "different replies" count, and cell 14 prints its demo warning.  
15. With `use_backend("custom", olmo_url="http://127.0.0.1:9/v1")` (nothing listening), results are `demo-fallback` with `error` set, and the same banners print.  
16. No cell or teaching note promises that temperature 0 gives identical or correct output, or that 0.9 gives different output.

**Regeneration and run**

17. `python build_day1_notebooks.py --only T1-02` changes only T1-02. `git diff --stat` shows no other notebook.  
18. The notebook runs top to bottom without errors in the container with `BACKEND="demo"` and with `BACKEND="local"`. Only OLMo is called, and nothing is loaded into the notebook kernel apart from the tokenizer.