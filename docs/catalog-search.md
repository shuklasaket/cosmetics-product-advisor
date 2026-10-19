# Catalog search and detail service

[US-016](https://github.com/shuklasaket/cosmetics-product-advisor/issues/16) adds
read-only, model-free Python queries for CAT-05/06/07 in
[PRD 01](requirements/01-catalog-and-search.md). [US-017](https://github.com/shuklasaket/cosmetics-product-advisor/issues/17)
adds the validated Streamlit request form, and [US-018](https://github.com/shuklasaket/cosmetics-product-advisor/issues/18)
wires it to ordered result entries and inspectable evidence details. Synthetic test
catalogs do not establish genuine seed or release acceptance.

## Streamlit form

The local app presents the supported sunscreen/moisturiser and skin-type choices,
fixed India/INR defaults, and a required maximum budget. Zero is valid; blank,
negative, non-numeric, non-finite, and sub-paise budgets show sanitized guidance
without dispatching a request. Correcting the value and resubmitting validates the
new request.

Ingredient exclusions accept one value per line. Texture and finish are optional.
These personal inputs are collected for later screening and do not affect catalog
eligibility yet. A successful submit hands an immutable `UserRequirements` instance
to the session-local result boundary; [US-018](https://github.com/shuklasaket/cosmetics-product-advisor/issues/18)
connects it to one model-free query. Clear resets the form widgets and deletes the
request, result, selected detail, error, and dispatch state. A new browser session
starts empty.

## Result and evidence display

A valid submit searches the configured SQLite database. Matching entries retain the
service's case-sensitive name-then-ID order and show product name, India price, and pack
size. **View details** opens the complete selected fact set for that product. The view
does not add a suitability score, recommendation, ingredient screening, or review
summary.

Every non-null detail fact includes the attribution and explicit UTC verification
timestamp from its selected evidence. Verified HTTPS observation references become
fixed-label link buttons; `document:` references remain inert text. Product/source text
is rendered with native text elements rather than HTML or executable Markdown. A second
URL allowlist check prevents an unsafe scheme from becoming a link even if a malformed
value bypassed an earlier contract boundary.

Missing, selected-null, and unresolved values display as **Unknown**. Evidence-backed
unknown sponsorship remains visibly unknown; yes/no values retain their source state.
Skin-type values are labeled **Declared skin-type claims** and the detail view explains
that they are source statements, not safety or suitability findings.

Zero matches explain the active category, India, and INR ceiling and invite the shopper
to change the form. Missing, unreadable, incompatible, or invalid databases clear stale
results and show fixed restoration guidance without paths, SQL, source payloads, or
invented fallback products. Restoring a valid catalog and resubmitting retries the
query. The UI never creates, migrates, repairs, or imports the database.

## Consumer handoff

After [initializing storage](catalog-storage.md) and
[importing permitted evidence](catalog-import.md), construct the service with the
configured repository. This example defines a callable; it does not print or save
the shopper's request or results:

```python
from repositories.catalog import CatalogRepository
from schemas.requirements import UserRequirements
from schemas.settings import Settings
from services.catalog_search import CatalogSearchService

service = CatalogSearchService(CatalogRepository(Settings().database_path))


def search_catalog(requirements: UserRequirements):
    return service.search(requirements)
```

`search(requirements: UserRequirements) -> CatalogSearchResult` revalidates the
[session-only request contract](catalog-contracts.md#shopper-requirements).
Invalid requests raise `pydantic.ValidationError` before database access; display
only `UserRequirements.validation_messages(error)`, never raw exception details.

The result contains:

- `status`: the computed value `matches` or `empty`.
- `filters`: `CatalogFilters` with exact `category`, `country`, `currency` and
  `budget_paise`, including when no products match. These are the active hard
  filters, not the full personal request.
- `catalog`: a validated `CatalogEnvelope` containing matching products in display
  order, all their observations/current resolutions, and the sources referenced
  by those observations. An empty match has four empty collections.

`detail(product_id: str) -> CatalogEnvelope | None` validates the stable,
case-sensitive ID through `CatalogDetailQuery` before database access. It returns
one product and its complete field evidence/history, or `None` for an absent ID.
It works independently of a previous search, including for an over-budget product.
Invalid IDs raise `ValidationError`; display only
`CatalogDetailQuery.validation_messages(error)`.

Both operations raise `CatalogUnavailableError` with fixed recovery instructions
when the catalog is missing, inaccessible, corrupt, incompatible or invalid.
Display its message without exception context. Unavailability is distinct from
`empty` and from an absent detail ID. Check the configured file, initialize/import
only when appropriate, explicitly migrate a compatible older schema, or follow
the [backup/restore procedure](catalog-storage.md#back-up-and-restore).
Queries never create, migrate, repair or overwrite a database.

## Filtering and evidence rules

Category matches exactly. Availability requires an explicit `India` member in the
selected country sequence; null, missing, unresolved, empty or differently cased
availability cannot qualify. The selected India/INR price must be known and at or
below the integer-paise maximum. A known zero price qualifies at a zero budget;
unknown price never acts as zero. Historical observations do not become fallback
facts. Multiple agreeing selected observations produce one product.

Ordering is `name COLLATE BINARY`, then `product_id COLLATE BINARY`: case-sensitive
UTF-8 byte order without locale or case folding. For example, `Alpha` precedes
`Beta`, which precedes `alpha`. Tied names use the same rule on stable IDs.
Skin type, declared skin claims, preferences, exclusions, sponsorship and freshness
do not alter eligibility or order in this release. No suitability score is added;
source ratings remain descriptive facts with their explicit scale.

Use `catalog.resolved_value(product_id, field_name)` for the canonical fact.
Missing, selected-null and unresolved values remain `None`. Inspect resolutions,
observations and source records for evidence IDs, original references, dates,
versions, permission metadata and conflicting history. Never render a historical
alternative as the selected value or execute source HTML. A returned subset is a
read result, not a replacement snapshot for `save`; retain the complete catalog
when preparing an import/update.

## Storage and privacy

The repository exposes `search(CatalogFilters) -> CatalogEnvelope` and
`detail(str) -> CatalogEnvelope` (an empty envelope for an absent ID).
It opens one read-only connection and explicit transaction, validates the entire
catalog and evidence links, then executes a parameterized query in that same
snapshot. Even invalid evidence outside the requested category fails the query;
it cannot masquerade as no matches. A concurrent import can affect the next query,
but cannot mix eligibility from one snapshot with detail facts from another.

Price comparison uses a connection-local Python integer function over JSON integer
text and a bound text ceiling. It preserves exact paise even beyond SQLite's signed
64-bit range, without rounding through REAL. No schema, index, migration, dependency
or configuration change is needed. Full-snapshot validation is deliberate for the
small local catalog; it is not a large-catalog performance claim.

Requests, active filters, results, and the selected detail remain transient. The form
and result controller keep them only in Streamlit session state; the service keeps no
request or result state. Neither adds logs, persistent/shared caches, URLs, exports or
database writes. The form does not use query parameters. Model representations omit
active filters; explicit serialization still contains the budget and must remain in
session memory. A new valid submit clears the prior result/detail before querying, and
unavailability or Clear removes stale results.

## Verification

Run `uv run --frozen pytest tests/test_app.py tests/test_catalog_search.py -q` for
synthetic AppTest and temporary-SQLite checks covering the form-to-search workflow,
ordered entries, evidence details, unknown/sponsorship/claim wording, inert external
text, empty/retry and unavailable/restore behavior, both category ceilings,
unknown/unresolved/history handling, exact large integers, sanitized diagnostics,
read-only privacy, and a concurrent WAL writer. `make check` includes these tests.
Genuine seed and full offline release evidence remain separate.

Implementation references: [Python 3.12 SQLite bindings and transactions](https://docs.python.org/3.12/library/sqlite3.html),
[SQLite JSON operators](https://www.sqlite.org/json1.html), and
[SQLite collation](https://www.sqlite.org/datatype3.html#collation).
