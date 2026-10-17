# PRD 03 — Ingredient Screening and Personal Exclusions

Status: Draft · Dependencies: [PRD 01](01-catalog-and-search.md) · Source: report §§4, 6–7, 15, 17

## Problem and outcome

Shoppers cannot reliably distinguish a personal ingredient preference from a verified restriction or an unresolved information gap. They need inspectable findings without a misleading safety or compliance assurance.

**Minimum deployable increment:** an ingredient-screening panel on catalog product details, with session-only user exclusions, structured findings, and source-linked rule references.

## Goals and scope

- Detect every confirmed excluded/prohibited ingredient in the curated acceptance fixtures.
- Attach an exact source reference and applicable conditions to every regulatory finding.
- Make incomplete lists, ambiguous aliases, and unknown restriction conditions visibly unresolved.

This is a limited India-specific screen. It does not diagnose conditions, assess clinical efficacy, infer concentrations, certify legal compliance, or guarantee absence of allergic reactions. No comprehensive regulatory dataset is implied.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| ING-01 | Load a small verified India rule set with canonical ingredient, curated aliases, rule type, category/use conditions, concentration limits where applicable, exact authoritative document/section, version, and last-checked date. Reject rules missing required provenance; display dataset version and coverage limits. |
| ING-02 | Normalize case, spacing, and curated INCI aliases deterministically. Keep original declarations and match evidence. An ambiguous or unrecognized name remains unresolved; an LLM cannot create a rule or decide a final regulatory match. |
| ING-03 | Accept an editable session-only avoid list. A confirmed ingredient/alias match produces a hard user-exclusion finding regardless of legal status. A general preference such as lightweight remains a preference; an ambiguous avoidance term is flagged for clarification rather than treated as a verified absence. |
| ING-04 | Emit separate per-ingredient findings: prohibited in the applicable context; restricted with conditions satisfied; restricted with conditions failed; requires verification; user-excluded match; or no matching issue in the implemented rule set. Applicable prohibition or failed restriction blocks eligibility; unknown concentration/category conditions require verification. |
| ING-05 | Mark absent, partial, conflicting, or critically ambiguous ingredient evidence as unverified. Missing required concentration stays unknown; ingredient order cannot be used to infer it. A complete list with no matching rule means only that no issue was found within the limited dataset. |
| ING-06 | Display matched declaration, finding type, conditions checked/missing, rule citation, and date. Keep personal exclusions separate from regulatory findings and show a concise limitation beside every screening summary. No green “safe” or “fully compliant” designation is permitted. |
| ING-07 | Publish a structured eligibility outcome for ranking: excluded for confirmed hard-rule failures; verification required for unresolved critical checks; or eligible within limited checks. The first two groups remain outside the future recommended set but remain inspectable in the catalog. Changing an avoid list recomputes the result. |
| ING-08 | Version screening results by product ingredient evidence and rule-set version. A changed declaration or rule invalidates prior results. User-specific checks stay in session memory and are cleared with the session; persistent caches/logs contain no avoid-list or allergy details. |

## Release verification

In the deployed product-detail screen, inspect a sourced complete declaration and apply a confirmed exclusion. Show the matching ingredient and the changed eligibility status. Use clearly labeled synthetic rule fixtures to exercise prohibition, a satisfied restriction, a failed restriction, and a concentration-dependent restriction with no concentration.

Also verify a missing ingredient list, an alias match, an ambiguous avoid term, a rule without provenance, and a rule-version change. No unresolved case may receive a safety assurance or quietly enter the eligible group.

## Success measures

- 100% match/exclusion correctness on the curated rule and alias fixtures.
- 100% of regulatory flags carry a valid rule reference and scope.
- Zero unsupported safety/compliance assurances in acceptance outputs.

## Dependencies and decisions

A data/domain reviewer must validate the limited real rule set before it is published. The report's regulatory names/versions are leads to verify, not authoritative rules supplied by this PRD. Proposed product policy: all explicit avoid-list matches are hard exclusions, and all unresolved critical ingredient checks stay outside recommendations.
