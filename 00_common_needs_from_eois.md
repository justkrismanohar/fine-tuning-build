# Common needs from the ministry EOIs

Read from `materials/SLM Training` (eleven papers). Used to shape CivicDesk, the Tier 1 notebooks, and the self-taught auxiliary workshops. Training still uses **synthetic CivicDesk only**. Live applications, Cabinet papers, case files, health records, burgess PII, patrol tracks and operational feeds stay out of the room.

## The eleven papers in one line

| Org | Submitted problem (type) | What they actually need the model to do |
|---|---|---|
| Labour (MOLSED) | Recruitment screening | Match text to **published criteria**, **quote evidence**, flag **human review**; never hire |
| Trade IMSD | ICT support agent | Conversational **triage**, **RAG** over approved KB, **ticket hand-off**, **no privileged tools** |
| Finance | Cabinet Minutes/Notes in EDMS | Meaning search + **summary + citations**; **keep EDMS access rules** |
| Health | LMS grading; suicide-guideline check | Score against a **rubric/matrix**, show **criterion evidence**; administrator **validates**; sensitive content |
| Defence | IT asset query; OPR procurement advisor | **Structured query** over a register; **RAG with citations** to OPR sources; no award |
| MPSDFS | Case summarisation; policy/circular retrieval | **Extract/summarise** (PII-heavy); **RAG** over approved policy |
| THA (Health & Wellness) | Tobago Public Health Observatory | Cross-source **retrieval, classification, summary**; health-data **custody** |
| RDLG | Minutes, resolutions, service requests, burgess applications | **Search/summary** of institutional records; **PII** in service requests |
| CPO / PD | Judgments, decisions, precedents; agentic market-research | **On-prem** model; domain knowledge; **agentic** collection — high control |
| TTDF / Coast Guard | Maritime surveillance / interdiction support | Pattern support from **operational** sources; **strict data custody** |
| MOWI | Project/GIS; ECMS knowledge; reporting | **Classify, retrieve, summarise, report**; existing platforms |

## What repeats (the training problems)

The systems differ. The training problems underneath are few. CivicDesk is one fictional package that rehearses these types.

### N1 — Criteria matching with a quoted evidence span

Match incoming text against a published rule and show the sentence that justified the label.

- **Labour:** vacancy mandatory/desirable criteria vs a CV.
- **Health:** marking rubric vs an assignment; suicide-reporting matrix vs a draft (advisory only).
- **Defence (OPR):** thresholds, method, approvals vs a procurement question.
- CivicDesk stand-in: classify a service request against a published handbook paragraph and extract a quote.

### N2 — Human review; the model does not decide

Where text is incomplete, ambiguous, or the act is consequential, the label is **Human review required**. The model never hires, grades, awards a contract, issues a licence, publishes a mark, or deploys an asset.

- Named in Labour, Health, Trade, Defence procurement, CPO.
- Implicit in every other paper (officer remains accountable).

### N3 — Retrieval from an *approved* corpus, with citations (or refusal)

Natural-language question → retrieve the governing paragraph → cite it → or abstain if it is not there.

- Finance EDMS; Defence OPR handbooks; MPSDFS policies/circulars; MOWI ECMS; Health guidelines; Trade IMSD knowledge base; RDLG minutes/resolutions; THA observatory sources.

### N4 — Retrieval is not authorisation

A hit in the index does not mean this user may see that paragraph.

- Finance (Cabinet access); Defence assets; MPSDFS case files; THA health; RDLG burgess files.

### N5 — PII, sensitive and operational data stay out of the classroom (and usually out of the model)

Names, IDs, health, income, CVs, Cabinet text, patrol tracks, burgess applications.

- Heavy in Labour, Health, MPSDFS, THA, RDLG, TTDF.
- Trade: tickets and device identifiers.
- Course rule: CivicDesk only; planted canaries must be refused or stripped.

### N6 — Bounded agency (tools the model must never call)

Conversational assistance is not a licence to reset a password, grant AD rights, approve spend, create an unchecked GLPI change, or scrape the open web for negotiation inputs.

- Trade IMSD (explicit allowlist / escalation matrix).
- CPO (agentic market-research workflows).
- Defence procurement (must not award).

### N7 — Government-controlled inference when the work is core

On-prem or Ministry VPC; data does not leave on a public API.

- Stated by CPO, TTDF, Finance, THA.
- Implied wherever PII or Cabinet/ops data is in play.

### N8 — Summarise and extract from long records

Case notes, minutes, project files, Cabinet packs, health reports.

- MPSDFS, RDLG, MOWI, Finance, THA.

### N9 — Classify incoming text

Ticket category, document type, request type, “in/out of scope.”

- Trade triage; MOWI ECMS classification; THA; CivicDesk request type.

### N10 — Structured query over a register (language as the interface, not the source of truth)

“Which licences expire this month?” only works if the **register** is authoritative. The model is a query layer.

- Defence IT assets; Trade GLPI status; MOWI project/GIS fields.

### N11 — Cost, GPU, burst vs standing

Who pays, laptop vs Ministry VM vs MEA Azure vs hosted API; fine-tune is a short burst; serving is standing inference; VRAM is not interchangeable.

- All ministries will be asked to buy or rent something. CPO/TTDF/Finance need this to argue for owned compute.

### N12 — Open source vs open weight vs a closed API

Can you see training data? Weights? What does the licence allow?

- Programme theme. Material for CPO (on-prem), anyone comparing ChatGPT to OLMo/Phi.

### N13 — Fit beside a system that already exists

GLPI + AD (Trade), EDMS (Finance), LMS (Health), asset DB (Defence), ISEMS (MPSDFS), ECMS/IKEP/GIS (MOWI). The workshop will not wire those systems.

### N14 — Audit: recommendation, override, who signed

Labour screening trail; Health grade accept/adjust; Trade ticket completeness.

### N15 — Pattern-finding on operational / tabular / geospatial data

TTDF routes, weather, radar; MOWI GIS/project risk. **This is often not a language-model job.** Teach when to stop and use a different method.

## Four learning-need clusters (how the room is grouped)

| Cluster | Needs | Ministries (type of problem) |
|---|---|---|
| A Criteria | N1, N2, N14 | Labour; Health grading / guideline check |
| B Retrieval | N3, N4, N8 | Finance; Defence OPR; MPSDFS policy; MOWI ECMS; Health guidelines; RDLG minutes; THA |
| C Service desk | N9, N3, N6, N13 | Trade IMSD; Defence assets as a query layer |
| D Local control | N5, N7, N6 | CPO; TTDF; THA; Finance; any PII-heavy paper |

A singleton sits with the nearest cluster for group work.

## What we will *not* do in the six days

- Ingest real ministry records.
- Connect GLPI, EDMS, LMS, AD, GIS, or a WhatsApp channel.
- Train a foundation model, or fine-tune on judgments / case law.
- Run maritime prediction, GIS risk models, or statistical-validation agents.
- Produce a ministry budget, a DPIA, or a go-live plan.

Those sit in the auxiliary (self-taught) workshops, or in a later GoRTT project under a separate approval.
