# Approved retrieval sources and refresh outcomes

[US-034](https://github.com/shuklasaket/cosmetics-product-advisor/issues/34)
introduces the PRD 02 contract boundary before any live HTTP adapter is enabled.
It does not approve a source, fetch external data, or treat a successful HTTP response
as verified product evidence.

## Registry boundary

`SourceRegistry` contains complete `ApprovedSource` records with a stable source ID,
source type, HTTPS endpoint prefixes, separately reviewed redirect origins, attribution,
access and reuse conditions, permission reference, check date, enabled state, and
external-ID namespace. Missing metadata, duplicate identities/destinations, credentials,
HTTP URLs, fragments, traversal segments, query-bearing endpoint prefixes, and non-origin
redirect entries fail validation.

Registrations should remain disabled until the operator/data reviewer confirms the exact
endpoint contract, access/reuse terms, attribution, stable external identifier, and
redirect behavior. Enabling one registration authorizes only its configured endpoint
path prefixes. Redirects are checked again against the registration's explicit origin
allowlist. Retrieved text, model output, shopper input, and arbitrary URLs never extend
that allowlist.

Call `authorize_destination` immediately before every initial request and redirect,
before handing the URL to an HTTP client. Its failure is deliberately sanitized and does
not echo the rejected destination.

## Persistence and recovery

Schema v2 adds `approved_sources` beside the catalog-v1 evidence tables. Run the normal
[`migrate`](catalog-storage.md#initialize-and-inspect) path with the app and importer
stopped. Upgrading a valid v1 database creates a validated v1 backup before the v2 DDL;
initializing an empty database creates v2 directly.

`SourceRegistryRepository.replace` revalidates the complete registry and replaces it in
one `BEGIN IMMEDIATE` transaction. SQL, validation, or verification failure rolls back
the replacement and leaves the last-valid registry intact. The repository returns only
fixed diagnostics; registry payloads and local paths do not enter errors or logs. Restore
the pre-upgrade backup into a new path with the matching older application if recovery is
required, then retry the forward migration after correcting the cause.

The migrated registry starts empty; no approved source registration is shipped by this
story. A later connector story supplies a reviewed registration and live adapter after
source approval is recorded.

## Refresh-result boundary

`RefreshResult` reports one of `fetched`, `cached`, `missing`, `stale`, `partial`,
`invalid`, or `unavailable`. It always identifies the source, external ID, mapped catalog
product, cache state, bounded attempt count, start/completion times, evidence IDs, and a
fixed sanitized error code where applicable. Fetched results include the actual retrieval
time. Cached and stale outcomes must declare matching cache states.

The contract cannot contain a raw response body. Adapters validate source payloads and
write accepted observations through the evidence boundary; callers receive evidence IDs
and status, not untrusted source content disguised as a trusted tool instruction.

## Open Beauty Facts product lookup

[US-036](https://github.com/shuklasaket/cosmetics-product-advisor/issues/36) adds the
bounded, read-only `OpenBeautyFactsClient` adapter. It accepts only an enabled
`open-beauty-facts` dataset registration with the
`open-beauty-facts-barcode` namespace and exactly one approved
`https://world.openbeautyfacts.org/api/v3/product/` endpoint. Redirects are disabled;
images and any URL supplied by returned content are never fetched. The client identifies
itself with a User-Agent and calls only `{barcode}.json` after
`authorize_destination` succeeds.

The caller supplies a previously reviewed exact `product_id`/barcode match. This story
does not persist or infer a mapping: [US-039](https://github.com/shuklasaket/cosmetics-product-advisor/issues/39)
owns transactional mapping and evidence commits. A valid response yields unverified,
allowlisted candidates for brand, name, pack size, and ingredient declaration, each with
the source ID, exact original URL, retrieval time, content hash, and deterministic
candidate ID. Missing and rejected fields remain explicit. The raw response body is
neither returned nor cached.

Each request is limited to 10 seconds. Timeouts, transport failures, HTTP 408, 429 and
5xx responses receive at most two retries (three attempts total); a longer `Retry-After`
ends/defer the refresh instead of sleeping through it. Not-found and invalid responses
do not retry. Valid returned or partial candidates use an in-memory 30-day cache; a
fresh hit reports `cached`, while a failed refresh can return only a clearly `stale`
cached candidate set. The cache is public evidence only and is not persisted.

The registration must record the source's ODbL/reuse conditions and attribution to Open
Beauty Facts contributors. This adapter excludes product images, which have separate
licensing conditions. The later PRD-02 release evidence still needs reviewed exact
catalog mappings and permitted live outcomes; its recorded/synthetic adapter tests do
not establish those genuine-data checks.
