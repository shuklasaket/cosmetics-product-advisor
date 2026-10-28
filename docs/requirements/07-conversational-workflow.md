# PRD 07 — Controlled Conversational Recommendation Workflow

Status: Draft · Dependencies: [PRD 02](02-approved-data-refresh.md) through [PRD 06](06-grounded-explanations.md) · Source: report §§3–4, 10–11, 14–15, 17–18

## Problem and outcome

Shoppers should be able to describe a need in natural language and receive the same validated result as the structured interface. Missing details and failed evidence retrieval need clear, bounded paths rather than an unrestricted agent loop.

**Minimum deployable increment:** a Streamlit conversation that coordinates the existing search, review, screening, ranking, and explanation tools through one LangGraph workflow, with live execution status.

**Smallest delivery path:** add one fixed LangGraph state machine that validates a
natural-language request, asks for missing fields, then calls the same services used
by the form in a known order. Conditional edges cover empty, partial, failed, and
cancelled outcomes. The model extracts request fields; it does not select arbitrary
tools or control the graph. Keep state in the Streamlit session and use the existing
SQLite store only for allowlisted public evidence and redacted events.

## Goals and scope

- Complete a request end to end through real, inspectable tool calls.
- Ask only for required missing information and preserve explicit user corrections within a session.
- Terminate successfully, partially, or with a clear error within configured execution limits.

One orchestrator selects from approved Python tools. Independent agents, MCP hosting, unrestricted browsing, persistent conversation history, and autonomous purchases are deferred. The existing structured path remains available.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| AGT-01 | Interpret category, skin type, INR budget, country, exclusions, and preferences into the same validated schema used by the form. Required fields are category, skin type, and budget; India/INR are visible defaults. Ask about missing required fields or ambiguous exclusions before proceeding; optional preferences may be skipped. |
| AGT-02 | Use typed state and explicit stages: collect/validate → search/details → review analysis → ingredient checks → hard filters/ranking → evidence validation → explanation → display. Conditional paths handle no results, unavailable reviews, unresolved ingredients, and failed sources. Python owns validation, eligibility, and arithmetic. |
| AGT-03 | Expose allowlisted structured tools for search, product details, reviews/analysis, ingredient checks, and ranking. Validate tool arguments/results; reject unsupported tools or arbitrary endpoints. Record actual tool outcomes and whether they came from live retrieval or valid cache/local evidence. |
| AGT-04 | Preserve current-session requirements and explicit corrections. “Show cheaper options” retains category/skin type but asks for a new maximum unless a numeric limit is supplied. A correction recomputes downstream results and never reuses a shortlist for an obsolete request version. |
| AGT-05 | Bound execution. Proposed defaults: 30 tool invocations per recommendation run, at most six review-model calls per product, 20 model calls per run overall, existing per-step token caps, and a five-minute run deadline. Count nested model calls separately from tool invocations. On limit/deadline, stop starting work and surface only already validated partial results or an explicit failure. |
| AGT-06 | Display progress from actual state transitions and an expandable execution panel with run ID, stage, tool, timing, status, counts, and redacted errors. Do not persist raw user prompts, avoid lists, or sensitive tool arguments. Completion markers require successful validation. |
| AGT-07 | Treat retrieved text and model output as untrusted. They cannot alter system instructions, tool permissions, budgets, or scoring. Use bounded schema-repair paths and already defined fallbacks; no retry may bypass a failed ingredient gate. |
| AGT-08 | Support cancel/reset and controlled recovery. Reset clears session-only sensitive state; cancellation stops new calls and marks the run cancelled. In-flight results from cancelled/superseded runs cannot overwrite current results. Persist only redacted audit events; durable raw graph checkpoints remain disabled. |

## Release verification

Deploy the conversation and enter “I need sunscreen for oily skin.” Supply the missing budget, then obtain a validated shortlist and inspect the actual tool trace. Request cheaper options, supply a lower maximum, and verify preserved session attributes and recomputed eligibility.

Exercise no products, no reviews, unavailable external source, invalid model output, hostile retrieved text, repeated follow-up turns, a limit hit, and cancellation during analysis. Verify explicit terminal states and no stale results presented as current. Compare structured and conversational runs with identical validated inputs; eligible IDs and deterministic scores must match.

## Success measures

- Five end-to-end acceptance scenarios complete through the graph with truthful tool traces.
- 100% of paired structured/conversational fixtures produce matching eligibility and score fields.
- 100% of limit, cancellation, and invalid-tool fixtures terminate without unsupported recommendations.

## Dependencies and decisions

Use valid cached review analyses first. Proposed fresh-analysis bound: five products per run, selected by stable product ID from eligible search matches. Rank all otherwise eligible candidates; products without valid analysis use PRD 05's missing-review policy. Show analyzed/unanalyzed candidate counts and this coverage limit so the shortlist does not imply every review was examined.

Engineering calibrates the proposed limits against the selected MacBook/model, recording any revised bounds before release. The graph may use a valid local catalog during external outages, with freshness and source limitations visible. Preference tools are added only in PRD 08; auditability does not authorize persistent sensitive checkpoints.
