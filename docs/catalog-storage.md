# Local catalog storage and recovery

[PRD 01](requirements/01-catalog-and-search.md) stores validated public catalog
records through [`CatalogRepository`](../repositories/catalog.py). This delivers
storage. The [local importer](catalog-import.md),
[search/detail service](catalog-search.md), genuine seed and Streamlit UI consume it.
The application deliberately does not open a writable database or create storage at
startup; follow the [release runbook](catalog-release.md) for explicit setup.
Do not store shopper requests, budgets, exclusions, medical details, or conversations.

## Initialize and inspect

Run from the repository root after `make setup`, with the application stopped:

```sh
uv run --frozen python - <<'PY'
from repositories.catalog import CatalogRepository, migrate
from schemas.settings import Settings

path = Settings().database_path
backup = migrate(path)
catalog = CatalogRepository(path).read()
print(f"Schema ready; products: {len(catalog.products)}; upgrade backup created: {backup is not None}")
PY
```

`ADVISOR_DATABASE_PATH` defaults to `database/advisor.db`; existing Settings and
`.env.example` paths remain supported. Only explicit `migrate` creates parent
folders/a missing database. Reads use SQLite URI `mode=ro`; writes require an
existing database (`mode=rw`). Missing, inaccessible, corrupt, unsupported, or
inconsistent storage raises a fixed `CatalogStorageError`. Display its message
without logging exception context, SQL, or record payloads.

Schema v1 uses `PRAGMA application_id = 0x43504131` and `PRAGMA user_version = 1`.
Only an empty, unversioned database can be initialized. Nonempty unversioned,
foreign, or newer databases are refused without schema/data changes. There is no
implicit downgrade or overwrite. Repeated migration of a valid current schema is
a no-op. Migrations are ordered statement tuples in
[`migrations.py`](../repositories/migrations.py), with DDL and version changes
inside an explicit transaction; do not use `executescript` (implicit transaction
behavior can break atomic upgrades). SQLite JSON functions and generated columns
are required and exercised by the pinned Python environment and integration tests.

## Repository handoff

`save(envelope: CatalogEnvelope)` takes a **complete** catalog-v1 snapshot,
revalidates serialization, and writes under `BEGIN IMMEDIATE`. `read()` reopens a
consistent read transaction and returns a validated envelope, including all
observations and current explicit resolutions. It checks SQLite integrity, foreign
keys, and correspondence between resolution payloads and evidence-link rows.

Products, sources, and observations are immutable: retain existing IDs and exact
payloads; append new records rather than rewriting or deleting history. A source
metadata change currently requires a new source ID (retain the old registration).
An identity correction requires a separately reviewed future migration/policy;
this API does not silently remap a stable product. A changed fact adds an observation
with a new evidence ID and updates the field's explicit resolution. Conflicting
observations remain stored even after selecting one. An unresolved, missing, or
selected-null fact reads as unknown through `CatalogEnvelope.resolved_value`.
Unresolved identity cannot contradict a non-null product identity.

Identical snapshot replay makes no duplicate products/observations. The caller
must retain historical products/sources/observations when assembling a later
snapshot; partial batches are not accepted as replacement catalogs. The
[local importer](catalog-import.md) owns file parsing, batch merging,
cross-import idempotency reporting and operator-facing rejected-row diagnostics.
It passes `expected=current_snapshot` to `save` so the repository refuses a stale
writer inside its transaction; callers building snapshots from reads should do the
same. Omitting `expected` preserves the direct complete-snapshot API.

Tables retain canonical JSON payloads to preserve exact decimal strings, UTC
provenance and explicit nulls. Generated keys, unique variant identities, composite
foreign keys, enum/type/range checks and immutable-history triggers add database
constraints. The `resolution_evidence` relation prevents cross-product/field links.
Full typed validation and source/snapshot/identity consistency remain enforced by
catalog-v1 at the repository boundary; direct SQL is not a supported writer API.
SQLite rating range checks use numeric casts as defense in depth; exact decimal
and finite-value checks remain Python's responsibility. No automatic fact selection,
source preference, price/rating mixing, or suitability ranking occurs here.

Any failed validation/write rolls back the transaction, including inserted history
and replaced resolutions. Connections always close and roll back unfinished work.
Foreign keys are enabled on every connection. No database/source data enters logs.

## Back up and restore

Stop all application/import processes before migration, backup, or restoration.
A forward upgrade first validates the old catalog and uses SQLite's backup API
(including committed journal contents) to write a unique backup under
`DATABASE_NAME.backups/vVERSION-UUID.db` beside the database. A backup error stops
the upgrade. Initial empty initialization has no prior catalog to back up. Failed
DDL/version changes roll back; the pre-upgrade backup remains available. Do not
remove the database or journals after an error; first inspect using the matching
application version and restore a known valid backup if necessary.

For a manual backup:

```sh
uv run --frozen python - <<'PY'
from repositories.catalog import CatalogRepository
from schemas.settings import Settings

backup = CatalogRepository(Settings().database_path).backup()
print(backup)  # Local operator path only; do not publish paths or catalog contents.
PY
```

Restore into a **new** path; `restore` refuses to overwrite any existing file:

```sh
uv run --frozen python - <<'PY'
from pathlib import Path
from repositories.catalog import CatalogRepository, restore

# Replace with the actual backup path printed above. Never guess the backup UUID.
backup = Path("database/advisor.db.backups/v1-ACTUAL_UUID.db")
destination = Path("database/recovered.db")
restore(backup, destination)
print(f"Restored products: {len(CatalogRepository(destination).read().products)}")
PY
```

Verify the restored catalog with the matching application version, then set
`ADVISOR_DATABASE_PATH=database/recovered.db` in your local `.env` and restart.
Keep the original database and backup until recovery is verified. Older backups
may require the matching older application before a forward migration. A failed
restore can leave a partial new destination; retain the original/backup and choose
another unused path after correcting the cause. Never restore by copying over a
live database or deleting its WAL/journal files.

Databases, journals, and `*.backups/` directories are ignored. Do not commit or
redistribute generated files; genuine evidence and source permission remain separate
release requirements under the [data policy](../data/README.md). The US-014 tests use
only synthetic evidence and temporary SQLite files; injected v2 migrations test the
upgrade mechanism without shipping an invented production v2 schema.

Implementation references: [Python 3.12 SQLite transaction control and backup API](https://docs.python.org/3.12/library/sqlite3.html).
