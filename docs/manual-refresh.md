# Manual refresh and operator status

[US-037](https://github.com/shuklasaket/cosmetics-product-advisor/issues/37) connects
PRD 02's approved source, reviewed mapping, transactional commit, and evidence policy
to the local Streamlit app. No source is enabled or mapping supplied by this change.

## Prepare an approved product

1. Stop the app and importer, back up the catalog, and follow the
   [schema-v3 migration procedure](catalog-storage.md). The UI never migrates or
   creates storage.
2. Review source access/reuse conditions and attribution. Register the same enabled
   Open Beauty Facts dataset source in the catalog and
   [approved-source registry](approved-source-registry.md).
3. Review the exact barcode, brand, name, pack, and ingredient declaration against the
   existing stable formulation variant. Follow the
   [reviewed mapping and commit handoff](approved-source-registry.md#reviewed-variant-and-refresh-commit-handoff)
   outside the browser to persist the first successful reviewed mapping. Do not infer
   mappings from similar names or import synthetic test mappings as genuine evidence.
4. Start the local app, search the catalog, and choose **View details**. The refresh
   button remains disabled if the approved source, current schema, or unique reviewed
   mapping is unavailable. Multiple external IDs for one product need operator review;
   the app will not guess which barcode to request.

## Refresh and interpret the result

**Refresh product** runs one synchronous lookup for the selected mapped product. The
spinner reports work in progress, with up to three attempts and the adapter's
10-second per-attempt timeout. Opening details, changing search inputs, and opening
**Show operator status** never trigger source requests. There is no batch, schedule,
background job, arbitrary URL input, or browser mapping editor.

The result distinguishes source execution from storage:

| Outcome | Meaning and next action |
| --- | --- |
| `fetched` | Validated candidate fields were retrieved. Check storage status; retrieval alone does not mean evidence was saved or verified. |
| `cached` | Public candidates were reused from this browser session's fresh adapter cache; no new retrieval date is invented. |
| `partial` | Some allowlisted fields are missing/rejected. Missing identity/formulation evidence requires review and is not committed. |
| `missing` | The source did not find the mapped product. Check its barcode mapping. |
| `invalid` | Payload validation failed. Keep dated local evidence and investigate the source contract. |
| `unavailable` | Check the safe error code (`timeout`, `rate_limited`, etc.); retry later or check approved configuration. |
| `stale` | A failed request retained previously cached candidates with their original dates. Review dated local evidence before relying on it. |

Storage reports `committed` or `unchanged` separately. `review_required`, `rejected`,
or `failed` means the attempt was not saved; check mapping or storage before retrying.
Uncommitted summaries remain only in the current browser session and are labeled as
such. Durable outcomes survive restart. The UI compares completion times to show the
latest session or stored outcome, including safe errors, cache state, attempts, and
actual retrieval/completion dates. An error never becomes a successful refresh merely
because its failure outcome was stored.

The adapter's public candidate cache lasts for the session (30-day freshness window),
resets when the source registration changes, and contains no raw HTTP payload or
shopper requirements. Owned HTTP clients close after each request. Source approval
and the product mapping are checked again when the button is used; the repository
rechecks the source and exact mapping in its write transaction.

## Evidence and operator attention

Product details retain the explicitly selected value and its original verification
date. They show policy freshness and conflict counts, source attribution/references,
retrieval dates, and validation state. Additional evidence appears under an expander;
unverified candidates are labeled **Evidence date (unverified)**. A fresh observation
is not necessarily verified or suitable. The policy's proposed fallback does not
replace an unresolved displayed fact, which remains **Unknown**.

**Show operator status** reads the whole public catalog independently of search filters.
For every stable product ID it reports fresh/stale/conflicting facts, unknown or absent
facts, unresolved recorded facts, latest refresh/error, and recovery guidance. Conflict
counts follow the deterministic policy; ambiguous unresolved selections are also
counted separately. Review stale, missing, conflicting, or unverified observations
against permitted sources. Use the existing manual import/review process for explicit
resolution changes; refresh does not resolve conflicts or promote candidates.

Timeouts, rate limits, malformed/missing payloads, and rejected commits leave selected
local facts browsable. For storage errors, stop writers and use the
[backup/restore procedure](catalog-storage.md#back-up-and-restore). To disable network
refresh, disable the approved registration; browsing remains available. Rolling back
the UI does not delete evidence, mappings, or outcomes; use a schema-v3-compatible
application or restore the corresponding pre-migration backup when downgrading further.

## Verification boundary

`uv run --frozen pytest tests/test_refresh_ui.py tests/test_open_beauty_facts.py -q`
uses synthetic public evidence, real temporary SQLite storage, AppTest, and mocked HTTP
transport with routine outbound sockets disabled. It covers explicit action, cached and
stale paths, failures, storage rejection, approval revocation, provenance/conflicts,
operator recovery, and payload/private-input exclusion. These checks do not satisfy
[US-035's genuine catalog and live release evidence](https://github.com/shuklasaket/cosmetics-product-advisor/issues/35).
