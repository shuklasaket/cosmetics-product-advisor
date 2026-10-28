# ADR-0001: Adopt a Local Modular Architecture with Controlled AI

**Status:** Proposed

**Date:** 17 October 2026

**Deciders:** Project owner and engineering maintainer; approval not recorded

**Scope:** MVP architecture across PRDs 01–09

## Context

The advisor must compare sunscreen and moisturiser available in India using a verified catalog of approximately 20–30 products. Every recommendation needs traceable evidence, deterministic hard-constraint checks, and an explanation of missing information. Each PRD must deliver a runnable, testable increment.

The deployment target is one MacBook and one local user. Live sources may fail or provide incomplete data. Local model capacity is not yet benchmarked, and hosted inference is optional within the proposed API budget. Sensitive user inputs must remain session-only; the product must demonstrate limited opt-in memory and inspectable tool/model execution.

The [technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md) and [architecture diagram](../architecture/cosmetic-advisor-architecture.drawio) already describe a draft baseline. This record explains that design choice; it does not claim acceptance, implementation, or measured performance.

## Decision drivers

- Deliver the nine small releases without requiring public infrastructure or paid inference.
- Make eligibility, ranking, provenance, and failure behavior independently testable.
- Support clarification, conditional tool use, cancellation, and bounded execution.
- Keep personal exclusions, budgets, and raw conversations out of persistent storage and exports.
- Preserve usable sourced facts when retrieval or model generation fails.

## Decision

Adopt a **local modular monolith**: one Python/Streamlit application with separate controllers, schemas, application services, adapters, and repositories. Ollama runs as the local inference backend; it is separate from the application process. Approved external sources remain behind validated adapters.

| Area | Selected approach and rationale |
| --- | --- |
| UI and deployment | Local Streamlit interface bound to loopback. This fits the single-user deployment boundary and makes each release directly usable. |
| Workflow | Direct service calls for early releases; one typed LangGraph orchestrator from PRD 07. Form and conversation reuse the same services and validation. |
| Decision authority | Python/Pydantic own validation, ingredient findings, hard filters, scores, and evidence checks. Models interpret requests, extract review findings, and phrase supported evidence. |
| Persistence | SQLite behind repositories, with transactions, migrations, and versioned field-level evidence. Store validated public-evidence artifacts and redacted events alongside the catalog. |
| Research | Verified local catalog plus approved refresh and permitted manual imports. Preserve provenance, conflicts, and freshness; stale or unresolved critical evidence cannot qualify a recommendation. |
| Inference | Ollama first, with bounded structured outputs, cache keys, usage capture, and factual fallback. Exact model and package versions remain implementation decisions requiring validation. |
| Memory | In-memory sensitive session state; persist only reviewed, opted-in currency, country, and product finish. Disable durable raw conversation/graph checkpoints. |
| Tools | Typed, allowlisted Python functions. Models receive no unrestricted HTTP, database, shell, or preference-write access. MCP serving and independent agents remain deferred. |

Apply controls when each capability first appears. Every nested call, retry, and repair shares the run's limits; cancellation or a newer request prevents stale results from being published. Eligibility precedes scoring, and generated text cannot change selected IDs, scores, or screening outcomes.

Hosted inference remains disabled by default. Enabling it requires a configured provider/task policy, sanitized payloads, dated rates, and budget preflight. It is an extension to this baseline, not an implicit fallback.

## Options considered

| Dimension | A — Local modular app + controlled graph (selected) | B — Local procedural workflow only | C — Multiple independent agents |
| --- | --- | --- | --- |
| Complexity | Separate reusable services plus explicit graph/state contracts | Fewest initial orchestration abstractions; branching/recovery written directly | Additional coordination, handoffs, state ownership, and validation boundaries |
| Cost | Local inference by default; bounded optional paid calls | Same inference choices; potentially less framework work initially | More potential model/tool calls; actual cost depends on execution policy |
| Scalability | Fits the local MVP; modules can later be extracted | Also fits this catalog; workflow changes require explicit control-flow maintenance | Can distribute independent work, but requires concurrency and consistency controls |
| Team familiarity | Not assessed; validate Streamlit/LangGraph during implementation | Not assessed; avoids a graph framework to learn | Not assessed; requires an additional coordination model |

