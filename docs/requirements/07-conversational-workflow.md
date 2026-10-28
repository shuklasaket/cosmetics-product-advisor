# PRD 07 — Controlled Conversational Recommendation Workflow

Status: Draft · Dependencies: [PRD 02](02-approved-data-refresh.md) through [PRD 06](06-grounded-explanations.md) · Source: report §§3–4, 10–11, 14–15, 17–18

## Problem and outcome

Shoppers should be able to describe a need in natural language and receive the same validated result as the structured interface. Missing details and failed evidence retrieval need clear, bounded paths rather than an unrestricted agent loop.

**Minimum deployable increment:** a Streamlit conversation that coordinates exactly five fixed specialist roles through one trusted LangGraph controller, with live execution status.

**Smallest delivery path:** add one fixed LangGraph controller that validates a
natural-language request, asks for missing fields, and invokes these five roles in a
known order: Intake and Clarification; Catalog Evidence; Review Evidence; Policy and
Ranking; Explanation and Citation. Conditional edges cover empty, partial, failed, and
cancelled outcomes. Roles exchange typed minimum-necessary artifacts only through the
controller. A model extracts fields, review findings, or claim selections; it does not
select arbitrary tools, control routing, or communicate with another role. Keep state
in the Streamlit session and use SQLite only for allowlisted public evidence and
redacted events.

## Goals and scope

- Complete a request end to end through real, inspectable tool calls.
- Ask only for required missing information and preserve explicit user corrections within a session.
- Terminate successfully, partially, or with a clear error within configured execution limits.

The controller statically selects role-specific capabilities; roles are not independent
or autonomous agents. They cannot delegate, invoke one another, own persistent state,
or select tools dynamically. MCP hosting, unrestricted browsing, persistent conversation
history, and autonomous purchases are deferred. The existing structured path remains available.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| AGT-01 | The Intake and Clarification role interprets category, skin type, INR budget, country, exclusions, and preferences into a candidate for the same validated schema used by the form. Required fields are category, skin type, and budget; India/INR are visible defaults. It has no tools and can only ask about missing required fields or ambiguous exclusions; optional preferences may be skipped. |
| AGT-02 | Use typed state and explicit controller-owned stages: intake/validate → catalog evidence → review evidence → policy/ranking → explanation/citation → display. The controller invokes exactly these five roles in that order, skipping only documented unavailable/empty paths. Each role receives a minimum-necessary immutable view and returns a schema-validated artifact to the controller. Python owns validation, eligibility, arithmetic, citations, and final publication. |
| AGT-03 | Grant fixed capabilities only: Catalog Evidence may call allowlisted search/detail and approved retrieval adapters; Review Evidence may call the bounded review-model adapter; Policy and Ranking may call deterministic screening/ranking services; Explanation and Citation may call only the bounded explanation-model adapter. Intake has no tools. Roles cannot invoke each other, preference tools, arbitrary endpoints, SQLite, shell, or dynamic dispatch. Validate every handoff and record whether evidence came from live retrieval or valid cache/local evidence. |
| AGT-04 | Preserve current-session requirements and explicit corrections. “Show cheaper options” retains category/skin type but asks for a new maximum unless a numeric limit is supplied. A correction recomputes downstream results and never reuses a shortlist for an obsolete request version. |
| AGT-05 | The controller centrally bounds every role. Proposed defaults: 30 tool invocations per recommendation run, at most six review-model calls per product, 20 model calls per run overall, existing per-step token caps, and a five-minute run deadline. Count nested model calls separately from tool invocations. On limit/deadline, stop starting work and surface only already validated partial results or an explicit failure. No role can reserve or reset another role's counter. |
| AGT-06 | Display progress from actual controller transitions and an expandable execution panel with run ID, role, stage, capability, timing, status, counts, and redacted errors. Do not persist raw user prompts, avoid lists, sensitive tool arguments, or role payloads. Completion markers require controller validation. |
| AGT-07 | Treat retrieved text and model output as untrusted. They cannot alter system instructions, role permissions, routing, budgets, or scoring. Validate every cross-role artifact, use bounded schema-repair paths and already defined fallbacks, and never let a retry bypass a failed ingredient gate. |
| AGT-08 | Support cancel/reset and controlled recovery. Reset clears session-only sensitive state; cancellation stops new calls across the full role chain and marks the run cancelled. In-flight results from cancelled/superseded runs cannot overwrite current results. Persist only redacted controller-owned audit events; durable raw graph checkpoints remain disabled. |

## Release verification

Deploy the conversation and enter “I need sunscreen for oily skin.” Supply the missing budget, then obtain a validated shortlist and inspect the actual tool trace. Request cheaper options, supply a lower maximum, and verify preserved session attributes and recomputed eligibility.

Exercise no products, no reviews, unavailable external source, invalid role output, hostile retrieved text, repeated follow-up turns, a limit hit, and cancellation during each model-capable role. Verify that a role cannot request an unsupported capability, communicate directly with another role, or receive sensitive state outside its contract. Compare structured and conversational runs with identical validated inputs; eligible IDs and deterministic scores must match.

## Success measures

- Five end-to-end acceptance scenarios complete through the graph with truthful tool traces.
- 100% of paired structured/conversational fixtures produce matching eligibility and score fields.
- 100% of limit, cancellation, invalid-tool, and invalid-handoff fixtures terminate without unsupported recommendations.

## Dependencies and decisions

Use valid cached review analyses first. Proposed fresh-analysis bound: five products per run, selected by stable product ID from eligible search matches. Rank all otherwise eligible candidates; products without valid analysis use PRD 05's missing-review policy. Show analyzed/unanalyzed candidate counts and this coverage limit so the shortlist does not imply every review was examined.

Engineering registers the five role/protocol versions and calibrates the proposed limits against the selected MacBook/model, recording any revised bounds before release. The graph may use a valid local catalog during external outages, with freshness and source limitations visible. Preference tools remain a trusted controller boundary in PRD 08; no role can claim consent or write preferences. Auditability does not authorize persistent sensitive checkpoints.
