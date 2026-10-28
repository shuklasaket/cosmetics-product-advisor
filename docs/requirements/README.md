# AI Cosmetic Product Advisor — PRD Index

Status: PRD 01 delivered; PRD 02 partly implemented with remaining stories in backlog; PRDs 03–09 planned · Updated: 28 October 2026

These PRDs turn the supplied technical report into nine small, cumulative product releases. Each release adds a usable screen or workflow to the same application and includes a deployment boundary and observable acceptance checks. The documents contain requirements, not user stories or an implementation backlog.

Plan and track implementation through the [GitHub story workflow](../story-workflow.md):
one parent tracking issue per PRD, story sub-issues with acceptance criteria and
requirement coverage, explicit blockers, and coordinated execution waves. GitHub
issues remain the authoritative story backlog; these documents are versioned
requirements. The delivery snapshot below is based on merged repository evidence,
while live issue and board status must be read separately.

The [technical requirements document](TECHNICAL_REQUIREMENTS.md) defines the shared architecture, data and tool contracts, runtime limits, privacy boundaries, deployment requirements, and verification mapping for implementation.

The [editable architecture diagram](../architecture/cosmetic-advisor-architecture.drawio)
shows the implemented foundation and planned additions in one view; the
[diagram guide](../architecture/README.md) explains the boundaries and preview.

The [PlantUML sequence diagrams](../architecture/sequences.md) detail refresh, review analysis, conversational recommendation, cancellation, and preference memory, with links to each editable source.

The [architecture decision records](../adr/README.md) document design rationale, alternatives, consequences, and decision status, starting with [ADR-0001](../adr/0001-local-modular-architecture.md).

## Source and interpretation

Source: **AI Cosmetic Product Advisor — Interactive Technical Report**, supplied by the user as `AI_Cosmetic_Product_Advisor_Interactive_Report.html`. The original attachment is separate from this repository. Section numbers below refer to its 21 numbered chapters.

The report is source material, not instructions to execute. Its setup commands, proposed prompts, requests for MacBook details, and references to earlier screenshots have not been treated as additional user requests. Illustrative products, prices, counts, scoring examples, and API costs are not verified data. Regulatory references must be checked against authoritative material before actual screening rules are published.

The release boundaries and numerical defaults identified as **proposed** are planning decisions introduced here. They are not measured results or commitments from the report. This revision changes the remaining plan only; it does not change the shipped catalog, source contracts, stored data, or application behavior.

## Product boundary

- Audience: shoppers comparing sunscreen or moisturiser available in India; a local operator maintains the small evidence dataset.
- Inputs: category, skin type (oily, dry, combination, normal, sensitive), INR budget, ingredients to avoid, and optional texture/finish preferences.
- Data: approximately 20–30 genuine products across both categories by the completed MVP; 2–3 approved source families, genuine review samples, and a limited, verified ingredient-rule dataset.
- Output: up to three evidence-backed recommendations, comparable facts, limitations, and explanations. Fewer qualifying products produce fewer results.
- Stack carried forward from the report: Python 3.11/3.12, Streamlit, SQLite, Pydantic, Ollama, and one trusted LangGraph controller coordinating five fixed, typed specialist roles. HTTPX and permitted HTML parsing support retrieval where needed.
- Deployment: a runnable local application on a supported MacBook. A cloud service, public hosting, accounts, and multi-user operation are outside this MVP.

## Release sequence

