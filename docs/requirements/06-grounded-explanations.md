# PRD 06 — Source-Grounded Recommendation Explanations

Status: Draft · Dependencies: [PRD 04](04-review-analysis.md), [PRD 05](05-ranking-and-comparison.md) · Source: report §§8, 15, 17–18

## Problem and outcome

A shortlist alone leaves shoppers unsure why a product was chosen or what its evidence cannot establish. They need a readable explanation that preserves the deterministic selection and points back to supporting facts.

**Minimum deployable increment:** an AI explanation on each existing recommendation card, including reasons, drawbacks, ingredient limitations, and source links; factual cards remain usable if generation fails.

**Smallest delivery path:** let the local model choose from a small, typed vocabulary of
reason and drawback claims tied to selected evidence IDs. Render approved wording and
immutable product facts in Python. If the model cannot return verifiable choices,
display the factual explanation from the same evidence. This keeps an AI explanation
without requiring a general free-form claim verifier.

## Goals and scope

- Validate every displayed generated factual claim against supplied evidence references.
- Keep selected product IDs, order, scores, prices, and screening outcomes unchanged.
- Explain uncertainty and observed drawbacks for every recommended product where evidence exists.

Use the local model and validated evidence already available. Exclude fresh web research during explanation, new product selection, clinical advice, generated customer testimonials, and inference of absent facts.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| EXP-01 | Give the model only the selected IDs/order, immutable score facts, validated review findings, ingredient statuses, relevant preference attributes, and an evidence manifest. Raw reviews, arbitrary pages, and unrelated conversation history are unnecessary for this step. |
| EXP-02 | Require structured output per selected product: reasons for fit, supported benefits, drawbacks, ingredient considerations, missing information, and evidence IDs for each factual claim. Missing drawback evidence is disclosed as unavailable; the model cannot invent balance. |
| EXP-03 | Render product IDs, rank, price, dates, score, and screening status directly from validated application data. Reject responses referring to unselected products, altered facts, unknown evidence IDs, or contradictory conclusions. No explanation can override a hard filter. |
| EXP-04 | Use bounded claim types: product claim, review observation, screening finding, or comparative score fact. Validate a generated claim's referenced evidence type and content; omit claims that cannot be checked, rather than trusting a citation ID alone. Approved facts may use constrained templates when free-form wording is not reliably verifiable. |
| EXP-05 | Resolve claim citations through the evidence manifest to original sources and dates. Ingredient restrictions link to exact rule references; review findings link to their sample and count. Label manufacturer claims and customer observations as such. Every card includes screening-coverage and uncertainty limitations. |
| EXP-06 | Keep sourced content untrusted and restrict explanation generation from tool execution. Instructions embedded in names, product descriptions, or review summaries cannot change the output contract. Reject diagnosis, treatment recommendations, and guaranteed safety/efficacy/compliance language. |
| EXP-07 | Allow a proposed maximum of two generation calls including one validation repair, with a 1,500-output-token limit per call for the full shortlist. On timeout, invalid output, or exhausted limits, show a deterministic explanation from validated facts and label the AI explanation unavailable. Log model, usage status, duration, and validation outcome without raw sensitive prompts. |

## Release verification

Generate explanations for a normal three-product shortlist and a one-product shortlist. Follow each displayed citation to its actual supporting fact. Check that a mixed review remains mixed, a manufacturer claim remains a claim, and missing review data produces an explicit limitation.

Use fixtures with a fabricated citation ID, a real citation attached to an unrelated claim, an altered price, an extra product, embedded hostile instructions, and an unavailable model. Each failure must produce removal/rejection or the factual fallback; recommendation identity/order and hard constraints remain unchanged.

## Success measures

- 100% of displayed factual explanation claims have resolvable, matching evidence in acceptance fixtures.
- Zero changes to deterministic selection, ranking, or screening caused by generation.
- 100% of generation-failure scenarios retain useful factual cards and a visible generation status.

## Dependencies and decisions

Engineering/product define a small claim vocabulary and validation fixtures before release. The release may use constrained phrasing throughout if that is what the selected local model can support reliably. A hosted model is not a prerequisite.
