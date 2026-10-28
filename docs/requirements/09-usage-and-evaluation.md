# PRD 09 — Usage Visibility, Cost Controls, and Reproducible Evaluation

Status: Draft · Dependencies: [PRD 07](07-conversational-workflow.md), [PRD 08](08-preference-memory.md) · Source: report §§1, 15–19, 21

## Problem and outcome

The operator needs to understand resource use, demonstrate optimization, and reproduce product behavior. Token totals without context or a scripted demonstration cannot show whether the advisor is reliable or economical.

**Minimum deployable increment:** an execution/usage view and redacted report export in the running app, plus a repeatable evaluation dataset and demonstration guide. This release builds on usage capture and limits already required by earlier PRDs.

**Smallest delivery path:** aggregate the redacted model-attempt events already emitted
from PRD 04 onward, then add one local report/export view and a frozen, permitted
replay pack. The baseline demonstration uses local inference. Hosted routing and its
paid-call ledger are an explicitly configured extension, not a dependency for the
local release; if enabled later, the budget and preflight controls below apply before
the first paid call.

## Goals and scope

- Reconcile per-call measurements to per-run totals and distinguish measured, estimated, and unknown values.
- Demonstrate review batching/summary reuse with comparable evidence and output checks.
- Supply the report's five successful scenarios, two edge cases, and a reproducible final demonstration.

Include local usage reporting, configurable budget enforcement, benchmark evidence, and short operating/project documentation. A billing service, production monitoring platform, mandatory hosted provider, and claims of unmeasured savings are outside scope.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| USE-01 | Aggregate existing call events by run, role, activity, model, and cache status. Display input/output tokens, duration, role/protocol/model/prompt versions, attempts, validation status, and terminal outcome. Unknown token counts remain unknown and make totals explicitly partial; cache hits are not invented model calls. |
| USE-02 | Report local Ollama API expenditure as $0 while identifying device/electricity costs as unmeasured. For deliberately configured hosted inference, compute estimated USD cost as `(input_tokens*input_rate + output_tokens*output_rate)/1,000,000`, with dated rate configuration and token provenance. Missing rates yield unknown cost, not zero. |
| USE-03 | Let the controller enforce existing call/output-token limits across all five roles. If hosted inference is deliberately enabled, also enforce configurable per-run/project API budgets. Proposed defaults: $0.25 per hosted run and $25 project API ceiling. Reserve worst-case next-call cost before dispatch, including bounded output; deny/defer paid calls when rates/token bounds are unknown or projected totals exceed either ceiling. Reconcile reservations after completion. |
| USE-04 | Make the model/role policy visible: local inference first, deterministic work stays in Python, and only Review Evidence and Explanation and Citation may use the configured model adapters. Optional stronger local/hosted routing requires an explicit configuration. Record actual model selection and fallback reasons. If only one model is available, label tiering as unbenchmarked; never imply a hosted comparison occurred. No silent upload of user data. |
| USE-05 | Provide a repeatable A/B evaluation over the same fixed review IDs: A uses bounded raw-review input without summary-cache reuse; B uses validated batched summaries/reuse. Record a cold/warm-cache distinction, model/settings, token totals, elapsed time, estimated API cost, and `100*(A-B)/A` input-token reduction when A is known and nonzero. Check that critical supported benefits/complaints and eligibility are preserved. |
| USE-06 | Export a readable Markdown or JSON run report containing non-sensitive run identifiers, role IDs/versions, evidence/rule/policy versions, selected product IDs, aggregate usage, validation outcomes, and limitations. Exclude raw prompts, exclusions, medical details, credentials, sensitive profile data, and role payloads. Consumer runs use redacted constraint outcomes; reproducible evaluation uses separately labeled synthetic profiles and frozen public evidence. |
| USE-07 | Supply a rerunnable evaluation pack covering the five scenarios and two edge cases below, plus missing required input, unsupported country, duplicates, conflicting facts, invalid citations, prompt injection, memory reuse, budget/call ceilings, unsupported role capabilities, and invalid cross-role artifacts. Record actual pass/fail, versions, and dates; distinguish live retrieval from recorded-response fixtures. |
| USE-08 | Ship an updated startup/recovery guide, a concise 1–2-page-equivalent project overview, and a timed 10–12-minute demo guide. Cover the five roles, controller, tools, memory, guardrails, sources, test results, usage optimization, limitations, and MCP as an optional extension. A clean supported setup can reproduce the verified local demonstration without a live retailer dependency. |

## Required evaluation scenarios

| Scenario | Observable result |
| --- | --- |
| Oily skin, sunscreen, ₹800 | Only qualifying, evidence-backed sunscreen recommendations within budget |
| Dry skin, moisturiser, ₹600 | Only qualifying moisturiser recommendations; evidence supports claimed fit |
| Sensitive skin with an explicit exclusion | Confirmed matching ingredients are excluded; no safety guarantee |
| Very limited budget | Fewer than three or zero results, with actual limiting reasons |
| Sponsorship-only metadata change | Identical eligible IDs, scores, and order |
| Missing ingredient declaration | Unverified; outside the recommended set |
| Source/API failure | Bounded retry and visible fallback/partial result/error |

## Release verification and measures

Run the deployed usage view, reconcile a multi-step run with its call events, inspect a cache hit, and export a redacted report. Exercise a zero/unknown token total, missing rate, failed call, and exhausted budget; paid work must not dispatch when its cost cannot be bounded. Run the A/B comparison and report the observed reduction even if it is zero or negative.

Release targets: five successful end-to-end scenarios; both named edge cases pass; 100% hard-rule and evidence requirements pass; usage totals reconcile wherever complete measurements exist; no sensitive fields in exports. Proposed optimization target: at least 20% lower input tokens for B with preserved critical findings. Missing the optimization target is recorded as a result and triggers tuning, never fabricated savings.

## Dependencies and decisions

Engineering selects budget accounting and token-estimation bounds before optional paid use. Product/data freezes and licenses the demonstration evidence, confirms the scoring/rule versions, and records evaluation results. Model tiering can remain a documented optional path when hardware or budget does not support a second model; the core local product and its cost report must still work.
