# Ingredient screening evaluator

The PRD 03 evaluator is a pure Python service in
[`services/ingredient_screening.py`](../services/ingredient_screening.py). Its bounded
India manifest is in [`data/rules/india-limited-v1.json`](../data/rules/india-limited-v1.json)
with the official source review, scope, and recovery behavior in
[`data/rules/README.md`](../data/rules/README.md). It is deliberately a small rule set,
not a comprehensive regulatory database.

`IngredientRuleSet` requires versioned rules with a canonical ingredient, curated
aliases, an applicable product category, an exact source reference and section,
and a checked date. Rules cover India only. A prohibited match excludes the
product in the rule's category. A restricted match evaluates explicit use-condition
evidence and an optional maximum concentration in percent. A satisfied condition
is distinct from an explicitly failed one; missing conditions require verification.
The evaluator never derives concentration from declaration order.

`ScreeningInput` carries a public product/evidence ID and version, product category,
the original declaration and its completeness, explicit satisfied/failed use
conditions, and any sourced concentration values. The caller must pass only
validated public evidence, not a shopper's avoid list or allergy information.
Findings retain the matched declaration, rule citation/section/version/date,
applicable categories, checked/failed/missing conditions, and concentration
comparison. A confirmed prohibition or failed restriction yields `excluded`;
missing or conflicting ingredient evidence or a missing restriction condition yields
`requires_verification`; otherwise the result is `eligible_within_checks` **within
the limited supplied rule set only**. No result certifies safety or compliance.

`screening_input_from_catalog` only accepts explicitly selected catalog ingredient facts.
An unresolved declaration becomes a `requires_verification` input rather than an
implicit match. `result_is_current` checks both declared versions and content fingerprints for the
public evidence and rule set. Recompute when either changes, even if an upstream
caller accidentally repeats a version string. Results are not persisted by this
service. Validation errors must be converted to fixed, sanitized messages at a
future import or UI boundary; never display raw source text as instructions.

The product-detail panel displays regulatory findings separately from the editable
session-only avoid list. Exact declaration matches and curated rule aliases exclude a
product for that session. An unmatched term is shown as needing clarification and does
not become a regulatory or personal finding. Clear removes the avoid list and its
in-memory rule cache. Neither personal terms nor personal results are stored in the
catalog, a log, or an export.

The synthetic acceptance cases are in `tests/test_ingredient_screening.py` and
`tests/test_ingredient_screening_completion.py`. Their `example.com` citations are
test fixtures and must never be published as genuine regulatory findings.