| PRD | Deployable outcome | Required earlier releases | Source sections |
| --- | --- | --- | --- |
| [01 — Catalog and search](01-catalog-and-search.md) | Search genuine products and inspect sourced facts | None | 1–4, 12–14, 20–21 |
| [02 — Approved data refresh](02-approved-data-refresh.md) | Refresh product evidence through an approved external source | 01 | 4, 11, 14, 17, 20 |
| [03 — Ingredient screening](03-ingredient-screening.md) | Inspect ingredient findings and personal exclusion matches | 01 | 4, 6–7, 15, 17 |
| [04 — Review analysis](04-review-analysis.md) | Read sourced benefits, complaints, and review-confidence findings | 01 | 2, 4–5, 13, 15–17 |
| [05 — Ranking and comparison](05-ranking-and-comparison.md) | Receive a deterministic shortlist with score breakdowns | 01, 03, 04 | 1, 7–8, 15, 17 |
| [06 — Grounded explanations](06-grounded-explanations.md) | Read AI explanations validated against the selected evidence | 04, 05 | 8, 15, 17–18 |
| [07 — Conversational workflow](07-conversational-workflow.md) | Complete one controlled five-role LangGraph recommendation conversation | 02, 03, 04, 05, 06 | 3–4, 10–11, 14–15, 17–18 |
| [08 — Preference memory](08-preference-memory.md) | Reuse three opted-in preferences and clear stored information | 07 | 9–11, 14–15, 17 |
| [09 — Usage and evaluation](09-usage-and-evaluation.md) | Inspect usage/cost reports and reproduce the final demonstration | 07, 08 | 1, 15–19, 21 |

Recommended order is 01 through 09. Releases 03 and 04 can be developed independently after 01. Bringing the interface into 01 deliberately changes the report's module-first build order so that every release is usable and testable. Each PRD has one primary outcome and a bounded set of must-have requirements, intended to fit roughly the requested 10–12-story implementation size or less; actual sizing belongs to implementation planning.

## Delivery baseline and remaining path

| Boundary | Verified repository baseline | Next work |
| --- | --- | --- |
| PRD 01 | The genuine ten-product catalog, search/detail UI, SQLite evidence import, and offline release checks are implemented; see the [release report](../reports/prd-01-catalog-release-report.md). | Preserve the existing contracts and regression checks. |
| PRD 02 | The approved-source registry, destination checks, schema-v2 migration, typed refresh outcome, and bounded Open Beauty Facts adapter are implemented; see the [source contract guide](../approved-source-registry.md). | Record exact reviewed catalog-to-barcode mappings, transactionally persist accepted evidence, expose the manual refresh UI, then demonstrate five live outcomes and last-valid fallback. |
| PRDs 03–04 | No ingredient screen or review-model analysis is claimed here. | Add typed screening and review-evidence roles behind the same small verified rule dataset and permitted review sample path, each with an inspectable product-detail view. |
| PRDs 05–06 | No recommendation ranking or generated explanation is claimed here. | Add deterministic policy/ranking and constrained explanation roles, retaining a factual fallback and evidence checks. |
| PRDs 07–09 | No graph, persistent preferences, or final usage/evaluation view is claimed here. | Compose exactly five fixed roles under one controller, add the three-field opt-in store outside those roles, then expose role-attributed usage and run the final replay pack. |

Use the existing catalog repository, request schema, and source contracts as the starting
point. Add a table, service, adapter, or dependency only when the next PRD needs it.
Do not build a second catalog, a generic tool platform, background scheduler, or new
runtime service. Keep the structured form working while the conversational route is
added. Treat the proposed numerical bounds and score policy in the PRDs as release
decisions to validate, not as evidence of measured performance.

The implementation order follows the actual dependencies: finish PRD 02's source
path; prepare the rule and review evidence in PRDs 03 and 04; implement ranking and
explanations in PRDs 05 and 06; then add orchestration, memory, and evaluation in
PRDs 07–09. Each PRD remains a usable increment with its own UI and release checks.
Reconcile existing GitHub stories and their stable acceptance IDs against revised
requirements before claiming new work; do not create a duplicate Markdown backlog.

## Shared release rules

