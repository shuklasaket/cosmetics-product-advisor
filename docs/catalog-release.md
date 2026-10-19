# Run and verify the offline catalog release

This is the operator runbook for the [PRD 01](requirements/01-catalog-and-search.md)
local demo. It uses only the reviewed India-online seed, SQLite and Streamlit. No LLM,
hosted service, source fetch, account or credential is started by these commands.

## Prepare a Mac

Install Git and `uv`, clone the repository, and run these commands from its root. The
supported interpreter is the version in [`.python-version`](../.python-version); `uv`
selects it even when the Mac's system `python3` is older.

```sh
uv sync --locked
uv run --frozen python --version
uv run --frozen streamlit version
```

The lock file supplies exact dependency resolutions. For the compatibility-only pip
path, create a Python 3.12 environment and install `requirements.txt` with
`python -m pip install --require-hashes -r requirements.txt`.

## Create and load the local catalog

The application deliberately does not create, migrate or seed storage during startup.
With the app stopped, initialize once and load the reviewed non-commercial demo seed:

```sh
uv run --frozen python -c 'from repositories.catalog import migrate; from schemas.settings import Settings; migrate(Settings().database_path)'
uv run --frozen python -m scripts.import_catalog data/seed/catalog-v1.json
uv run --frozen python -m scripts.verify_catalog_release database/advisor.db
```

The importer must report `committed` on a new database or `unchanged` on an identical
replay. The verifier is read-only. It reports `passed` only when the database contains
the reviewed ten-product release, both required searches return five products, and the
Minimalist sunscreen retains separate retailer-price and manufacturer-ingredient
evidence with verification dates. Its output contains catalog identifiers and software
versions, never shopper input or arbitrary source text.

If `ADVISOR_DATABASE_PATH` selects another location, use that same path as the verifier
argument. Do not commit the generated database or its backups.

## Launch, stop and restart

```sh
uv run --frozen streamlit run app.py
```

Open `http://127.0.0.1:8501`. The checked-in configuration binds only to loopback.
Search for sunscreen at ₹800, then moisturiser at ₹600. Open **Minimalist Light Fluid
SPF 50** and inspect each fact's attribution and verification time. Its India price and
ingredient declaration must show different sources.

Press Ctrl+C, run the same launch command again, and repeat either search. The catalog
persists in SQLite; startup does not contact an LLM or external product source. Run the
read-only verifier again after the restart for a deterministic persistence check.

## Boundaries and recovery

The automated acceptance suite covers exact-ceiling inclusion, over-budget exclusion,
unknown India availability, zero and invalid budgets, unsupported countries, duplicate
input, empty results, missing/invalid databases, atomic import failure, migration
failure, backup/restore and post-restore search. Run it with:

```sh
uv run --frozen pytest tests/test_catalog_release.py tests/test_genuine_starter_catalog.py tests/test_app.py tests/test_catalog_search.py tests/test_catalog_import.py tests/test_catalog_repository.py -q
```

For an import rejection, correct the local batch and retry; the previous valid catalog
remains intact. For a missing, corrupt or incompatible database, stop the app and follow
the [validated backup/restore procedure](catalog-storage.md#back-up-and-restore), restore
into a new path, point `ADVISOR_DATABASE_PATH` to it, run the verifier, and restart.

See the [release evidence report](reports/prd-01-catalog-release-report.md) for the
observed target-Mac run and the exact acceptance mapping.
