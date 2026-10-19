# Load a local catalog batch

The [PRD 01](requirements/01-catalog-and-search.md) importer reads permitted public
evidence from a local UTF-8 JSON file and commits it to the
[SQLite catalog](catalog-storage.md). It performs no source fetching or scraping.
The [search/detail service](catalog-search.md) and Streamlit UI read imported evidence.
The reviewed demo seed is supplied separately and loaded explicitly; application
startup never imports or fetches products. See the [release runbook](catalog-release.md).

## Prepare and run

1. Run `make setup` and explicitly initialize the database using the
   [storage initialization guide](catalog-storage.md#initialize-and-inspect).
2. Prepare a `catalog-v1` JSON envelope under the
   [catalog contract](catalog-contracts.md#versioned-evidence-envelope):
   `contract_version`, `products`, `sources`, `observations`, and `resolutions`.
   All four collections are required arrays. The header-only
   [CSV intake templates](../data/README.md#intake-templates) remain collection
   aids; this command does not parse CSV or infer missing resolutions.
3. Verify source permissions and exact formulation/pack mappings. Stop other
   catalog writers and run from the repository root:

```sh
uv run --frozen python -m scripts.import_catalog data/local/approved-batch.json
```

The repository's reviewed non-commercial demo seed is available at
`data/seed/catalog-v1.json`; its [source policy and attribution](../data/seed/README.md)
must travel with it. Replace the example path only when importing another permitted
evidence file. The default database is `Settings.database_path`
(`database/advisor.db`, overridable with `ADVISOR_DATABASE_PATH`). To select an
existing initialized file explicitly:

```sh
uv run --frozen python -m scripts.import_catalog data/local/approved-batch.json \
  --database database/advisor.db
```

Settings must still validate when `--database` is supplied. Use `--help` for the
command syntax. The batch must be a local regular file of at most 5 MiB. Malformed
UTF-8/JSON, duplicate object members, non-finite JSON constants, unsupported versions,
extra fields and invalid values are refused. Decimal JSON numbers retain their exact
text for rating validation; non-integer paise/counts remain invalid. No database is
created or migrated implicitly, including when input validation fails.

## Source approval and provenance

Each batch must be self-contained: include every product and source registration
referenced by its observations and every observation referenced by its resolutions.
Use complete source metadata: original reference, access/reuse conditions,
permission reference, attribution, last-checked UTC timestamp and explicit `enabled`.
Observations must use enabled sources. `enabled: true` records the operator's
approval; the command validates metadata and links, not legal permission itself.
Establish actual permitted reuse before loading genuine evidence.

Each non-null identity needs matching selected evidence. Every observed field needs
an explicit selected or unresolved resolution. Verification/source-snapshot rules
remain those of catalog-v1. A retailer price and manufacturer ingredients retain
separate evidence IDs, original references, retrieval/verification dates and versions.
Missing/null facts remain unknown; the importer fills no gaps from inferred data.

## Repeated batches and conflicts

- Duplicate product/source/evidence IDs or product/field resolution keys within a
  batch reject the entire batch, even when their payloads are equal.
- Across imports, an equal existing immutable record is reused. New products,
  source registrations and observations append; the merged catalog retains prior
  records omitted from the incoming batch.
- A changed payload under an existing product/source/evidence ID rejects the batch.
  Add a new evidence/source ID for changed facts/metadata. Identity corrections
  require a separately reviewed mapping policy; no silent variant remapping occurs.
- Existing resolutions remain unless explicitly supplied. Changing a supplied
  stored resolution requires reviewing the evidence and passing
  `--update-resolutions`. New field resolutions need no replacement flag. Conflicting
  observations can coexist as retained history, but incoming resolutions must choose
  verified agreeing evidence or explicitly mark the field unresolved.

To apply reviewed resolution changes:

```sh
uv run --frozen python -m scripts.import_catalog data/local/reviewed-batch.json \
  --update-resolutions
```

The flag authorizes resolution replacements in this invocation, including changes
from unresolved to selected. It never authorizes rewriting historical observations.
Replaying a fully equal batch reports `unchanged` without writing. Replaying an older
selection after a newer import rejects by default, rather than undoing it silently.
A second product ID for an existing exact variant also rejects after merge.

The complete merged envelope validates before a write. The repository compares the
previously read snapshot with current state inside `BEGIN IMMEDIATE`; a competing
writer causes refusal and requires reloading/retrying. Transaction failure rolls back
inserted records and resolution changes together.

## Read the report

The command prints one JSON summary to stdout and creates no report/log file. Exit
code `0` means `committed` or `unchanged`; exit code `1` means `rejected` or `failed`.
The summary contains:

| Field | Meaning |
| --- | --- |
| `status` / `committed` | Actual result and whether this invocation committed a transaction |
| `accepted` | Incoming rows accepted on success, including unchanged rows; zero on failure |
| `rejected` | All recognized incoming rows withheld on rejection/failure, not only the invalid ones |
| `unchanged` | Accepted rows identical to stored rows (a subset of `accepted`) |
| `updated_resolutions` | Existing resolutions explicitly replaced; new keys are not replacements |
| `unresolved` | Total explicitly unresolved fields in the resulting catalog on success |
| `rows_known` | False when reading/parsing fails; numeric counts are then zero placeholders |
| `issues` | Safe row identifiers and fixed corrective messages; empty on success |

A row identifier such as `observations:7` means the seventh entry (one-based) of
that JSON array; it does not echo an untrusted evidence ID. `batch`, `command`, and
`configuration` identify broader errors. Every recognized withheld row receives a
message: its validation/conflict reason, or a notice that the whole batch was withheld.
Batch-level relationship errors ask the operator to review IDs, variants, explicit
resolutions and compatible verified snapshots. All row counts refer to records across
the four recognized arrays, rather than product counts or JSON line numbers.

Diagnostics omit rejected values, source text, arbitrary extra-field names, IDs,
paths, raw SQL and exception payloads. Do not put shopper budgets, exclusions,
medical details or conversations into evidence files or source metadata. JSON
summaries are safe structural diagnostics, not copies of the input.

## Correct and retry

For rejected input, inspect the local array entry named in the report, correct its
identity/value/permission/resolution data, and retry the complete batch. Whole-batch
preflight rejection means no accepted-row mode or partial commit. For unavailable,
invalid or unsupported databases, check configuration and follow the
[backup and restore guide](catalog-storage.md#back-up-and-restore). Do not replace a
last-valid database merely to bypass an import error. After a concurrent update,
reload the latest catalog before rebuilding/retrying the batch.

Synthetic integration tests cover generic import and rollback behavior. Separate
US-019 acceptance tests validate the reviewed starter seed's category counts,
provenance boundary, repeat import and India/INR search behavior. These tests do not
grant broader rights than the documented source policy. Generated databases, backups
and local evidence files remain uncommitted under the [data policy](../data/README.md).

API references: [Python JSON decoding](https://docs.python.org/3.12/library/json.html),
[Pydantic validation errors](https://docs.pydantic.dev/latest/errors/errors/).
