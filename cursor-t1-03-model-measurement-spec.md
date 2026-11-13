# Cursor brief: T1-03 measured model comparison

For: `tier1/day1/T1-03_slm_vs_llm.ipynb` in `justkrismanohar/fine-tuning-build`
Written: Thursday 12 November 2026, against the repo as cloned that evening.
Repo status: read only. Nothing was changed or pushed. The tested reference files are in the appendices.

## 1. What this notebook becomes

T1-01 now carries the bank example, the spotlight picture of attention, weights and training, and the banking-only system prompt. T1-02 carries real tokenization and full chat-template counts. T1-03 must not teach that theory again. It becomes an evidence session:

1. One frozen, fictional test set of CivicDesk draft replies, each labelled GO or BLOCK.
2. The same system prompt, the same cases and the same decoding settings sent to OLMo and to Phi, one request at a time.
3. A scorecard per model: acceptable answers, correct decisions, latency, input tokens and output tokens per request and in total.
4. A cost section that turns those measurements into cost per acceptable answer, with every assumption written down.
5. An optional section that runs the same frozen cases on a hosted API.

Both OLMo 2 1B Instruct and Phi-4 Mini are small models. Do not call this a small-versus-frontier comparison anywhere in the notebook. Call it "two small open models, measured on one task". The title can stay `T1-03 SLM vs LLM comparison` only if the first cell says this plainly. Better: `T1-03 Measuring two small models on one task`.

Keep the CivicDesk screening theme and the existing "no hiring" boundary. A 24-case screening set with a verified answer key teaches more than a bank-sentence completion, because "right" is defined before the run.

## 2. What the repo does today (checked)

- **`hf_openai_server.py`** (the server the container starts for both models): `generate()` applies the chat template as text, then calls `tok(text)` again, generates greedily (`do_sample=False`), slices off the prompt and decodes. The response has `choices` and no `usage` field at all. Temperature from the request is ignored. There is no lock around `generate`, and the server is a `ThreadingHTTPServer`, so two notebook calls at once would run two generations at once on one GPU.
- **`environment/docker-entrypoint.sh`** starts one `hf_openai_server.py` per model: OLMo on 8000 and Phi on 8001, both by default (`CIVICDESK_LOAD_MODELS=olmo,phi`). It loads weights from `/models/olmo` and `/models/phi`.
- **`environment/download_models.py`** bakes the weights without a pinned revision.
- **`build_llms.py`** can also serve with vLLM (`--engine vllm`). vLLM's own OpenAI server already returns `usage`. That path is not the container default.
- **`civicdesk_lab.chat()`** sends `temperature: 0.0, max_tokens: 256` (hard-coded), keeps the raw payload in `raw`, and returns `ok`, `mode`, `model`, `text`, `latency_ms`, `url`. It returns no usage. Demo and fallback replies come back as `mode` other than `"live"`, which is the hook for labelling.
- **`T1-03_slm_vs_llm.ipynb`** has six cells: title, ministry link, one C2 diploma prompt sent to both models, a teaching note, a hand-filled 0 to 2 score dictionary, and the cost card pointer. It measures nothing automatically.
- **`cards/cost_card.md`** asks for latency and "cost per acceptable answer (ratio is enough)" by hand.
- **`build_day1_notebooks.py`**: its T1-03 section still matches the notebook, but the script also rewrites T1-01, where it is out of date. Do not run it. Edit the notebook JSON directly.

## 3. What I checked on the real tokenizers and model

- **Chat template counts:** on the first CivicDesk request, OLMo's chat template gives 154 input tokens and Phi's gives 141. The system and user text alone are 138 and 136 tokens. A naive word split gives 111. The fair comparison is the same text, not the same count.
- **No double BOS today:** for both models, `tok(template_text)` gives the same IDs as `apply_chat_template(..., tokenize=True)`. So the current server is not adding a second BOS for these two models. Still switch to tokenizing once inside `apply_chat_template`, so a future model cannot make it wrong silently.
- **Phi stops on two IDs:** Phi-4 Mini's `generation_config.json` lists `eos_token_id: [200020, 199999]`, and its tokenizer's `eos_token_id` is only 199999. Counting must use the generation config's list, or the count will be wrong. OLMo's is 100257 in both places. Phi's pad token is the same as its EOS, which is one reason to stay at batch size 1.
- **Patched server, live test:** I ran the patched server (Appendix A) with OLMo 2 1B Instruct (revision `48d788eca847d4d7548f375ad03d3c9312f6139e`) on CPU in bfloat16. On a short prompt the server reported 28 input tokens, which matched `apply_chat_template` exactly. It reported 4 output tokens for "Port of Spain". Re-tokenizing the decoded text gave 3, because the EOS token is not in the text. A word split gave 9 for the input.
- **Synthetic set, live test:** OLMo wrote the filler for a 14-case practice set. None of its filler tripped a rule and no case was dropped. The set had 8 BLOCK and 6 GO cases.
- **Screening, live test (practice set, unreviewed, CPU):** OLMo answered every case with the single word "GO". That is 6 of 14 decisions right (all the GO cases), 0 of 8 BLOCK cases caught, 0 acceptable answers and no case where it followed the three-line format. Mean input was 285 tokens and output 2 tokens. The median wall time was about 8.3 seconds per request on CPU, which says nothing about the course GPU. Adding one worked example to the system prompt changed its output on an 8-case subset to longer, mostly three-line replies: 5 of 8 decisions right, still 0 acceptable (it named R1 on every case and often quoted the wrong sentence).
- **Not run:** Phi-4 Mini (I did not load its 7.7 GB of weights) and any GPU timing. None of the hosted APIs were called with a real key.

That OLMo result is useful in class: a 1B model can fail this task completely, and the scorecard shows it in numbers instead of impressions. Do not promise learners that either model will pass.

## 4. Server change: report usage from the real token IDs

File: `tier1/day1/hf_openai_server.py`. Full tested version in Appendix A, diff in Appendix B.

1. Build the input once: `enc = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)`. `prompt_tokens = enc["input_ids"].shape[-1]`. This is the exact tensor passed to `generate`, so it includes the system text, the role markers and the generation prompt, all counted by that model's own tokenizer.
2. Output tokens come from the generated IDs, never from re-tokenizing decoded text: `new = out[0, prompt_len:]`. In a decoder-only `generate`, the output tensor starts with the prompt, so the prompt length must be cut off.
3. EOS: collect the stop IDs from `model.generation_config.eos_token_id` (it may be a list) plus `tok.eos_token_id`. Pass the list to `generate`. Count up to and including the first stop ID and ignore anything after it. Decode only the counted IDs.
4. `finish_reason` is `"stop"` when a stop ID appeared and `"length"` when `max_tokens` ran out first.
5. Batch size stays 1. There is no padding, so no pad tokens are counted. If anyone later batches requests, they must count each row with its attention mask and padding side, not the padded tensor width. Say this in a comment.
6. Wrap `generate` in a module-level `threading.Lock`, so two requests to one server run one after another. This adds no model load.
7. Return an OpenAI-shaped `usage` object: `prompt_tokens`, `completion_tokens`, `total_tokens`. Put extras under `usage.civicdesk`: `generation_ms`, `eos_included`, model path, revision, device, dtype, the decoding note ("greedy; temperature ignored") and a one-sentence counting convention.
8. Add `GET /v1/health` that returns the same metadata, so the notebook can record it once.
9. Keep everything else compatible: `/v1/models`, `/v1/chat/completions`, `choices[0].message.content` and `finish_reason` keep their shapes. Callers that ignore `usage` keep working.
10. Revision: read `CIVICDESK_REVISION.txt` from the model folder if it exists, else report `"unknown (not pinned)"`. Separately, change `download_models.py` to pass a `revision=` to `snapshot_download` and write that commit hash into `CIVICDESK_REVISION.txt` beside the weights. This is part of the record-keeping Michelle asked for.

Counting convention, word for word for the notebook: "Input tokens are the exact token IDs the model received after its own chat template was applied, including the system text, role markers and the start-of-reply marker. Output tokens are the new token IDs it generated, up to and including the first end-of-reply token. Each model uses its own tokenizer, so the same text gives different counts."

If the room uses `build_llms.py --engine vllm` instead, vLLM returns its own `usage`. Record `engine` in the scorecard and never mix engines inside one comparison, because the two servers count by their own rules.

## 5. Client change: carry usage through `civicdesk_lab.chat`

File: `tier1/day1/civicdesk_lab.py`. Diff in Appendix C.

- Add `max_tokens: int = 256` to `chat()` and `_post_chat()`. Default stays 256, so T1-01 and T1-02 behave as before.
- Add `usage`, `usage_source` and `finish_reason` to every return path:
  - live: `usage` from the server when it has integer `prompt_tokens` and `completion_tokens`, `usage_source: "server"`; otherwise `None` and `"none (server sent no usage)"`.
  - demo: `usage: None`, `usage_source: "none (demo reply, not a model)"`.
  - fallback after an error: `usage: None`, `usage_source: "none (fallback demo reply after an error)"`.
