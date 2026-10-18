---
name: cosmetics-data-integrity
description: "Implement or review this project's sourced catalog imports, SQLite evidence storage, ingredient screening, or deterministic ranking. Use for PRDs 01–03 and 05 data/policy work; not UI-only changes or general SQL tasks."
---

# Cosmetic evidence and deterministic decisions

Use the relevant [PRD](../../../docs/requirements/README.md), [technical contracts](../../../docs/requirements/TECHNICAL_REQUIREMENTS.md), and [data policy](../../../data/README.md) as the authority. Inspect existing schemas, migrations, repositories, and services before extending them; the CSV templates are collection aids, not an implemented import contract.

## Establish the evidence boundary

Separate product/variant identity, source observations, and resolved consumer-facing facts. Establish source permission, exact formulation/pack matching, retrieval/verification dates, completeness, sponsorship, and field-level provenance before importing genuine records. Preserve conflicting observations for explicit resolution. Missing evidence remains unknown; fabricated products, ingredient declarations, reviews, prices, and citations cannot fill gaps.

Use integer paise and explicit decimal arithmetic for prices and scores. A zero budget is valid. Validate imported types and units at the boundary; select Pydantic coercion/strictness deliberately so malformed values cannot silently become plausible facts. Keep source and product IDs stable across repeat imports.

## Protect state during changes

Keep persistence in repositories and introduce explicit migrations with the first schema. Use parameterized SQL and an explicit transaction boundary for each atomic import. Set Python 3.12 SQLite transaction behavior deliberately instead of assuming implicit commits; verify foreign-key enforcement on each connection. Test failed imports and migrations against an existing valid database, including recovery behavior.

Sensitive exclusions, medical details, budgets, and raw conversations remain session-only. Do not copy request models or graph state into database rows, exception payloads, logs, fixtures, exports, or persistent caches. Persistent preferences are restricted to the separately reviewed PRD 08 contract.

## Keep policy in Python

Ingredient eligibility precedes ranking. Missing or conflicting critical evidence cannot be repaired by a score or model explanation. Regulatory rules need authoritative references, versioned applicability, and domain review; never invent a prohibited-ingredient list or infer an unknown concentration as safe.

Implement the documented score formula and deterministic tie order. Exclusions and eligibility do not become model decisions. Sponsorship cannot influence ranking. Explanations consume validated decisions and evidence rather than modifying them.

## Verify the affected contract

Use temporary databases and clearly labeled synthetic fixtures for repeatable failure and arithmetic checks. Cover applicable variant mismatches, unknown values, duplicate/repeated imports, rollback, freshness boundaries, zero budgets, exclusions, score ties, and sponsorship neutrality. Keep genuine catalog acceptance evidence separate from synthetic fixtures. Add tests for affected behavior rather than mirroring implementation details.

For current API details, consult the pinned environment and primary documentation: [Python 3.12 SQLite](https://docs.python.org/3.12/library/sqlite3.html), [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/). Follow the repository's shared checks and PR workflow; report actual verification and unresolved data inputs.