**A — Benefits:** shared behavior across form/chat, visible conditional execution, and isolated deterministic policies. **Costs:** graph integration and adapter/version maintenance; local hardware constrains inference.

**B — Benefits:** straightforward early releases and fewer dependencies. **Costs:** follow-up loops, cancellation, retries, and partial states require hand-maintained orchestration. This remains the early-release implementation path; it is not the proposed final conversational architecture.

**C — Benefits:** independently specialized reasoning and potential parallel work. **Costs:** extra calls, coordination, debugging, and conflicting intermediate conclusions. The bounded catalog and defined workflow do not currently justify these costs; deterministic policy enforcement would still be required.

## Trade-off analysis

Choose A because the product needs inspectable conditional tool execution while retaining one owner of request state and final validation. Delaying LangGraph until PRD 07 preserves B's simpler early implementation. Separate agents do not remove the need for the same evidence, exclusion, privacy, and budget checks.

The companion choices favor the documented MVP boundary: SQLite keeps structured persistence local; a curated catalog supports repeatable evaluation; permitted refresh addresses freshness; Ollama avoids making paid-provider availability a release dependency. These choices introduce local data-maintenance and hardware responsibilities. A hosted API/client deployment or server database may be appropriate for future shared access, but would also require identity, isolation, operations, and deployment decisions outside this MVP.

## Consequences

**Benefits**

- Pure screening/scoring services can be checked without a model, UI, or network.
- A source/model outage can preserve inspectable facts and validated partial output.
- Evidence versions and synthetic profiles support reproducible evaluation without retaining real sensitive requests.
- Each release can add a usable capability to the same local application.

**Costs and limitations**

- The local device remains the deployment and availability boundary; shared access is unsupported.
- Exact model quality, memory use, and latency need benchmarking. Token/call ceilings may produce partial findings.
- The operator must curate sources, review imports, rule references, conflicts, and freshness.
- Session-only sensitive state is lost on restart. A real user's full conversation cannot be replayed from audit logs.
- Missing critical evidence can reduce the shortlist to fewer than three products, including zero.

## Validation and action items

These are technical follow-ups for implementation, not user stories or completed checks.

- [ ] Pin and verify the Python/dependency baseline; ship a clean local catalog launch in PRD 01.
- [ ] Implement transactional imports, migrations, variant mapping, field provenance, and failed-refresh recovery in PRDs 01–02.
- [ ] Validate ingredient rules and deterministic eligibility/scoring with fixed fixtures; verify sponsorship neutrality in PRDs 03–05.
- [ ] Benchmark the local model, validate claim/evidence support, and exercise invalid-output/injection fallbacks in PRDs 04–06.
- [ ] Demonstrate form/chat numeric parity, nested-call limits, cancellation, and stale-result suppression in PRD 07.
- [ ] Inspect persistent stores for sensitive-data leakage; verify opt-in, cross-session preference reuse, and deletion in PRD 08.
- [ ] Reconcile usage and run the five successful scenarios, two named edge cases, and reproducible optimization comparison in PRD 09.

Acceptance criteria and proposed numeric defaults remain in the PRDs and TR-01–30; this record does not create a second set of thresholds. Data-source permissions, authoritative rules, model selection, and unbenchmarked targets remain unresolved implementation inputs.

## Revisit triggers

| Trigger | Decision to evaluate in a subsequent ADR |
| --- | --- |
| Public deployment, multiple users, or cross-device preferences become required | Identity, isolation, server storage, API/UI separation, and hosting |
| Local inference cannot meet measured quality/resource requirements | Smaller/different local model or explicitly enabled hosted task routing |
| Measured concurrency or semantic retrieval needs exceed the current approach | Storage/query changes; add vector retrieval only for an established semantic-search need |
| Graph orchestration adds no useful control or cannot meet tested requirements | Retain procedural orchestration or choose another bounded workflow mechanism |
| Independent parallel reasoning demonstrates measurable value | Separate agents with explicit authority, evidence, state, and budget contracts |

Record the replacement rationale and migration impact in a new ADR; keep this record and mark it superseded when appropriate.

## References

- [PRD index and release sequence](../requirements/README.md)
- [Technical requirements, TR-01–30](../requirements/TECHNICAL_REQUIREMENTS.md)
- [Architecture diagram guide](../architecture/README.md)
- [Editable architecture diagram](../architecture/cosmetic-advisor-architecture.drawio)
