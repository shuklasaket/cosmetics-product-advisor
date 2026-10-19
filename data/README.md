# Product evidence and test data

Genuine consumer-facing records must have permitted use and traceable provenance. No product, price, review, ingredient list, or regulatory restriction may be invented to complete the catalog.

## Intake templates

The CSV files in [templates/](templates/) contain headers only; they are collection aids, not a loaded seed catalog or an implemented import API.

| Template | Purpose |
| --- | --- |
| [products.csv](templates/products.csv) | Stable product/variant identity across sunscreen and moisturiser |
| [sources.csv](templates/sources.csv) | Source identity, permitted access/reuse, attribution, and verification date |
| [facts.csv](templates/facts.csv) | Each sourced observation linked to product and source IDs |

For each real product, establish category, India availability, INR price/pack identity, claims, ratings/counts where available, ingredient declaration/completeness, sponsorship status, and fact-level provenance. A retailer price and manufacturer ingredient declaration require separate observation rows. Represent unknown values explicitly; do not substitute zero or false.

Use timezone-aware UTC dates. Monetary observations should store integer paise; the UI can format them as INR. `value_json` holds the typed field value, such as a JSON number, string, list, object, or null. The [catalog-v1 contracts](../docs/catalog-contracts.md) now validate these conventions
in memory. The [local JSON importer](../docs/catalog-import.md) loads catalog-v1
envelopes with explicit resolutions and complete permission metadata. CSV-to-contract
mapping remains manual; this command does not parse the intake templates.

PRD 02's [approved-source registry](../docs/approved-source-registry.md) is a separate
authorization boundary for retrieval. A catalog-v1 source observation does not by itself
authorize network access. No enabled connector registration is committed by US-034;
operator/data review is required before a later adapter can be enabled.

## Collection policy

1. Check the source's access/reuse conditions and record the reference, attribution, and check date.
2. Verify the exact formulation/pack variant; do not combine mismatched ratings, ingredients, and prices.
3. Keep conflicting observations and their sources. Resolve them explicitly using the release's policy.
4. Collect only permitted review text and necessary metadata; remove unnecessary reviewer identifiers.
5. Regulatory data needs exact authoritative references and domain review before PRD 03 uses it.

The versioned [India genuine starter catalog](seed/README.md) contains 10 reviewed
products, five per category. The completed MVP still targets approximately 20–30.
The header-only templates do not add to these counts.

## Storage and fixtures

`data/local/` is ignored for local imports and working copies. Only verified material
whose redistribution is allowed belongs in committed seed data. The committed starter
seed records its maintainer-approved non-commercial factual-use boundary and attribution
beside the dataset.

Tests use temporary directories/databases and labeled synthetic profiles or recorded responses. Synthetic product/review fixtures must stay in test fixtures and never appear as genuine catalog entries. Raw user conversations, current budgets, avoid lists, and medical details must not enter committed fixtures, databases, logs, or exports.

## Local persistence

The [catalog storage and recovery guide](../docs/catalog-storage.md) documents schema v1,
complete snapshot writes, immutable evidence history, explicit migrations and backup/restore.
Only validated public catalog evidence belongs there. The
[JSON importer](../docs/catalog-import.md) validates and merges local batches;
the CSV templates are collection aids. Storage/import tests use synthetic temporary
databases and do not establish a genuine seed.
Generated databases, journals and backup directories must remain uncommitted.
