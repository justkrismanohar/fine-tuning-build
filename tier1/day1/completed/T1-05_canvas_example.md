# Example canvas (loaded from reference)

Fictional CivicDesk Central Registry team. Not a ministry filing.

- Organisation: CivicDesk Central Registry (example)
- Cluster: A criteria
- Problem in one line: Officers screen fictional service applications against a published three-criterion handbook and must quote the span; unclear files go to a person.
- Owner (role): Registry supervisor
- Domain verifier (role): Handbook owner in Policy
- Current non-AI baseline: Officer reads each form against a paper checklist, ~8 minutes each
- Success measure: On a 20-item held-out set, label agrees with the verifier and a quote is present; “Human review required” when C2 is equivalent-not-identical
- Error cost: A false “Meets” that skips human review
- Data that must stay out: Real names, IDs, CVs, live EDMS
- Preferred intervention guess: unsure — probably prompt or RAG, not fine-tune
- Stop condition: Model must not recommend granting the service
- One cost question: Standing inference on a Ministry VM vs leaving a GPU up overnight
- Next question for your organisation: Is CivicDesk-style screening enough to brief HR, or is a later project required?

If you loaded this file, write “loaded from reference” on your own canvas and replace every line with your cluster’s type.
