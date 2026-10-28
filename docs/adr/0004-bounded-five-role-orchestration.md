# ADR-0004: Use a bounded five-role workflow under one trusted controller

**Status:** Proposed

**Date:** 28 October 2026

**Decider:** Repository maintainer

**Supersedes:** the single-specialist-function workflow portions of
[ADR-0001](0001-local-modular-architecture.md) and
[ADR-0003](0003-incremental-remaining-implementation.md)

## Context

The remaining product increments need distinct responsibility boundaries for request
collection, evidence access, review analysis, deterministic policy/ranking, and
grounded explanation. The prior plan described one graph over shared services and
explicitly deferred independent agents. The maintainer requested a small-agent design,
with no more than five agents, across the remaining work.

The product is still one local, single-user Streamlit application with one SQLite
database. It must preserve deterministic eligibility/ranking, evidence provenance,
session-only sensitive inputs, bounded local inference, cancellation, and reproducible
evaluation. Adding an open-ended swarm or separate runtimes would widen the privacy,
cost, and failure surface without helping this 20–30-product catalog.

## Decision

Use one trusted LangGraph controller and exactly five fixed specialist roles:

| Role | Introduced / composed | Inputs and authority |
| --- | --- | --- |
| Intake and Clarification | PRD 07 | Uses local-model extraction only to propose `UserRequirements` or a clarification. It has no tools. |
| Catalog Evidence | PRD 02, composed in PRD 07 | Calls approved search/detail and source adapters only. It returns typed facts, provenance, freshness, and limitations. |
| Review Evidence | PRD 04, composed in PRD 07 | Calls the bounded review-model adapter only over permitted review evidence, then returns a candidate typed analysis. |
| Policy and Ranking | PRDs 03 and 05, composed in PRD 07 | Uses Python-only screening, hard filters, and scoring over validated immutable snapshots. It makes no model call. |
| Explanation and Citation | PRD 06, composed in PRD 07 | Calls the bounded explanation-model adapter only with selected facts and an evidence manifest, then returns candidate claims. |

The controller owns the `RunContext`, capability grants, role order, minimum-necessary
views, counters, deadlines, optional budget reservations, cancellation, redaction,
persistence, validation, and publication. It invokes the roles in the fixed sequence
shown in the architecture diagrams. Empty, unavailable, failed, cancellation, and
clarification branches are explicit controller transitions, not role-selected routes.

Every handoff is a versioned `RoleInvocation`/`RoleResult` schema. A role cannot call
another role, choose a tool, access SQLite/shell/arbitrary HTTP, save preferences,
publish a result, persist state, or relax an earlier deterministic outcome. The
controller validates schema and evidence before the next handoff. Preferences stay a
separate controller-confirmed operation, not a sixth role.

This is a bounded role workflow, not a swarm or a set of independent autonomous
agents. There are no subgraphs created from model output, role-to-role messages,
general tool registries, durable raw checkpoints, or new services/processes.

## Alternatives considered

| Option | Benefit | Cost or risk |
| --- | --- | --- |
| One controller over anonymous functions | Smallest orchestration surface | Responsibility, least-privilege inputs, and usage attribution are less explicit. |
| Five fixed roles under one controller (selected) | Clear responsibility and testable typed handoffs while retaining one state/authority owner | Requires role contracts and capability tests. |
| Independent or dynamic agents | Flexible delegation or parallel reasoning | Conflicting state, broader permissions, unpredictable cost, harder privacy guarantees, and no demonstrated value for the bounded catalog. |

## Consequences

**Benefits**

- Each remaining PRD has a stable role boundary and a direct-call path before PRD 07
  composes the roles.
- Only the two evidence-interpretation roles may call the local model; deterministic
  screening/ranking remains independently testable.
- Role/protocol versions make redacted usage reporting and replay evaluation more
  diagnosable without recording sensitive inputs.
- The controller can reliably suppress stale/cancelled results and centrally apply all
  call, token, deadline, and budget limits.

**Costs and limitations**

- The roles are sequential and do not add parallelism or separate deployment scaling.
- Extra schemas and contract tests are required before composition.
- The five-role limit is intentional. Adding a role requires a new ADR and PRD/story
  traceability update rather than silently expanding the graph.

## Rollout and verification

1. Publish typed role/protocol contracts and capability tests with the first affected
   role increment; preserve existing direct service callers.
2. Add Review Evidence, Policy and Ranking, and Explanation and Citation using the
   corresponding PRD acceptance evidence and redacted events.
3. In PRD 07, wire only the five named roles through the controller and test denied
   capabilities, invalid handoffs, structured/conversational parity, limits,
   cancellation, and stale-result suppression.
4. In PRDs 08–09, verify preference isolation plus role-attributed, redacted usage and
   replay exports. Do not mark this decision implemented until those increments merge.

## References

- [PRD index](../requirements/README.md)
- [Technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md)
- [PRD 07 workflow](../requirements/07-conversational-workflow.md)
- [Architecture guide](../architecture/README.md)
