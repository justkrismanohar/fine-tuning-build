# AUX-01 Sitting beside a system you already have

**Self-taught. 45–60 minutes. No GPU. No ministry data.**

The workshop will not wire GLPI, EDMS, LMS, Active Directory, ECMS or GIS. Those integrations are a project. This note is so you can ask for the right project.

## Who this is for

- **Trade IMSD** — GLPI + AD + knowledge base.
- **Finance** — EDMS remains the record; the model is a retrieval layer.
- **Health** — LMS remains the grade book.
- **Defence** — asset register remains the source of truth.
- **MOWI** — ECMS / IKEP / GIS stay the systems of record.
- **MPSDFS** — ISEMS, when it exists.

## The rule

The language model is a **component**. It is not the system of record.

```
User → your existing app (ticket, EDMS, LMS) → orchestration
         → (optional) retrieve approved chunks
         → language-model API
         → your app writes the audit row and shows a human the draft
```

If the model is down, the ministry still has GLPI / EDMS / the LMS.

## Three integration shapes

1. **Read-only retrieve.** The model may search a copy of approved documents. It cannot write. (Finance, OPR, policy RAG.)
2. **Draft, human posts.** The model fills a ticket summary or a grade suggestion. An officer clicks. (Trade, Health, Labour.)
3. **Tool call.** The model is allowed to call one named API with an allowlist. Default is none. (Trade: create a ticket, never reset a password.)

## Exercise (on paper)

Pick *your* existing system. Write four lines:

1. What is the system of record today?
2. Would the model read, draft, or call a tool?
3. Which three API actions are forbidden even if a user asks?
4. Where does the audit row live — in the model log, or in the existing system?

## Stop

If you cannot name the system of record, you are not ready to integrate a model. Go back to the Day 1 canvas.
