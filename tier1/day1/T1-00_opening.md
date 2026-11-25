# T1-00 Opening — 09:00–09:15

Facilitator reads this. Projector can show the data ban. No slides.

People who had never used a notebook were pointed at `course/prep/` (Google Colab, no Python) before the week. Do not re-run that prep in this 15-minute opening.

## Safe use (say out loud)

1. This is training. It is not a pilot and not approval to connect Cabinet, GLPI, LMS, GIS, or a patrol system.
2. **CivicDesk only.** If it came from work, it does not go in a notebook.
3. The model does not hire, grade, award a contract, issue a licence, reset a password, or deploy an asset.
4. Mixed tables. No-code people run cells. Occasional-code people change marked lines. Deep-code people do not drive someone else’s notebook.
5. Last block of the day is group work. Download at 14:55.

## Pre-test (paper or this form — not graded as a barrier)

Circle one.

1. A language model produces the next token using: luck / frozen or adapted **weights** / the ministry database.
2. If ChatGPT answers a Cabinet question, the minute lived in: the model’s training data for sure / maybe not; you cannot inspect it / your EDMS.
3. Open-weight means: free of charge / you can download and run the weights / you can see the training data.
4. Name one thing that must never be pasted today: ________________.

Collect. Seating from the readiness survey still stands.

## Hosted image (facilitator only)

The entrypoint copies `/opt/civicdesk` into `/civicdesk` only when `tier1/day1/civicdesk_lab.py` is missing. An old bind-mounted volume keeps the previous helper and `hf_openai_server.py`. For the click-a-link hosted image that is fine. If a local Docker run still shows the old tokenizer stand-in or ignores temperature, the mount is stale: update the checkout or run without `-v`.
