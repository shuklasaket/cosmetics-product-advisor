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
