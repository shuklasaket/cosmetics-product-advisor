# Catalog and request contracts

[PRD 01](requirements/01-catalog-and-search.md) uses Pydantic boundary models in
[`schemas/requirements.py`](../schemas/requirements.py) and
[`schemas/catalog.py`](../schemas/catalog.py). These contracts validate in-memory
inputs; they do not load files, create a database, search products or collect evidence.
The development preview remains the runnable application until its UI stories ship.

## Shopper requests

`UserRequirements` requires `category`, `skin_type` and `budget_inr`. Categories are
`sunscreen` and `moisturiser`; skin types are `oily`, `dry`, `combination`, `normal`
and `sensitive`. Country/currency default visibly in consumers to `India`/`INR`;
other values are rejected by the contract. UI and conversational consumers must
reuse this validation before dispatching a search.

Budgets accept decimal text, integers, `Decimal`, or a finite float interpreted
through its decimal string. Booleans, blank/non-numeric/non-finite/negative values
and amounts smaller than whole paise are rejected. There is no rounding: `800.01`
means 80,001 paise and `800.009` is invalid. Zero is valid. `budget_paise` performs
an exact integer conversion independent of the ambient decimal arithmetic context;
callers must not submit that derived property as an input field.

Optional `exclusions` are an immutable sequence of nonblank strings. Optional
`preferences` has nullable nonblank `texture` and `finish` strings. These are
collected for later use; PRD 01 does not evaluate exclusions or turn skin-type
claims into eligibility rules. Absent exclusions become an empty sequence;
absent preferences remain null. Blank entries and undeclared preference fields
are rejected rather than silently discarded.

Requests and preferences are session-only. Their representations omit personal
fields, but explicit model serialization still contains them for in-memory use.
Never persist or log these models, serialized requests or raw `ValidationError`
objects. Clear request-dependent results when editing/clearing the session.
Consumers display `UserRequirements.validation_messages(error)` for fixed,
field-specific diagnostics without rejected input, exception context or unknown
field names. The equivalent method on every catalog model also omits raw data.

## Versioned evidence envelope

The canonical validation boundary is `CatalogEnvelope.model_validate(payload)`
(or `model_validate_json`), with required `contract_version: "catalog-v1"` and four
collections: `products`, `sources`, `observations` and `resolutions`. Always validate
the complete envelope before a downstream write; individual record models cannot
check foreign references or batch-wide conflicts. Unknown contract versions and
undeclared fields are rejected. Empty collections are valid for an empty catalog;
only the genuine seed/release checks establish required product counts.

Models are frozen, with immutable collection values. Use normal validation when
changing records, rather than unvalidated `model_construct`/`model_copy(update=...)`.
IDs are stable, case-sensitive ASCII tokens of 1–128 characters, beginning with
an alphanumeric character and thereafter allowing alphanumerics, `.`, `_`, `:` or
`-`. Non-ID text is trimmed and must be nonblank when supplied.

| Record | Required content and checks |
| --- | --- |
| `Product` | `product_id`, brand, name, category and an exact formulation/pack `variant`; optional `pack_size` remains null when unknown. Every non-null identity field also requires selected, matching evidence. The operator must establish exact variant identity; the schema cannot verify a manufacturer's real formulation. |
| `Source` | `source_id`, type (`manufacturer`, `retailer`, `dataset`, `document`), original reference, access conditions, reuse conditions, permission reference, attribution, `last_checked`, and explicit boolean `enabled`. All observations must reference enabled sources present in the envelope. Disabled unused registry entries are allowed. Metadata records permission evidence; it does not independently establish legal reuse rights. |
| `FactObservation` | `evidence_id`, exact `product_id`, registered `source_id`, `field_name`, typed `value`, original reference, `retrieved_at`, `verified_at`, `content_version` (hash or version), source `snapshot_id` and explicit `validation_status` (`verified`/`unverified`). Price additionally requires explicit India/INR context. |
| `FactResolution` | Exact product/field key, `selected` or `unresolved` status, nonempty unique `evidence_ids`, and `policy_version: "explicit-selection-v1"`. Every observed product/field needs a resolution status, including historical observations. |