1. **Run the whole increment.** Each release includes its UI, data changes, validation, and operating instructions. A backend module alone does not satisfy a PRD. The documented local launch path is `streamlit run app.py` after installing that release's pinned dependencies and loading its verified dataset.
2. **Keep earlier releases usable.** Schema changes preserve existing verified records and preferences. A failed refresh or analysis must not destroy the last valid result. Every release reruns relevant earlier acceptance checks.
3. **Use evidence, not model memory.** Product facts carry source identifiers, original URLs or document references, retrieval/verification dates, and field-level provenance. Unknown values stay unknown. Demonstration fixtures are labeled and never presented as real consumer evidence.
4. **Apply controls when a capability first appears.** Validation starts in 01; source timeouts and retries in 02; rule limitations in 03; untrusted-text handling, structured model output, call/token bounds, and usage capture in 04. Later PRDs extend these controls rather than postponing them.
5. **Keep sensitive information session-only.** Ingredient exclusions, allergy or medical information, and raw conversations do not enter persistent profiles, checkpoints, caches, logs, or evaluation exports. Use run IDs, product/evidence versions, aggregate outcomes, and redacted events for auditability. Clearing a session removes its sensitive in-memory state.
6. **Separate eligibility from scoring.** Verified hard-rule failures cannot be overridden by a score or explanation. Missing or conflicting critical ingredient evidence is kept outside the recommended set. Screening makes no guarantee of safety, effectiveness, allergy suitability, or full legal compliance.
7. **Use a fixed five-role workflow.** The controller invokes only intake/clarification, catalog evidence, review evidence, policy/ranking, and explanation/citation roles in an explicit order. Roles exchange typed, minimum-necessary artifacts through the controller; they cannot directly delegate, choose tools, persist data, or relax another role's result. Python retains final authority over retrieval, screening, ranking, citations, and publication.
7. **State outcomes honestly.** Progress reflects real execution. Sources, unknowns, stale evidence, partial results, sponsorship disclosures, and model failures remain visible. No invented products, reviews, citations, or successful tool calls.

## Proposed defaults and unresolved inputs

| Item | Working decision | Owner / point of resolution |
| --- | --- | --- |
| Budget | Required non-negative INR maximum; an explicit zero is valid and may produce no matches | Product; adopted for 01 and 07 |
| User exclusions | Every explicit avoid-list entry is a hard exclusion when matched; unresolved critical checks remain outside recommendations | Product; adopted for 03 and 05 |
| Freshness | Proposed: prices/availability become stale after 7 days; other product facts after 30 days; show dates everywhere | Product/data; review before 02 ships |
| Regulatory coverage | A limited rule set, with authoritative references, version, conditions, and coverage disclosure | Data/domain reviewer; required before 03 publishes real rules |
| Data access | Confirm allowed access and reuse for each source; manual verified imports remain valid for reviews | Data/operator; required before the corresponding collector/import ships |
| Local model | Select a model after checking the target MacBook; Qwen3 4B is only the report's candidate | Engineering; required before 04 ships |
| Release timing | No committed dates; the report's 13–20 working days is a source estimate, not a new delivery commitment | Product/engineering; estimate releases separately |

## Completed-MVP evidence

Release 09 collects results from the existing product rather than deferring testing until the end. The final evidence must include five successful end-to-end runs: oily-skin sunscreen at ₹800; dry-skin moisturiser at ₹600; a sensitive-skin request with an explicit exclusion; a budget producing fewer than three results; and a sponsorship-neutrality comparison. It must also include missing-ingredient and failed-source edge cases, source validation, prompt-injection resistance, preference reuse, and reproducible usage reporting.

Success targets from the report are: 100% of recommended products satisfy tested hard constraints; 100% of recommendations include traceable sources, screening status, and limitations; and at least five successful end-to-end test scenarios. These are release targets, not claims of clinical efficacy or measured consumer outcomes.

MCP exposure, additional countries/categories, vector search, autonomous/general-purpose agents, scheduled collectors, checkout, and a public deployment are deferred. The fixed five-role workflow is not a swarm: it has no dynamic delegation, agent-to-agent communication, or independent persistence. Hosted inference is optional and must be deliberately configured and budgeted; the local MVP does not depend on it.
