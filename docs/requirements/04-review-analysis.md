# PRD 04 — Evidence-Backed Customer Review Analysis

Status: Draft · Dependencies: [PRD 01](01-catalog-and-search.md) · Source: report §§2, 4–5, 13, 15–17

## Problem and outcome

An average rating hides recurring complaints, limited coverage, and feedback relevant to a skin type. Shoppers need a concise summary that can be checked against genuine review evidence.

**Minimum deployable increment:** a review-analysis tab on product details that runs a compatible local Ollama model over permitted review samples and displays validated findings and coverage.

## Goals and scope

- Link every displayed benefit/complaint to the review evidence supporting it.
- Distinguish a source's total review count from collected, deduplicated, analyzed, and explicitly skin-type-relevant counts.
- Complete local analysis within declared context/call bounds and expose honest failure states.

Include genuine, attributed review imports and one local model. Do not claim fake-review detection, infer reviewer skin type from sentiment, collect reviewer profiles, or depend on a live retailer scraper.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| REV-01 | Import permitted reviews with product/variant ID, stable review ID, source URL/reference, collection date, allowed excerpt/text, rating if present, and explicitly supplied skin-type metadata. Keep source aggregate rating/count distinct from the sample. Strip reviewer identifiers unnecessary for analysis. |
| REV-02 | Validate review-product mapping and remove exact duplicates before analysis. Flag near-duplicate patterns as a confidence limitation without declaring fraud. Report collected, unique, analyzed, and failed/unprocessed counts consistently. |
| REV-03 | Connect to a locally configured Ollama model selected for the target MacBook. Document installation, model configuration, and health check. A missing/unavailable model leaves raw sourced review evidence viewable and shows analysis unavailable. |
| REV-04 | Analyze batches sized to context capacity; proposed initial limits are 20 reviews per batch, 60 unique reviews per product, six model calls per product including validation retries, and 1,000 output tokens per call. Use deterministic sampling and record exclusions/truncation. Capture model, tokens where available, duration, and outcome from the first release. |
| REV-05 | Validate structured sentiment, positive/negative aspects, explicit skin-type mentions, and supporting review IDs with Pydantic. Reject unknown evidence IDs or unsupported claims. Allow at most one repair attempt within the call cap; persistent invalid output produces unavailable/partial analysis rather than invented findings. |
| REV-06 | Aggregate validated findings in Python. Display recurring aspects only when supported by at least two unique analyzed reviews; label single-review observations individually. Proposed confidence bands: low for fewer than 10 unique analyzed reviews; medium for 10–29; high for 30+; downgrade one band for a flagged repetitive sample. Always show coverage and missing-data limits alongside the band. |
| REV-07 | Show an overall summary and feedback explicitly relevant to the selected skin type. Link findings to review sources and counts; absent explicit skin-type evidence produces “not established.” Empty reviews and missing ratings stay unknown, never neutral/positive sentiment. |
| REV-08 | Treat all reviews as untrusted data. Embedded instructions cannot change tools, eligibility, ranking, or model settings. Cache validated per-review/batch extraction by evidence hash, model, prompt, and schema versions; derive user-specific views in session so exclusions and raw user text are not persisted. |

## Release verification

Launch the updated app, open a genuine sourced review sample, and run local analysis. Check a recurring benefit, a recurring complaint, a single observation, and an explicit skin-type mention against their evidence IDs. Repeating an unchanged analysis should reuse a valid cache entry; changing evidence/model/prompt invalidates it.

Exercise duplicate text, no reviews, mixed sentiment, a malformed model response, an unavailable Ollama service, and an instruction embedded inside a review. Confirm count reconciliation, bounded calls, honest partial results, and unchanged application controls.

## Success measures

- 100% of displayed findings resolve to existing supporting review IDs.
- Duplicate reviews add zero weight to recurring-aspect counts.
- 100% of model calls have a run/product reference, duration, and usage status; unavailable token counts are labeled unknown.

## Dependencies and decisions

Data/operator confirms permitted review access and a proposed minimum of five genuine reviews for at least four catalog products; sparse products may remain sparse. Engineering selects and smoke-tests the model on the target machine before release. Confidence bands are proposed coverage heuristics, not probabilities of truth; their counts and limitations remain visible.