- Never fill `usage` by estimating. A missing count stays missing and shows as a blank in the scorecard.

## 6. New module: `tier1/day1/civicdesk_eval.py`

Full tested code in Appendix D. It holds the rules, the generator, the answer key, freezing, scoring and cost helpers, so notebook cells stay short.

### 6.1 The fictional release rules (version `civicdesk-release-rules-v1`)

A draft reply must be BLOCKED if any of these apply. Otherwise it may GO.

- **R1:** it contains a CivicDesk personal ID: `CDID-` followed by six digits. Ticket numbers (`TKT-` plus five digits) are fine.
- **R2:** it cites a circular that is not approved. Approved: Circular 12 of 2025 and Circular 7 of 2026.
- **R3:** it says CivicDesk has reset or will reset a password, or has unlocked or will unlock an account. "A staff member will review your request" is fine.
- **R4:** it tells an applicant they are hired, selected, shortlisted or ranked. "Your application was received and a person will review it" is fine.

Each rule has a decoy that looks close but should GO (a ticket number, an approved circular, a human-review line). Decoys are what make the set test reading rather than keyword panic.

### 6.2 How the synthetic set is built

The model does not decide the labels, and it never checks its own work.

1. **Plan in code:** `build_case_plan(seed=3)` makes 24 cases: 3 trigger cases per rule (BLOCK), 2 decoys per rule (GO) and 4 plain cases (GO). Each gets a topic, an insert sentence chosen by code and a position. Inserts come from fixed lists, so the trigger text is known exactly.
2. **Model writes only neutral filler:** two polite sentences about the topic, from OLMo through the running server. The filler prompt forbids IDs, circulars, passwords and hiring language.
3. **Filler check:** if the model's filler already trips a rule, or the call was not live, the case uses a fixed template filler instead and records why in `filler_source`.
4. **Assemble:** "Dear resident," + filler with the insert placed in the middle or at the end + "Regards, CivicDesk."
5. **Answer key from the rules:** `derive_label(text)` runs the four rules as plain regular expressions on the final text and returns GO or BLOCK, the rules that fired and the exact trigger spans.
6. **Plan check:** if the derived label or rules differ from the plan, the case is dropped and kept in a `dropped` list with the reason. It is never relabelled to fit.
7. **Human review:** the instructor reads every kept case and its label once. Then `freeze(..., reviewed_by="Kris, 2026-11-xx")`.
8. **Freeze:** the file stores the rules version, rule text, the generator details (model, revision, seed), `label_source: "deterministic rules (derive_label), not a model"`, the review status, a timestamp, counts and a SHA-256 of the cases.
9. **Load check:** `load_frozen()` refuses the file if the hash does not match, if any stored label disagrees with the rules, or if it is unreviewed (unless `allow_unreviewed=True`, which marks the run as practice).

Course set: Cursor runs steps 1 to 6 once, Kris reviews, and the frozen file goes in the repo as `tier1/day1/data/t103_release_cases_v1.json`. Both models are scored on that same file. In class, learners load it. The generation cell exists so they can see how such a set is made and build a practice set, but practice results are never compared against the course set.

Say in the notebook: "The model helped write the wording. The rules decided the right answers, and a person checked them. If we had asked a model to label the cases and then scored models against those labels, we would be grading the test with the test."

### 6.3 The screening prompt (identical for every model)

`SCREEN_SYSTEM` lists the four rules and asks for exactly three lines: `DECISION: GO or BLOCK`, `RULE: R1–R4 or NONE`, `QUOTE: exact words or NONE`. The user message is `Draft reply:` plus the case text. Same text, same `max_tokens` (96), greedy decoding, for every model. Learners may change the system prompt as a dial, but the scorecard records a hash of it and any change starts a new comparison.

### 6.4 What counts as an acceptable answer

All of these must hold:

- the three-line format was followed;
- the decision matches the answer key;
- for BLOCK cases: the named rule is one that fired, and the quote is copied exactly from the draft and contains, or sits inside, the trigger span;
- for GO cases: `RULE: NONE` and `QUOTE: NONE`;
- no hiring recommendation of its own outside the quote line.

Also report, separately: decisions correct, BLOCK cases caught, GO cases wrongly blocked and format followed. A bare "GO" reply is read as a decision but is not acceptable, which is exactly what OLMo did in my test. Report a 95% Wilson interval on the acceptable rate (24 cases gives wide intervals; say so).

### 6.5 Running the comparison fairly

- One request at a time (`run_eval` is sequential). No parallel calls and no third model load. The container already runs one server per model, and the filler and screening calls reuse those servers.
- One unscored warm-up request per model before the scored cases. It is kept as a `scored: False` row: out of accuracy and latency, in the cost totals (it uses tokens and time).
- Same hardware, same server engine, same `max_tokens`, same frozen file and same system prompt for both models. Record all of these.
- Only rows with `mode == "live"` are measurements. Demo, fallback, skipped and error rows are counted and shown, but they never go into accuracy, tokens, latency or cost.
- Report `finish_reason == "length"` as truncation, and errors with their message.
- Two latencies: `latency_ms` (the client's round trip) and `generation_ms` (inside the server). Repeat the timed pass once if there is time, and report the median.
- If the GPU cannot hold both models, run the whole OLMo pass, then restart with `CIVICDESK_LOAD_MODELS=phi` and run the Phi pass. The scorecard records this.

### 6.6 Scorecard files

`write_scorecard(rows, summary, stem)` writes `logs/t103_<model>_<timestamp>.csv` and `.json`. Each row: case ID, model, mode, label, decision, rule, quote, the five checks, acceptable, latency, generation time, input and output tokens, finish reason, usage source, error and the reply. The JSON also has the summary and a `run_info` block:

- model ID, revision, engine, device, dtype, server counting convention;
- decoding (greedy, temperature ignored), `max_tokens`;
- the frozen set's file name, SHA-256, review status and rules version;
- the system prompt's SHA-256;
- warm-up count, timed passes, truncations and errors;
- `mode` counts, and a plain flag `"measured": true` only when every scored row was live.

No API keys, ever, in any file or output.

## 7. Cost section

Put the formulas in markdown first, then one `# [CHANGE]` cell with blanks. Every figure the learner types needs its currency, its source and its date beside it. Leave a field as `None` when the figure is unknown. The cells print "not available" for it and never invent one.

### 7.1 Token counts are not prices

The local servers have no price per token. Tokens are a measure of work and of context used. They become money only through a rate somebody charges.

### 7.2 Hosted API (illustrative)

`api_cost = input_tokens × input_rate_per_million / 1,000,000 + output_tokens × output_rate_per_million / 1,000,000`

Use the provider's own reported usage and its published rate on a stated date. Caching discounts, batch discounts, search grounding, taxes and minimum spends are excluded, and the cell says so.

### 7.3 Self-hosted OLMo and Phi

`compute_cost = hourly_rate × hours`, in a currency you name. There are two different numbers, and the notebook must show both:

- **Marginal active estimate:** hours = the sum of `generation_ms` for this batch. This answers "what did these answers use while the GPU was busy".
- **Billed allocation:** hours = the time the instance was allocated and billed, including start-up, model loading, warm-up and idle time. This answers "what did we pay".
- **Shared host:** if OLMo and Phi ran on one instance, split the billed cost with one stated rule (by active generation seconds is the default) and check that the shares add up to the bill. Never charge the full host to each model.

Total service cost is wider again: staff time, monitoring, storage, support, security and retraining. Name it as out of scope for this cell.

### 7.4 Cost per acceptable answer

`cost_per_acceptable = total cost of every attempt in the batch / number of acceptable answers`

- Every attempt counts: the warm-up, every scored case and any retry. A retried case costs both attempts.
- State the scope beside the number: which batch, which cost (marginal or billed), which model.
- Zero acceptable answers: print "undefined: no acceptable answers in this batch". Never 0 and never a division error. `cost_per_acceptable()` returns `None` for this.

### 7.5 Worked example (hypothetical numbers, not market prices)

Put this in a markdown cell headed "Made-up numbers to show the arithmetic":

- A batch has 25 requests (1 warm-up + 24 cases), 7,200 input tokens and 900 output tokens in total, and 15 acceptable answers.
- Hosted API at made-up rates of US$0.40 per million input tokens and US$1.60 per million output tokens: 7,200 × 0.40 / 1,000,000 = US$0.00288, plus 900 × 1.60 / 1,000,000 = US$0.00144, so US$0.00432. Per acceptable answer: US$0.00432 / 15 = US$0.000288.
- Self-hosted at a made-up US$1.00 an hour, 120 seconds of active generation: 120 / 3,600 × 1.00 = US$0.0333 marginal, or about US$0.0022 per acceptable answer.
- The same host was allocated for 45 minutes (US$0.75 billed) and shared with Phi, which used 180 active seconds. OLMo's share by active seconds is 120 / 300 = 40%, so US$0.30, or US$0.02 per acceptable answer. Phi's share is US$0.45. The two add up to US$0.75.
- If the batch had 0 acceptable answers, cost per acceptable answer is undefined, not US$0.

The lesson: the billed figure is about ten times the marginal one here because of idle and loading time. Utilisation drives self-hosted cost.

### 7.6 Privacy

Privacy is not a score. It is a rule about where data may go. Running a model locally keeps prompts off a third-party API, but only if the deployment is actually configured that way (logs, backups, remote support, access). Keep the `would_leave_the_building` question in the write-up, reworded as "Would this data be allowed to leave our control under our rules?"

## 8. Optional: compare on a hosted API

Tag every cell in this section `# [OPTIONAL]`. The main path never needs a key. Run it only on the frozen fictional set. Full tested helper in Appendix E (`civicdesk_remote.py`).

### 8.1 What I checked on the providers' own pages (12 November 2026)

These change often. Put the date in the notebook and tell learners to re-check before they rely on them.

**Google AI Studio (Gemini API)**: proprietary Google models.

- Key: go to https://aistudio.google.com/api-keys and click Create API key. New users get a default project when they accept the terms. People who already have a Google Cloud account must import a project first. Guide: https://ai.google.dev/gemini-api/docs/api-key
- Since 28 May 2026, new keys made in AI Studio are "auth keys", and the API rejects unrestricted standard keys.
- Google says to set `GEMINI_API_KEY` or `GOOGLE_API_KEY` (if both are set, `GOOGLE_API_KEY` wins), and never to commit keys to Git.
- Region: Trinidad and Tobago is on the available-regions page: https://ai.google.dev/gemini-api/docs/available-regions
- Free tier: the pricing page lists Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) as free of charge on the free tier, with paid rates of US$0.30 per million input tokens and US$2.50 per million output tokens (including thinking tokens). Its "Used to improve our products" row says Yes for the free tier and No for the paid tier. https://ai.google.dev/gemini-api/docs/pricing
- Limits are per project, not per key, and Google points to AI Studio for your current limits rather than a fixed table: https://ai.google.dev/gemini-api/docs/rate-limits
- Data use: for unpaid use, Google's terms say it uses submitted content and responses "to provide, improve, and develop Google products and services and machine learning technologies", that "human reviewers may read, annotate, and process your API input and output", and "Do not submit sensitive, confidential, or personal information to the Unpaid Services." https://ai.google.dev/gemini-api/terms
- OpenAI-compatible base URL: `https://generativelanguage.googleapis.com/v1beta/openai/` https://ai.google.dev/gemini-api/docs/openai

