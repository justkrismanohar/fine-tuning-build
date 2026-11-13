# From stop rule to safe rollout (optional, T1-05)

Fictional CivicDesk résumé redaction. Classroom guidance, not a release procedure.

## Three different jobs

- **Per-document hold.** Checks run on every output. If one fires (residual email or phone, a name from the application form, an ID pattern, empty or much shorter output, timeout, out-of-scope input), that document is held and routed to the authorised verifier. It is not released. This protects that one document, and only against what the checks can see.
- **Sampled audit.** A person checks a random sample of outputs that passed the checks. This estimates how often misses happen across the batch. It does not protect the documents nobody looked at, and it does not authorise sending any of them outside the approved environment.
- **Service pause.** Stop the whole run when the batch looks wrong: an audit finds a leak above your threshold, holds jump, outputs come back malformed or empty in a burst, inputs change (new layout, language, scans), or the model, prompt or check version changed without a new measurement. Contain (stop sending), escalate to the owner, roll back to the last known-safe version or the manual process, reassess, and re-measure before restarting.

## What the numbers can and cannot say

- Zero failures in a small sample is not zero risk. With 40 random audits and no failures, the true miss rate could still be about 7% (one-sided 95% bound). With 300, about 1%. The bound holds only for documents like the ones sampled.
- Checks have false alarms and misses. A second detector or a second model is not automatically better; they often miss the same things.
- Confidence from generated-token probabilities is not confidence that a span is PII. Route on what the checks find and on document risk (new layout, unusual language, high-sensitivity role), not on the model sounding sure.

## Human capacity

You cannot review everything. Size the review queue from the measured hold rate and the audit sample. If the queue backs up, documents wait in the approved environment, or the work falls back to the manual process. They are never released unreviewed to clear the queue.

## Safe rollout, in stages

1. **Offline, synthetic:** the frozen benchmark, in the authorised environment.
2. **Shadow:** real inputs, outputs stored but sent to nobody new. Compare against the manual process.
3. **Canary:** one versioned model + prompt + checks, a small share of work, outputs only to staff already authorised to see the originals. No automatic external or public release of unreviewed redactions.
4. Before each stage: a written baseline, monitoring, stop thresholds, an accountable owner who decides, and a tested rollback to the known-safe manual workflow.

A canary limits how many people one bad version can reach. It is not proof of privacy. Rollback stops future harm; it cannot un-disclose a CV that already leaked.

## Logs

Keep raw CVs and redacted outputs out of broad logs. Log versions (model, prompt, checks, data), counts, check names that fired and decisions. In this course everything is synthetic.
