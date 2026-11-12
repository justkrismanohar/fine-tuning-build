# AUX-03 Identity is not a chat message

**Self-taught. 30 minutes. No GPU.**

## Who this is for

- **Trade IMSD** (email + staff ID on WhatsApp is identification, not authentication).
- **Finance** (Cabinet access is a directory decision).
- **Defence assets, MPSDFS, THA, RDLG.**

## Two different questions

1. **Who do they claim to be?** Name, email, staff number. Easy to type. Easy to fake in a chat.
2. **Have they proved it?** SSO, MFA, a session issued by AD. That proof lives *outside* the model.

The model must never be the identity provider. It receives a verified user id from the orchestration layer, or it sees a public FAQ only.

## Day 2 link

T1-10 (access and governance) is the classroom version: a retrieved paragraph the fictional user is not allowed to see. Vector similarity is not authorisation.

## Exercise

Write the rule for your desk:

- Channel (email, portal, chat, walk-in).
- What is required before the model may mention *this user’s* ticket, asset, or case.
- What the model may still answer with zero identity (public SOP).

## Stop

Do not put passwords, MFA codes or recovery phrases in a prompt. If a user pastes one, the run is a fail for that exercise — same as in class.