References are HTTPS URLs without embedded credentials, whitespace or backslashes,
or explicit nonblank `document:` references. No URL is fetched or HTML executed by
these contracts. Source host/redirect allowlists and escaped rendering remain
responsibilities of future adapters/UI. Timestamps accept timezone-aware ISO strings
or datetimes, reject naive/numeric inputs, and normalize to UTC. Verification cannot
precede retrieval. `last_checked` uses the same UTC contract.

### Fact values

All observation values below may be null to represent unknowns. Omitting an
optional observation entirely also leaves that fact unknown. A known zero count or
price is different from unknown; empty text is never an unknown substitute.

| `field_name` | Non-null value |
| --- | --- |
| `brand`, `name`, `variant`, `pack_size`, `ingredient_declaration` | Nonblank text |
| `category` | `sunscreen` or `moisturiser` |
| `availability` | Sequence of nonblank country names; empty means explicitly no listed availability, null means unknown |
| `price_paise` | Non-negative integer, with `country: "India"` and `currency: "INR"`; numeric strings, floats and booleans rejected |
| `skin_type_claims` | Sequence of supported skin types; these are declared claims |
| `rating` | Object with finite decimal `score`, `scale_min` and `scale_max`; non-negative increasing scale containing the score |
| `review_count` | Non-negative integer; numeric strings, floats and booleans rejected |
| `ingredient_completeness` | `complete`, `partial` or `unknown` |
| `sponsorship` | `yes`, `no` or `unknown`; no inference from absent evidence |

Country/currency context on other fields is rejected; availability carries its
own country sequence. A retailer price and manufacturer ingredient list remain
separate observations with their own IDs, references, dates and versions.

### Explicit resolution and import handoff

`explicit-selection-v1` never chooses the newest observation or a preferred source
implicitly. Selected evidence must be verified, refer to the exact product and
field, and agree on the typed value. The operator may select one observation while
retaining conflicting alternatives as history. An unresolved resolution retains
its evidence but exposes no canonical value through `resolved_value(product_id,
field_name)`. Missing and selected-null facts also return null. Identity fields
cannot be unresolved when the product asserts their non-null value.

Selected non-null rating and review-count observations must come from one source
and snapshot for the exact variant. A missing count or rating stays unknown; it is
never borrowed from another source or variant to complete a pair.

Within an envelope, duplicate product/source/evidence IDs and duplicate
product/field resolution keys are errors, even when records look identical. One
exact identity tuple (brand, name, category, variant) cannot use two
product IDs. The operator must review ambiguous mappings; no fuzzy identity merge
is performed. The [storage repository](catalog-storage.md) now enforces immutable
identities/history across complete snapshots. The
[local JSON importer](catalog-import.md) now merges batches and reports rejected/unchanged
rows.

The initial importer handoff is whole-batch preflight rejection on invalid records,
with no writes before successful validation. Transactional snapshot writes,
identical-snapshot replay and recoverable migrations are available in the storage
repository. The [local JSON importer](catalog-import.md) adds per-row rejection reports,
repeat-import idempotency and explicit resolution-update handling for file batches.
Any future accepted-row import mode must be explicit and still preserve transactional
failure recovery and the last-valid catalog.

The CSV [intake templates](../data/README.md#intake-templates) remain collection aids,
not a parser or a separate source of truth. A future loader must explicitly map
their `value_json` into the typed `value` and `content_hash` into `content_version`,
and assemble required resolutions; it cannot infer missing source metadata.

## Verification and limits

[`test_requirements.py`](../tests/test_requirements.py) covers supported requests,
exact paise, invalid boundaries and sanitized diagnostics.
[`test_catalog_contracts.py`](../tests/test_catalog_contracts.py) covers typed facts,
unknowns, field provenance, snapshot compatibility, conflicts, identity/link errors,
UTC dates and serialization round-trips. All evidence is labeled synthetic and
stays in tests; it does not establish genuine product correctness or permission.

These models are now consumed by the [persistent repository](catalog-storage.md).
The [import command](catalog-import.md) consumes these contracts and storage.
Search, catalog UI, genuine seed and release acceptance remain pending. These
increments do not introduce later model/graph contracts or change the Proposed
status of the existing ADRs.