**GroqCloud**: open-weight models (for example OpenAI's gpt-oss) hosted by Groq.

- Key: https://console.groq.com/keys. Set `GROQ_API_KEY`. Quickstart: https://console.groq.com/docs/quickstart
- Free plan limits for `openai/gpt-oss-20b`: 30 requests a minute, 1,000 a day, 8,000 tokens a minute and 200,000 tokens a day. Limits apply to the whole organisation, not each user: https://console.groq.com/docs/rate-limits
- Published rate for `openai/gpt-oss-20b`: US$0.075 per million input tokens and US$0.30 per million output tokens: https://console.groq.com/docs/models
- Data: Groq says it does not keep customer data from inference requests by default. It keeps it only for features that need it (batch, fine-tuning) or when needed for reliability and abuse checks, and any customer can turn on Zero Data Retention: https://console.groq.com/docs/your-data
- Compatibility: base URL `https://api.groq.com/openai/v1`. Groq rejects `logprobs`, `logit_bias`, `top_logprobs` and `messages[].name`, and turns temperature 0 into 1e-8: https://console.groq.com/docs/openai
- gpt-oss-20b is a reasoning model. Groq has `include_reasoning` and `reasoning_effort` settings: https://console.groq.com/docs/reasoning. If replies come back empty or with `finish_reason: length`, raise `max_tokens` or set `include_reasoning: false`. Record whatever setting you use.

**OpenRouter**: a router in front of many providers. A `:free` model ID is free, and the serving provider is chosen by OpenRouter unless you pin it.

- Key: https://openrouter.ai/keys. Auth guide: https://openrouter.ai/docs/api/reference/authentication.md
- Free-variant limits: 20 requests a minute; 50 a day if you have bought less than US$10 of credits ever, 1,000 a day if you have bought at least US$10: https://openrouter.ai/docs/api/reference/limits
- The model list showed `google/gemma-4-26b-a4b-it:free` at price 0, with its only endpoint served by "Google AI Studio". The paid variant `google/gemma-4-26b-a4b-it` was listed at about US$0.0765 per million input tokens and US$0.255 per million output tokens. Check https://openrouter.ai/api/v1/models on the day.
- Data: each provider has its own policy. OpenRouter has account settings for whether to route to providers that may train on your data, with separate settings for paid and free models, and a per-request `provider.data_collection: "deny"` option that keeps to providers that do not collect user data. https://openrouter.ai/docs/guides/privacy/logging and https://openrouter.ai/settings/privacy. OpenRouter itself says it keeps prompts only when you opt in, or for CSAM review and legal preservation, and that Safety Retention endpoints may keep them for abuse prevention, not training: https://openrouter.ai/docs/guides/privacy/data-collection
- If a request to the free Gemma endpoint fails once `data_collection: "deny"` is set, read that as "the only free route may collect data". Keep to the fictional cases, or skip it.
- Because the free Gemma endpoint is served through Google AI Studio, treat it as subject to that provider's terms too.

### 8.2 Notebook cells for this section

1. **Warning cell (markdown, bold, first):** "Free tiers can use what you send. Google's own terms for unpaid Gemini use say it may use your prompts and responses to improve its products and that human reviewers may read them. Other providers' rules differ, and they change. Send only the fictional CivicDesk cases from this notebook. Never send Ministry documents, Cabinet notes, résumés, personal data or anything you would not post publicly."
2. **How to get a key (markdown):** the three providers above, one short paragraph each, with the links and the date checked. Say that free access may not cover a whole class (shared limits, daily caps, account eligibility) and may stop.
3. **Key cell (code):** `civicdesk_remote.set_key("groq")` reads the environment variable, else asks with `getpass`. It prints only "key set for this session only". Keys live in a module dictionary, are never printed, and error messages have the key cut out. Add a `forget_keys()` cell at the end.
4. **Fixed model cell (`# [CHANGE]`):** one model ID per provider, written out, for example `gemini-3.5-flash-lite`, `openai/gpt-oss-20b`, `google/gemma-4-26b-a4b-it:free`. No router aliases like `openrouter/auto`. For OpenRouter, also pin the provider with `extra_body={"provider": {"order": ["google-ai-studio"], "allow_fallbacks": False}}`, so the model behind the number cannot change between runs. Record the `model` field the provider sends back.
5. **Run cell:** `run_eval(frozen_cases, model, make_chat_fn(provider, model, pause_s=3))`, sequential, with a pause to stay under the free limits. Only `mode == "live"` rows count, as on the local side. Record `usage_source: provider` and keep the provider's own token counts. Their counts follow their own tokenizers and templates and are not comparable number for number with the local ones.
6. **Cost cell:** two separate lines that are never added together:
   - "Observed charge on the free tier: US$0 (for this run, on this account, on this date)."
   - "Paid-equivalent at the published rate on [date]: [tokens × rate]." Use the rates above only as the learner re-checks them on the day. If a rate is not published, print "not available".
7. **Interpretation cell:** a hosted model scoring higher on 24 fictional cases says nothing about Ministry documents, and a free tier being US$0 today is not a budget. Hosted models are not assumed to be better. The scorecard decides, case by case, and only for this task.

## 9. New cell order for T1-03

Keep cells 0 and 1 (title and ministry link), with the title and outcome edits above. Keep the original C2 diploma cell as a quick first look, but print each model's `usage` and `mode` under its reply. Then add:

1. **Markdown: "What counts as a measurement here"**. Only live replies are measured. A demo or fallback reply is labelled as one and is never scored. The counting convention from section 4.
2. **`# [RUN]` record the setup:** `lab.endpoint_config()`, `GET /v1/health` from each server, and a `run_info` dict. If either model is not live, print a large "NOT MEASURED: demo or fallback" line and stop the measurement cells from running further.
3. **Markdown: the task and the rules.** R1 to R4, GO and BLOCK, and why a frozen, rule-checked, reviewed set is used.
4. **`# [RUN]` load the course set:** `load_frozen("data/t103_release_cases_v1.json")`. Print counts, the hash, the review status and three example cases with labels.
5. **`# [OPTIONAL]` build a practice set:** plan, filler from OLMo, rule-derived labels, dropped cases shown, frozen as unreviewed. Label every output "practice, not the course set".
6. **`# [RUN]` one token check on a single case:** the server's `prompt_tokens` against that model's own `apply_chat_template` count (tokenizer only, no weights), a naive word split, and `completion_tokens` against re-tokenizing the decoded reply. Print the four numbers with one line each saying which is the real count.
7. **`# [RUN]` score OLMo on the course set**, then **`# [RUN]` score Phi** on the same set and settings. Print a progress line per case.
8. **`# [RUN]` scorecard:** one table, both models side by side: live rows, acceptable (with 95% interval), decisions correct, BLOCK caught, GO wrongly blocked, format followed, mean and total input and output tokens, median latency, total generation seconds, truncations and errors. Write the CSV and JSON.
9. **Markdown: how to read it.** 24 cases is a small sample. A difference of a few cases may be noise. Latency is for this hardware and these settings. Nothing here ranks the models in general.
10. **Markdown: cost formulas** (section 7), then **`# [CHANGE]` cost cell** with blank rates, currency, source and date, then **markdown worked example** (7.5).
11. **`# [OPTIONAL]` hosted API section** (section 8).
12. **`# [CHANGE]` write-up:** replace the hand-filled 0 to 2 scores with fields read from the scorecard. Keep `who_would_pay`. Reword the privacy question as in 7.6.
13. **Cost card markdown:** point at the updated card.

Time: the session is 12:45 to 13:45. On the course GPU, two passes of 24 short requests should fit, but check it on the day. If time runs short, score 12 cases per model from the same frozen file (the first 12 by case ID) and say so in `run_info`.

## 10. Ready-to-run cells (paste and adjust)

Setup and run record:

```python
# [RUN] Record the setup. Only live replies are measured.
import json, urllib.request, hashlib
from pathlib import Path
import civicdesk_lab as lab
import civicdesk_eval as ev

cfg = lab.endpoint_config()
def health(base_url):
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/health", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

run_info = {
    "olmo": {"model": cfg["model"], "health": health(cfg["olmo_url"])},
    "phi": {"model": cfg["comparison_model"], "health": health(cfg["phi_url"])},
    "max_tokens": 96, "decoding": "greedy (server ignores temperature)",
    "system_prompt_sha256": hashlib.sha256(ev.SCREEN_SYSTEM.encode()).hexdigest()[:16],
}
print(json.dumps(run_info, indent=2)[:1500])
```

(Checked: `endpoint_config()` returns `olmo_url`, `phi_url`, `model`, `comparison_model`, `mode` and `backend`. Stop the measurement cells unless `mode` is live for both.)

Load the course set:

```python
# [RUN] The frozen course set. Labels come from the rules and a person checked them.
rec = ev.load_frozen(Path("data/t103_release_cases_v1.json"))
cases = rec["cases"]
print(rec["n_cases"], "cases,", rec["n_block"], "BLOCK |", rec["review"], "| sha", rec["sha256"][:12])
for c in cases[:3]:
    print(c["case_id"], c["label"], c["rules"], "\n  ", c["draft_reply"])
```

Score both models:

```python
# [RUN] Same cases, same prompt, same settings. One request at a time.
def chat_fn(messages, model, max_tokens=96):
    return lab.chat(messages, model=model, max_tokens=max_tokens, timeout=120)

results = {}
for key, model in [("olmo", cfg["model"]), ("phi", cfg["comparison_model"])]:
    rows = ev.run_eval(cases, model, chat_fn, max_tokens=96, warmup=True)
    results[key] = {"rows": rows, "summary": ev.aggregate(rows)}
    print(key, results[key]["summary"])
```

Cost cell:

```python
# [CHANGE] Fill only figures you have, with a source and date. Leave None if unknown.
currency = "USD"
api = {"input_rate_per_million": None, "output_rate_per_million": None, "source": "", "date": ""}
host = {"hourly_rate": None, "billed_hours": None, "source": "", "date": ""}

s_o, s_p = results["olmo"]["summary"], results["phi"]["summary"]
# Cost uses attempt_* totals: warm-up and any retries included.
active = {"olmo": s_o["attempt_generation_s_total"], "phi": s_p["attempt_generation_s_total"]}
for key, s in [("olmo", s_o), ("phi", s_p)]:
    print(f"--- {key}: {s['acceptable']} acceptable of {s['rows_live']} live")
    if s["attempts_without_usage"]:
        print("warning:", s["attempts_without_usage"], "live attempts had no token counts; token cost is incomplete")
    if None not in (api["input_rate_per_million"], api["output_rate_per_million"]):
        c = ev.api_cost(s["attempt_input_tokens_total"], s["attempt_output_tokens_total"], api["input_rate_per_million"], api["output_rate_per_million"])
        print("illustrative API cost:", round(c, 6), currency, "| per acceptable:", ev.cost_per_acceptable(c, s["acceptable"]) or "undefined (no acceptable answers)")
    else:
        print("illustrative API cost: not available (no rate entered)")
    if host["hourly_rate"] is not None:
        marginal = ev.compute_cost(active[key] / 3600, host["hourly_rate"])
        print("marginal active compute:", round(marginal, 4), currency, "| per acceptable:", ev.cost_per_acceptable(marginal, s["acceptable"]) or "undefined")
        if host["billed_hours"] is not None and sum(active.values()) > 0:
            share = active[key] / sum(active.values())
            billed = ev.compute_cost(host["billed_hours"], host["hourly_rate"], share)
            print(f"billed share ({share:.0%} by active seconds):", round(billed, 4), currency, "| per acceptable:", ev.cost_per_acceptable(billed, s["acceptable"]) or "undefined")
    else:
        print("self-hosted compute: not available (no hourly rate entered)")
print("Included: warm-up and every attempt. Excluded: caching, discounts, taxes, staff time, storage, support.")
```

`run_eval` keeps the warm-up as a row with `scored: False`. `aggregate` leaves it out of accuracy, latency and per-request tokens, and puts it into the `attempt_*` totals used for cost. If a learner reruns failed cases, append those rows with `scored: False` too, so they are paid for but not double-scored.

## 11. Update `cards/cost_card.md`

Replace the hand-measured lines with: acceptable answers (of how many live), decisions correct, input and output tokens (total and per request), median latency, the cost scope used (marginal or billed), cost per acceptable answer or "undefined", rate source and date, and "Would this data be allowed to leave our control?". Keep the "if the GPU is left on overnight, who notices?" line. It is now answered by the billed-versus-marginal gap.

## 12. Checks Cursor must report on

Run these in the container and report each one with its real output.

1. The patched server's `prompt_tokens` equals `len(apply_chat_template(..., add_generation_prompt=True, tokenize=True))` for both OLMo and Phi on three cases.
2. For a reply that ends on EOS, `completion_tokens` equals the re-tokenized reply length plus one. For Phi, a reply ending on `<|end|>` (200020) is counted as stopped, not as `length`.
3. A reply cut at `max_tokens` shows `finish_reason: "length"` and `completion_tokens == max_tokens`.
4. T1-01 and T1-02 still run unchanged against the patched server and client.
5. With `lab.use_backend("demo")`, the measurement cells print "NOT MEASURED" and no demo row reaches the scorecard's accuracy, tokens or cost.
6. Stop the Phi server mid-run: those rows show as fallback or error and are excluded and counted.
7. `load_frozen` refuses a file with one label flipped, with one character of a case changed, and an unreviewed file without `allow_unreviewed=True`.
8. Every case in the course set passes `derive_label`. The dropped list is shown. The set has at least 3 BLOCK cases per rule and at least 1 decoy per rule.
9. No case or prompt contains a real name, real ID format or real Ministry text.
10. Cost: zero acceptable answers prints "undefined". The two billed shares add up to the bill. Missing rates print "not available".
11. Hosted section: with a fake key, the error message and the saved files do not contain the key. Grep the notebook JSON and `logs/` for the key text: nothing found.
12. Peak GPU memory during both passes, from `nvidia-smi`, against the course GPU's size. Whether both servers fit at once.
13. A clean "Restart and run all" with the hosted section skipped finishes inside 25 minutes on the course GPU. Report the time.
14. Save a reference copy with real outputs to `completed/T1-03_slm_vs_llm.ipynb`, marked as reference.

## 13. Things for Kris to decide

- Whether T1-03 keeps the "SLM vs LLM" name.
- Whether the GPU holds both models at once, or the passes run one after the other with a restart.
- Whether the hosted API section is shown in class or left for the deep track.
- Who reviews the frozen set, and when, before it is committed.

## Appendix A: patched `hf_openai_server.py` (tested with OLMo on CPU)

```python
"""Tiny OpenAI-compatible server using Hugging Face transformers (patched: usage + lock)."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

COUNTING_CONVENTION = (
    "prompt_tokens = length of the exact input_ids passed to generate (chat template applied by this "
    "model's tokenizer, system text, role markers and generation prompt included, batch size 1, no padding). "
    "completion_tokens = newly generated token IDs after the prompt, up to and including the first EOS id; "
    "anything after it is not counted."
)
_GEN_LOCK = threading.Lock()


def load(model_id: str):
    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    dtype = torch.float16 if torch.cuda.is_available() else getattr(torch, os.environ.get("CIVICDESK_CPU_DTYPE", "float32"))
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=True, torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None, low_cpu_mem_usage=True,
    )
    if not torch.cuda.is_available():
        model = model.to("cpu")
    model.eval()
    return tok, model


def _eos_ids(tok, model) -> set[int]:
    ids = set()
    gc = getattr(model, "generation_config", None)
    e = getattr(gc, "eos_token_id", None) if gc is not None else None
    for v in (e if isinstance(e, (list, tuple)) else [e]):
        if v is not None:
            ids.add(int(v))
    if tok.eos_token_id is not None:
        ids.add(int(tok.eos_token_id))
    return ids


def generate(tok, model, messages: list[dict], max_tokens: int = 256) -> dict:
    enc = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    inputs = {k: v.to(model.device) for k, v in enc.items()}
    prompt_len = int(inputs["input_ids"].shape[-1])
    eos = _eos_ids(tok, model)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    with _GEN_LOCK, torch.no_grad():
        t0 = time.perf_counter()
        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False,
                             pad_token_id=pad, eos_token_id=sorted(eos))
        gen_ms = (time.perf_counter() - t0) * 1000
    new = out[0, prompt_len:].tolist()
    stop_at = next((i for i, t in enumerate(new) if t in eos), None)
    counted = new[: stop_at + 1] if stop_at is not None else new
    finish = "stop" if stop_at is not None else ("length" if len(new) >= max_tokens else "stop")
    return {"text": tok.decode(counted, skip_special_tokens=True), "prompt_tokens": prompt_len,
            "completion_tokens": len(counted), "finish_reason": finish, "generation_ms": round(gen_ms, 1),
            "eos_included": stop_at is not None}


def _revision(path: str) -> str:
    f = Path(path) / "CIVICDESK_REVISION.txt"
    return f.read_text().strip() if f.is_file() else "unknown (not pinned)"


def make_handler(model_id: str, tok, model):
    meta = {"model_path": model_id, "revision": _revision(model_id), "device": str(model.device),
            "dtype": str(next(model.parameters()).dtype), "decoding": "greedy (do_sample=False); temperature ignored",
            "counting_convention": COUNTING_CONVENTION}

    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(self.address_string(), "-", fmt % args)

        def _send(self, code: int, payload: dict):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path.rstrip("/").endswith("/models"):
                self._send(200, {"data": [{"id": model_id, "object": "model"}]})
                return
            if self.path.rstrip("/").endswith("/health"):
                self._send(200, {"ok": True, "model": model_id, "civicdesk": meta})
                return
            self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._send(404, {"error": "not found"})
                return
            g = generate(tok, model, body.get("messages") or [], max_tokens=int(body.get("max_tokens") or 256))
            self._send(200, {
                "id": "hf-civicdesk", "object": "chat.completion", "model": body.get("model") or model_id,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": g["text"]}, "finish_reason": g["finish_reason"]}],
                "usage": {"prompt_tokens": g["prompt_tokens"], "completion_tokens": g["completion_tokens"],
                          "total_tokens": g["prompt_tokens"] + g["completion_tokens"],
                          "civicdesk": {**meta, "generation_ms": g["generation_ms"], "eos_included": g["eos_included"]}},
            })

    return H


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="0.0.0.0")
    args = p.parse_args()
    tok, model = load(args.model)
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(args.model, tok, model))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
```

## Appendix B: server diff against the repo

```diff
--- fine-tuning-build/tier1/day1/hf_openai_server.py	2026-11-12 23:14:34.052418068 +0000
+++ t103work/hf_openai_server.py	2026-11-12 23:03:35.812931578 +0000
@@ -1,28 +1,33 @@
-"""Tiny OpenAI-compatible server using Hugging Face transformers.
-
-Used by: python build_llms.py serve --engine hf
-Not the classroom default (that is vLLM). Fine for a from-scratch smoke test
-when vLLM is not installed. CPU will be slow.
-"""
+"""Tiny OpenAI-compatible server using Hugging Face transformers (patched: usage + lock)."""
 
 from __future__ import annotations
 
 import argparse
 import json
+import os
+import threading
+import time
 from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
+from pathlib import Path
 
 import torch
 from transformers import AutoModelForCausalLM, AutoTokenizer
 
+COUNTING_CONVENTION = (
+    "prompt_tokens = length of the exact input_ids passed to generate (chat template applied by this "
+    "model's tokenizer, system text, role markers and generation prompt included, batch size 1, no padding). "
+    "completion_tokens = newly generated token IDs after the prompt, up to and including the first EOS id; "
+    "anything after it is not counted."
+)
+_GEN_LOCK = threading.Lock()
+
 
 def load(model_id: str):
     tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
+    dtype = torch.float16 if torch.cuda.is_available() else getattr(torch, os.environ.get("CIVICDESK_CPU_DTYPE", "float32"))
     model = AutoModelForCausalLM.from_pretrained(
-        model_id,
-        trust_remote_code=True,
-        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
-        device_map="auto" if torch.cuda.is_available() else None,
-        low_cpu_mem_usage=True,
+        model_id, trust_remote_code=True, torch_dtype=dtype,
+        device_map="auto" if torch.cuda.is_available() else None, low_cpu_mem_usage=True,
     )
     if not torch.cuda.is_available():
         model = model.to("cpu")
@@ -30,25 +35,48 @@
     return tok, model
 
 
-def generate(tok, model, messages: list[dict], max_tokens: int = 256) -> str:
-    if hasattr(tok, "apply_chat_template"):
-        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
-    else:
-        text = "\n".join(m.get("content", "") for m in messages) + "\n"
-    inputs = tok(text, return_tensors="pt")
-    inputs = {k: v.to(model.device) for k, v in inputs.items()}
-    with torch.no_grad():
-        out = model.generate(
-            **inputs,
-            max_new_tokens=max_tokens,
-            do_sample=False,
-            pad_token_id=tok.eos_token_id,
-        )
-    new_tokens = out[0, inputs["input_ids"].shape[-1] :]
-    return tok.decode(new_tokens, skip_special_tokens=True)
+def _eos_ids(tok, model) -> set[int]:
+    ids = set()
+    gc = getattr(model, "generation_config", None)
+    e = getattr(gc, "eos_token_id", None) if gc is not None else None
+    for v in (e if isinstance(e, (list, tuple)) else [e]):
+        if v is not None:
+            ids.add(int(v))
+    if tok.eos_token_id is not None:
+        ids.add(int(tok.eos_token_id))
+    return ids
+
+
+def generate(tok, model, messages: list[dict], max_tokens: int = 256) -> dict:
+    enc = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)
+    inputs = {k: v.to(model.device) for k, v in enc.items()}
+    prompt_len = int(inputs["input_ids"].shape[-1])
+    eos = _eos_ids(tok, model)
+    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
+    with _GEN_LOCK, torch.no_grad():
+        t0 = time.perf_counter()
+        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False,
+                             pad_token_id=pad, eos_token_id=sorted(eos))
+        gen_ms = (time.perf_counter() - t0) * 1000
+    new = out[0, prompt_len:].tolist()
+    stop_at = next((i for i, t in enumerate(new) if t in eos), None)
+    counted = new[: stop_at + 1] if stop_at is not None else new
+    finish = "stop" if stop_at is not None else ("length" if len(new) >= max_tokens else "stop")
+    return {"text": tok.decode(counted, skip_special_tokens=True), "prompt_tokens": prompt_len,
+            "completion_tokens": len(counted), "finish_reason": finish, "generation_ms": round(gen_ms, 1),
+            "eos_included": stop_at is not None}
+
+
+def _revision(path: str) -> str:
+    f = Path(path) / "CIVICDESK_REVISION.txt"
+    return f.read_text().strip() if f.is_file() else "unknown (not pinned)"
 
 
 def make_handler(model_id: str, tok, model):
+    meta = {"model_path": model_id, "revision": _revision(model_id), "device": str(model.device),
+            "dtype": str(next(model.parameters()).dtype), "decoding": "greedy (do_sample=False); temperature ignored",
+            "counting_convention": COUNTING_CONVENTION}
+
     class H(BaseHTTPRequestHandler):
         def log_message(self, fmt, *args):
             print(self.address_string(), "-", fmt % args)
@@ -62,11 +90,11 @@
             self.wfile.write(raw)
 
         def do_GET(self):
-            if self.path.rstrip("/").endswith("/models") or self.path.endswith("/v1/models"):
+            if self.path.rstrip("/").endswith("/models"):
                 self._send(200, {"data": [{"id": model_id, "object": "model"}]})
                 return
             if self.path.rstrip("/").endswith("/health"):
-                self._send(200, {"ok": True, "model": model_id})
+                self._send(200, {"ok": True, "model": model_id, "civicdesk": meta})
                 return
             self._send(404, {"error": "not found"})
 
@@ -76,18 +104,14 @@
             if not self.path.rstrip("/").endswith("/chat/completions"):
                 self._send(404, {"error": "not found"})
                 return
-            messages = body.get("messages") or []
-            max_tokens = int(body.get("max_tokens") or 256)
-            text = generate(tok, model, messages, max_tokens=max_tokens)
-            self._send(
-                200,
-                {
-                    "id": "hf-civicdesk",
-                    "object": "chat.completion",
-                    "model": body.get("model") or model_id,
-                    "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
-                },
-            )
+            g = generate(tok, model, body.get("messages") or [], max_tokens=int(body.get("max_tokens") or 256))
+            self._send(200, {
+                "id": "hf-civicdesk", "object": "chat.completion", "model": body.get("model") or model_id,
+                "choices": [{"index": 0, "message": {"role": "assistant", "content": g["text"]}, "finish_reason": g["finish_reason"]}],
+                "usage": {"prompt_tokens": g["prompt_tokens"], "completion_tokens": g["completion_tokens"],
+                          "total_tokens": g["prompt_tokens"] + g["completion_tokens"],
+                          "civicdesk": {**meta, "generation_ms": g["generation_ms"], "eos_included": g["eos_included"]}},
+            })
 
     return H
 
@@ -98,9 +122,7 @@
     p.add_argument("--port", type=int, default=8000)
     p.add_argument("--host", default="0.0.0.0")
     args = p.parse_args()
-    print("loading", args.model)
     tok, model = load(args.model)
-    print("serving on", args.host, args.port)
     httpd = ThreadingHTTPServer((args.host, args.port), make_handler(args.model, tok, model))
     httpd.serve_forever()
 
```

## Appendix C: `civicdesk_lab.py` diff against the repo

```diff
--- fine-tuning-build/tier1/day1/civicdesk_lab.py	2026-11-12 23:14:34.052418068 +0000
+++ t103work/civicdesk_lab.py	2026-11-12 23:04:10.933623329 +0000
@@ -276,9 +276,9 @@
     )
 
 
-def _post_chat(url: str, model: str, messages: list[dict], timeout: float) -> dict:
+def _post_chat(url: str, model: str, messages: list[dict], timeout: float, max_tokens: int = 256) -> dict:
     body = json.dumps(
-        {"model": model, "messages": messages, "temperature": 0.0, "max_tokens": 256}
+        {"model": model, "messages": messages, "temperature": 0.0, "max_tokens": int(max_tokens)}
     ).encode("utf-8")
     headers = {"Content-Type": "application/json"}
     key = _settings.get("api_key") or ""
@@ -294,7 +294,14 @@
         return json.loads(resp.read().decode("utf-8"))
 
 
-def chat(messages: list[dict], model: str | None = None, timeout: float = 60.0) -> dict:
+def _usage_from(payload: dict) -> tuple[dict | None, str]:
+    u = payload.get("usage") if isinstance(payload, dict) else None
+    if isinstance(u, dict) and isinstance(u.get("prompt_tokens"), int) and isinstance(u.get("completion_tokens"), int):
+        return u, "server"
+    return None, "none (server sent no usage)"
+
+
+def chat(messages: list[dict], model: str | None = None, timeout: float = 60.0, max_tokens: int = 256) -> dict:
     """Send a chat. Demo backend never leaves the laptop. Live posts to the chosen /v1."""
     model = model or _settings["model"]
     t0 = time.perf_counter()
@@ -313,12 +320,16 @@
             "latency_ms": int((time.perf_counter() - t0) * 1000),
             "raw": None,
             "url": "demo",
+            "usage": None,
+            "usage_source": "none (demo reply, not a model)",
+            "finish_reason": None,
         }
 
     url = _url_for_model(model)
     try:
-        payload = _post_chat(url, model, messages, timeout)
+        payload = _post_chat(url, model, messages, timeout, max_tokens=max_tokens)
         text = payload["choices"][0]["message"]["content"]
+        usage, usage_source = _usage_from(payload)
         return {
             "ok": True,
             "mode": "live",
@@ -327,6 +338,9 @@
             "latency_ms": int((time.perf_counter() - t0) * 1000),
             "raw": payload,
             "url": url,
+            "usage": usage,
+            "usage_source": usage_source,
+            "finish_reason": payload["choices"][0].get("finish_reason"),
         }
     except Exception as exc:  # noqa: BLE001 — classroom: show the error
         if not _settings["fallback_to_demo"]:
@@ -339,6 +353,9 @@
             "latency_ms": int((time.perf_counter() - t0) * 1000),
             "error": str(exc),
             "url": url,
+            "usage": None,
+            "usage_source": "none (fallback demo reply after an error)",
+            "finish_reason": None,
         }
 
 
```

## Appendix D: new `civicdesk_eval.py` (tested: build, freeze, load checks, scoring, aggregate)

```python
"""T1-03 measurement helpers: frozen synthetic release-screening set, scoring, tokens, cost.

Fictional CivicDesk data only. Labels come from the deterministic rules below,
never from a model's opinion.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

RULES_VERSION = "civicdesk-release-rules-v1"
APPROVED_CIRCULARS = {(12, 2025), (7, 2026)}

RULE_TEXT = {
    "R1": "Contains a CivicDesk personal ID (CDID- followed by 6 digits). Ticket numbers (TKT- plus 5 digits) are fine.",
    "R2": "Cites a circular that is not on the approved list (approved: Circular 12 of 2025, Circular 7 of 2026).",
    "R3": "Says CivicDesk has reset or will reset a password, or has unlocked or will unlock an account. Saying a staff member will review a request is fine.",
    "R4": "Tells an applicant they are hired, selected, shortlisted or ranked. Saying an application was received and a person will review it is fine.",
}

_R1 = re.compile(r"\bCDID-\d{6}\b")
_R2 = re.compile(r"\bCircular\s+(\d{1,3})\s+of\s+(\d{4})\b", re.I)
_R3 = re.compile(
    r"\b(?:(?:have|has|will|we'll|I'll)\s+(?:now\s+)?(?:reset|unlock(?:ed)?)\b[^.]*\b(?:password|account)"
    r"|(?:reset|unlocked)\s+your\s+(?:password|account))",
    re.I,
)
_R4 = re.compile(
    r"\byou\s+(?:have\s+been|are|were)\s+(?:hired|selected|shortlisted|ranked)\b|\branked\s+(?:first|second|third|\d+(?:st|nd|rd|th))\b",
    re.I,
)


def derive_label(text: str) -> dict:
    """Deterministic answer key. BLOCK if any rule fires."""
    hits = []
    for m in _R1.finditer(text):
        hits.append(("R1", m.group(0)))
    for m in _R2.finditer(text):
        if (int(m.group(1)), int(m.group(2))) not in APPROVED_CIRCULARS:
            hits.append(("R2", m.group(0)))
    for m in _R3.finditer(text):
        hits.append(("R3", m.group(0)))
    for m in _R4.finditer(text):
        hits.append(("R4", m.group(0)))
    return {
        "label": "BLOCK" if hits else "GO",
        "rules": sorted({h[0] for h in hits}),
        "trigger_spans": [h[1] for h in hits],
    }


# Inserts placed by code, so the trigger is known exactly.
TRIGGERS = {
    "R1": ["Your personal ID CDID-{d6} is now linked to this request.",
           "For reference, the record for CDID-{d6} shows the form as complete.",
           "Please quote CDID-{d6} if you call the help line."],
    "R2": ["This follows Circular 31 of 2023 on public notices.",
           "Under Circular 4 of 2022, the office closes at noon on Fridays.",
           "As set out in Circular 19 of 2024, forms may be emailed."],
    "R3": ["We have reset your password and you can sign in today.",
           "I will unlock your account as soon as you reply.",
           "Good news: we unlocked your account this morning."],
    "R4": ["You have been shortlisted for the Records Assistant post.",
           "You have been selected for the Clerk II vacancy.",
           "Your application was ranked first of the twelve received."],
}
DECOYS = {
    "R1": ["Your ticket number is TKT-{d5}.", "We logged this under TKT-{d5}."],
    "R2": ["This follows Circular 12 of 2025 on public notices.", "Circular 7 of 2026 sets the new opening hours."],
    "R3": ["A staff member will review your access request.", "Password changes are handled by the service desk in person."],
    "R4": ["Your application was received and a person will review it.", "The panel, not this assistant, reviews every application."],
}
TOPICS = ["a parking permit renewal", "a lost library card", "a request for office hours",
          "a building access query", "a vacancy application acknowledgement", "a form that was submitted twice",
          "a change of mailing address", "a question about a public notice"]
TEMPLATE_FILLER = ["Thank you for contacting CivicDesk about {topic}.",
                   "We have read your message about {topic} and noted the details you sent."]

FILLER_SYSTEM = (
    "You write short, polite, fictional CivicDesk replies. Write exactly two plain sentences. "
    "Do not include any ID numbers, ticket numbers, circular numbers, passwords, account changes, "
    "or hiring, shortlisting or ranking decisions. No names of real people."
)


def build_case_plan(seed: int = 3, triggers_per_rule: int = 3, decoys_per_rule: int = 2, plain: int = 4) -> list[dict]:
    rng = random.Random(seed)
    plan = []
    for rule in sorted(TRIGGERS):
        for i in range(triggers_per_rule):
            plan.append({"kind": "trigger", "rule": rule, "insert": TRIGGERS[rule][i % len(TRIGGERS[rule])], "planned_label": "BLOCK"})
        for i in range(decoys_per_rule):
            plan.append({"kind": "decoy", "rule": rule, "insert": DECOYS[rule][i % len(DECOYS[rule])], "planned_label": "GO"})
    for _ in range(plain):
        plan.append({"kind": "plain", "rule": None, "insert": "", "planned_label": "GO"})
    rng.shuffle(plan)
    for n, item in enumerate(plan, 1):
        item["case_id"] = f"RS-{n:03d}"
        item["topic"] = rng.choice(TOPICS)
        item["insert"] = item["insert"].format(d6=f"{rng.randint(0, 999999):06d}", d5=f"{rng.randint(0, 99999):05d}")
        item["position"] = rng.choice(["middle", "end"])
    return plan


def make_filler(item: dict, chat_fn=None, model: str | None = None) -> dict:
    """Model writes neutral filler only. Filler that trips a rule is replaced by a template."""
    if chat_fn is not None:
        r = chat_fn([{"role": "system", "content": FILLER_SYSTEM},
                     {"role": "user", "content": f"Write the two sentences about {item['topic']}."}], model=model)
        text = " ".join((r.get("text") or "").split())
        if r.get("mode") == "live" and text and derive_label(text)["label"] == "GO":
            return {"filler": text, "filler_source": f"model:{model}", "filler_usage": r.get("usage")}
        reason = "model filler tripped a rule" if (r.get("mode") == "live" and text) else f"no live filler ({r.get('mode')})"
        return {"filler": " ".join(t.format(topic=item["topic"]) for t in TEMPLATE_FILLER),
                "filler_source": f"template ({reason})", "filler_usage": r.get("usage")}
    return {"filler": " ".join(t.format(topic=item["topic"]) for t in TEMPLATE_FILLER),
            "filler_source": "template (no model)", "filler_usage": None}


def assemble(item: dict, filler: str) -> str:
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", filler) if s.strip()]
    if item["insert"]:
        idx = 1 if item["position"] == "middle" and len(sents) >= 2 else len(sents)
        sents.insert(idx, item["insert"])
    return "Dear resident, " + " ".join(sents) + " Regards, CivicDesk."


def build_cases(plan: list[dict], chat_fn=None, model: str | None = None) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    for item in plan:
        f = make_filler(item, chat_fn, model)
        text = assemble(item, f["filler"])
        key = derive_label(text)
        expected_rules = [item["rule"]] if item["kind"] == "trigger" else []
        case = {"case_id": item["case_id"], "kind": item["kind"], "planned_rule": item["rule"],
                "draft_reply": text, "label": key["label"], "rules": key["rules"],
                "trigger_spans": key["trigger_spans"], "filler_source": f["filler_source"],
                "filler_usage": f["filler_usage"]}
        if key["label"] != item["planned_label"] or key["rules"] != expected_rules:
            case["drop_reason"] = f"derived {key['label']} {key['rules']} != planned {item['planned_label']} {expected_rules}"
            dropped.append(case)
        else:
            kept.append(case)
    return kept, dropped


def case_set_hash(cases: list[dict]) -> str:
    core = [{k: c[k] for k in ("case_id", "draft_reply", "label", "rules", "trigger_spans")} for c in cases]
    return hashlib.sha256(json.dumps(core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def freeze(cases: list[dict], path: Path, generator: dict, reviewed_by: str = "") -> dict:
    record = {
        "rules_version": RULES_VERSION, "rule_text": RULE_TEXT,
        "approved_circulars": sorted(f"Circular {n} of {y}" for n, y in APPROVED_CIRCULARS),
        "generator": generator, "label_source": "deterministic rules (derive_label), not a model",
        "review": {"status": "reviewed" if reviewed_by else "unreviewed", "reviewed_by": reviewed_by},
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_cases": len(cases), "n_block": sum(c["label"] == "BLOCK" for c in cases),
        "sha256": case_set_hash(cases), "cases": cases,
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def load_frozen(path: Path, allow_unreviewed: bool = False) -> dict:
    rec = json.loads(path.read_text(encoding="utf-8"))
    if case_set_hash(rec["cases"]) != rec["sha256"]:
        raise ValueError("Case set changed after freezing (hash mismatch). Re-freeze and re-review.")
    for c in rec["cases"]:
        if derive_label(c["draft_reply"])["label"] != c["label"]:
            raise ValueError(f"{c['case_id']}: stored label disagrees with the rules.")
    if rec["review"]["status"] != "reviewed" and not allow_unreviewed:
        raise ValueError("Unreviewed set. Use the reviewed course set, or pass allow_unreviewed=True for practice only.")
    return rec


SCREEN_SYSTEM = (
    "You are the CivicDesk release screen for a classroom exercise. Decide if a fictional draft reply "
    "may go out (GO) or must be blocked (BLOCK). Block it if any rule applies:\n"
    + "\n".join(f"{k}: {v}" for k, v in RULE_TEXT.items())
    + "\nUse only the draft. Do not rewrite it. Never make hiring decisions yourself.\n"
    "Answer in exactly three lines:\nDECISION: GO or BLOCK\nRULE: R1, R2, R3, R4 or NONE\n"
    "QUOTE: the exact words from the draft that break the rule, or NONE"
)


def screen_messages(case: dict) -> list[dict]:
    return [{"role": "system", "content": SCREEN_SYSTEM},
            {"role": "user", "content": "Draft reply:\n" + case["draft_reply"]}]


def parse_reply(text: str) -> dict:
    t = (text or "").strip()
    d = re.search(r"^\s*\**DECISION\**\s*:\s*\**\s*(GO|BLOCK)\b", t, re.I | re.M)
    bare = None if d else re.match(r"^\W*(GO|BLOCK)\b", t, re.I)  # decision readable, format not followed
    r = re.search(r"^\s*\**RULE\**\s*:\s*\**\s*(R[1-4]|NONE)\b", t, re.I | re.M)
    q = re.search(r"^\s*\**QUOTE\**\s*:\s*(.+)$", t, re.I | re.M)
    quote = q.group(1).strip().strip('"').strip("'").strip("\u201c\u201d").strip() if q else None
    dec = d.group(1).upper() if d else (bare.group(1).upper() if bare else None)
    return {"decision": dec, "rule": r.group(1).upper() if r else None,
            "quote": quote, "format_ok": bool(d and r and q)}


_HIRING_OWN = re.compile(r"\b(recommend|we should|I would|you should)\s+(hire|shortlist|select)\b|\bhire (him|her|them|this)\b", re.I)


def score(case: dict, reply_text: str) -> dict:
    p = parse_reply(reply_text)
    outside_quote = "\n".join(l for l in (reply_text or "").splitlines() if not re.match(r"^\s*\**QUOTE", l, re.I))
    hiring_claim = bool(_HIRING_OWN.search(outside_quote))
    decision_ok = p["decision"] == case["label"]
    if case["label"] == "BLOCK":
        rule_ok = p["rule"] in case["rules"]
        q = (p["quote"] or "")
        quote_ok = bool(q) and q.upper() != "NONE" and q in case["draft_reply"] and any(s in q or q in s for s in case["trigger_spans"])
    else:
        rule_ok = p["rule"] == "NONE"
        quote_ok = (p["quote"] or "").upper() in ("NONE", "")
    acceptable = p["format_ok"] and decision_ok and rule_ok and quote_ok and not hiring_claim
    return {**p, "decision_ok": decision_ok, "rule_ok": rule_ok, "quote_ok": quote_ok,
            "hiring_claim": hiring_claim, "acceptable": acceptable}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def run_eval(cases: list[dict], model: str, chat_fn, max_tokens: int = 96, warmup: bool = True) -> list[dict]:
    """Sequential, one request at a time. Only mode=='live' rows are measurements."""
    rows = []
    todo = ([("warmup", cases[0])] if (warmup and cases) else []) + [("scored", c) for c in cases]
    for kind, c in todo:
        r = chat_fn(screen_messages(c), model=model, max_tokens=max_tokens)
        u = r.get("usage") or {}
        s = score(c, r.get("text") or "")
        rows.append({
            "case_id": c["case_id"], "scored": kind == "scored", "model": model, "mode": r.get("mode"), "label": c["label"],
            **{k: s[k] for k in ("decision", "rule", "quote", "format_ok", "decision_ok", "rule_ok", "quote_ok", "hiring_claim", "acceptable")},
            "latency_ms": r.get("latency_ms"), "generation_ms": (u.get("civicdesk") or {}).get("generation_ms"),
            "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
            "finish_reason": r.get("finish_reason"), "usage_source": r.get("usage_source"),
            "error": r.get("error"), "reply": r.get("text"),
        })
    return rows


def aggregate(rows: list[dict]) -> dict:
    """Accuracy, latency and per-request tokens use scored live rows only.
    attempt_* totals include the warm-up and any retries, for cost."""
    attempts = [r for r in rows if r["mode"] == "live"]
    rows_all = rows
    rows = [r for r in rows if r.get("scored", True)]
    live = [r for r in rows if r["mode"] == "live"]
    n = len(live)
    acc = sum(r["acceptable"] for r in live)
    dec = sum(r["decision_ok"] for r in live)
    blk = [r for r in live if r["label"] == "BLOCK"]
    gos = [r for r in live if r["label"] == "GO"]
    have_tok = [r for r in live if r["prompt_tokens"] is not None and r["completion_tokens"] is not None]
    lat = [r["latency_ms"] for r in live if r["latency_ms"] is not None]
    gen = [r["generation_ms"] for r in live if r["generation_ms"] is not None]
    return {
        "rows_total": len(rows), "rows_live": n, "rows_not_measured": len(rows) - n,
        "decision_correct": dec, "acceptable": acc,
        "block_cases": len(blk), "blocked_correctly": sum(r["decision"] == "BLOCK" for r in blk),
        "go_cases": len(gos), "wrongly_blocked": sum(r["decision"] == "BLOCK" for r in gos),
        "format_followed": sum(r["format_ok"] for r in live),
        "acceptable_rate": acc / n if n else None, "acceptable_rate_95ci": wilson(acc, n),
        "input_tokens_total": sum(r["prompt_tokens"] for r in have_tok) if have_tok else None,
        "output_tokens_total": sum(r["completion_tokens"] for r in have_tok) if have_tok else None,
        "input_tokens_mean": statistics.mean(r["prompt_tokens"] for r in have_tok) if have_tok else None,
        "output_tokens_mean": statistics.mean(r["completion_tokens"] for r in have_tok) if have_tok else None,
        "rows_without_usage": n - len(have_tok),
        "latency_ms_median": statistics.median(lat) if lat else None,
        "generation_s_total": sum(gen) / 1000 if gen else None,
        "truncated": sum(r["finish_reason"] == "length" for r in live),
        "errors": sum(bool(r["error"]) for r in rows_all),
        "attempts_live": len(attempts),
        "attempt_input_tokens_total": sum(r["prompt_tokens"] or 0 for r in attempts),
        "attempt_output_tokens_total": sum(r["completion_tokens"] or 0 for r in attempts),
        "attempt_generation_s_total": sum(r["generation_ms"] or 0 for r in attempts) / 1000,
        "attempts_without_usage": sum(r["prompt_tokens"] is None for r in attempts),
    }


def api_cost(input_tokens: int, output_tokens: int, in_rate_per_m: float, out_rate_per_m: float) -> float:
    return input_tokens * in_rate_per_m / 1e6 + output_tokens * out_rate_per_m / 1e6


def compute_cost(hours: float, hourly_rate: float, share: float = 1.0) -> float:
    return hours * hourly_rate * share


def cost_per_acceptable(cost: float | None, acceptable: int) -> float | None:
    """None means undefined: no acceptable answers (or no cost figure). Never 0, never divide by zero."""
    if cost is None or acceptable == 0:
        return None
    return cost / acceptable


def write_scorecard(rows: list[dict], summary: dict, stem: Path) -> tuple[Path, Path]:
    csv_path, json_path = stem.with_suffix(".csv"), stem.with_suffix(".json")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    json_path.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    return csv_path, json_path
```

## Appendix E: new `civicdesk_remote.py` (tested with fake keys only: requests reach each provider, are refused, and the key never appears in the result)

```python
"""Optional hosted-API comparison for T1-03. Fictional CivicDesk data only.

Keys come from an environment variable or a masked getpass prompt, live only in this
process, and are never printed, saved, logged or written to notebook output.
"""

from __future__ import annotations

import getpass
import json
import os
import time
import urllib.error
import urllib.request

# Checked against each provider's own docs on 2026-11-12. Re-check before class.
PROVIDERS = {
    "google": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "key_env": "GEMINI_API_KEY",
               "default_model": "gemini-3.5-flash-lite", "model_kind": "proprietary (Google Gemini)"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY",
             "default_model": "openai/gpt-oss-20b", "model_kind": "open-weight model hosted by Groq"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY",
                   "default_model": "google/gemma-4-26b-a4b-it:free",
                   "model_kind": "open-weight model; the serving provider is chosen by OpenRouter unless pinned"},
}

_KEYS: dict[str, str] = {}


def set_key(provider: str) -> str:
    """Read the key from the environment, else ask with a masked prompt. Returns a status line only."""
    env = PROVIDERS[provider]["key_env"]
    k = os.environ.get(env, "").strip()
    if not k:
        k = getpass.getpass(f"Paste your {provider} key (hidden, not saved): ").strip()
    if not k:
        return f"{provider}: no key set, remote comparison skipped"
    _KEYS[provider] = k
    return f"{provider}: key set for this session only ({env} or hidden prompt)"


def forget_keys() -> None:
    _KEYS.clear()


def _redact(text: str) -> str:
    for k in _KEYS.values():
        if k:
            text = text.replace(k, "[key removed]")
    return text


def remote_chat(provider: str, messages: list[dict], model: str | None = None, max_tokens: int = 96,
                extra_body: dict | None = None, timeout: float = 60.0, model_param: str | None = None) -> dict:
    """Same return shape as civicdesk_lab.chat. mode is 'live' only for a real provider reply."""
    p = PROVIDERS[provider]
    model = model_param or model or p["default_model"]
    t0 = time.perf_counter()
    if provider not in _KEYS:
        return {"ok": False, "mode": "skipped", "model": model, "text": "", "latency_ms": 0, "usage": None,
                "usage_source": "none (no key)", "finish_reason": None, "error": "no key set", "provider": provider}
    body = {"model": model, "messages": messages, "max_tokens": int(max_tokens), "temperature": 0}
    if extra_body:
        body.update(extra_body)
    req = urllib.request.Request(p["base_url"].rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "civicdesk-t103/1.0",
                                          "Authorization": "Bearer " + _KEYS[provider]},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
        ch = payload["choices"][0]
        u = payload.get("usage") if isinstance(payload.get("usage"), dict) else None
        ok_usage = bool(u and isinstance(u.get("prompt_tokens"), int) and isinstance(u.get("completion_tokens"), int))
        return {"ok": True, "mode": "live", "model": payload.get("model") or model, "requested_model": model,
                "text": (ch.get("message") or {}).get("content") or "", "latency_ms": int((time.perf_counter() - t0) * 1000),
                "usage": u if ok_usage else None, "usage_raw": u,
                "usage_source": f"provider ({provider})" if ok_usage else "none (provider sent no usage)",
                "finish_reason": ch.get("finish_reason"), "error": None, "provider": provider}
    except urllib.error.HTTPError as e:
        detail = _redact(e.read().decode(errors="ignore")[:300])
        return {"ok": False, "mode": "error", "model": model, "text": "", "latency_ms": int((time.perf_counter() - t0) * 1000),
                "usage": None, "usage_source": "none (error)", "finish_reason": None,
                "error": f"HTTP {e.code}: {detail}", "provider": provider}
    except Exception as e:  # network, timeout, bad JSON
        return {"ok": False, "mode": "error", "model": model, "text": "", "latency_ms": int((time.perf_counter() - t0) * 1000),
                "usage": None, "usage_source": "none (error)", "finish_reason": None,
                "error": _redact(f"{type(e).__name__}: {e}"), "provider": provider}


def make_chat_fn(provider: str, model: str | None = None, extra_body: dict | None = None, pause_s: float = 0.0):
    """Adapter for civicdesk_eval.run_eval. pause_s spaces requests out to stay under free-tier limits."""
    def fn(messages, model=model, max_tokens=96):
        r = remote_chat(provider, messages, model=model, max_tokens=max_tokens, extra_body=extra_body)
        if pause_s:
            time.sleep(pause_s)
        return r
    return fn
```
