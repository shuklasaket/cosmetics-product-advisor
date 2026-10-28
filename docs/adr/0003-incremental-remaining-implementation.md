# ADR-0003: Extend the existing app incrementally

**Status:** Proposed

**Date:** 28 October 2026

**Decider:** Repository maintainer

## Context

PRD 01 has a runnable sourced catalog, request validation, SQLite evidence storage,
and a search/detail UI. The first PRD 02 story added approved-source and refresh-result
contracts. PRDs 02–09 still require live refresh, screening, reviews, ranking,
explanations, conversation, preference memory, and evaluation. Building every future
abstraction now would add interfaces and persistent state before their behavior can be
verified. Existing implemented contracts must remain stable.

## Decision

Extend one local Streamlit application and one SQLite database in PRD order. Each
release adds its UI, the smallest service or adapter it uses, and its acceptance
evidence. Keep the structured form as a direct caller of shared Python services.
Introduce a single local Ollama adapter with Review Evidence in PRD 04; reuse it for
Explanation and Citation in PRD 06. PRD 07 composes exactly five fixed roles through
the trusted controller defined in [ADR-0004](0004-bounded-five-role-orchestration.md).
It may ask for clarification and route known failure states, but does not let a model
select arbitrary tools or change deterministic eligibility, scoring, or evidence rules.
Store personal requests in session only.

Use the approved registry and existing import/evidence storage for PRD 02. Keep rule
and review datasets small, sourced, and versioned. Cache only validated public
extractions. Add a single allowlisted local preference record in PRD 08. PRD 09
aggregates redacted usage events already captured at model-call time. Hosted inference
and its paid ledger remain disabled optional extensions; they cannot be prerequisites
for the local demonstration.

## Alternatives considered

| Option | Benefit | Cost or risk |
| --- | --- | --- |
| Build all future layers and a general tool platform now | Early interfaces appear complete | Duplicates paths before evidence and behavior are known; larger migration and privacy surface |
| Separate services or autonomous agents | More deployment isolation | Adds processes, coordination, and failure modes to a single-user local app |
| Incremental shared services and a later bounded role graph | Each PRD stays runnable and testable; preserves current boundaries | Shared role contracts need deliberate versioning as later consumers arrive |

## Consequences

- Existing PRD 01 and source-contract behavior is untouched by this decision.
- PRD 03 and 04 can proceed independently after coordinating evidence IDs and
  repository changes; Policy and Ranking waits for their published outcomes.
- The form and conversation must produce identical deterministic eligibility and
  numeric ranking for identical validated requests and evidence versions.
- A future need for multi-user access, hosted inference, or scheduled collection
  requires a separate decision and privacy/source review.
- This proposal becomes accepted only after maintainer review; a diagram or PRD edit
  alone does not approve implementation details or numerical defaults.

## References

- [PRD index and remaining path](../requirements/README.md#delivery-baseline-and-remaining-path)
- [Technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md)
- [Architecture diagram](../architecture/cosmetic-advisor-architecture.drawio)
