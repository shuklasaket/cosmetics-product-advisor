# PRD 01 catalog release evidence

Observed on 20 October 2026 in the target Apple-silicon Mac workspace. This report is
release evidence for [US-020](https://github.com/shuklasaket/cosmetics-product-advisor/issues/20),
not a product-safety evaluation or permission to sell the catalog.

## Environment and startup

| Check | Observed result |
| --- | --- |
| Platform | macOS 26.5.2, arm64 |
| Pinned Python through uv | 3.12.15 |
| uv | 0.13.1 |
| Streamlit | 1.66.0 |
| SQLite | 3.53.1 |
| Bind address | `127.0.0.1:8501` |
| First launch health | `ok` |
| Restart health | `ok` |
| Post-restart catalog verifier | `passed`, 10 products |

The existing workspace environment was synchronized from the frozen lock and used for
the observed run; it was not a newly provisioned physical Mac. Reproducibility from a
clean clone is defined by the pinned setup and is also exercised by GitHub CI. No LLM,
hosted inference, source fetch or credentials were used. The local system `python3` is
older than the supported version; all acceptance commands used `uv run --frozen`.

## Genuine catalog workflow

Initialization created schema v1. Importing `data/seed/catalog-v1.json` reported
`committed`, 174 accepted rows, zero rejected rows and zero unresolved resolutions.
The release verifier then observed:

- 10 products total;
- 5 sunscreen results at an inclusive ₹800 ceiling;
- 5 moisturiser results at an inclusive ₹600 ceiling;
- `minimalist-light-fluid-spf50-50ml` price from
  `retailer:minimalist-light-fluid-spf50-50ml`;
- the same product's ingredients from
  `maker:minimalist-light-fluid-spf50-50ml`; and
- both selected observations verified at `2026-10-19T14:39:00Z`.

The genuine-data AppTest opens that product from the five-result sunscreen UI and
asserts that both distinct source attributions and both dates are visible. The verifier
reads the persisted database without changing it and passed again after the server was
stopped and restarted.

## Acceptance mapping

| Criterion | Evidence |
| --- | --- |
| AC-1 launch and restart | Frozen setup and load commands in the runbook; two loopback health checks; post-restart read-only verifier; versions above. |
| AC-2 discovery and provenance | `tests/test_catalog_release.py` genuine AppTest and verifier; `tests/test_genuine_starter_catalog.py` seed/replay checks. |
| AC-3 boundaries and validation | `tests/test_app.py`, `tests/test_catalog_search.py`, and `tests/test_requirements.py` cover ceiling, over-budget, unknown availability, zero/invalid/non-finite budget, unsupported country and explanatory empty state. |
| AC-4 failure recovery | `tests/test_catalog_import.py` and `tests/test_catalog_repository.py` cover duplicates, atomic import/migration failure and validated restore; `tests/test_catalog_release.py` proves the restored genuine catalog remains searchable. |

The maintainer replaced the deferred five-person timing pilot with five deterministic
automated journeys in [US-030](https://github.com/shuklasaket/cosmetics-product-advisor/issues/30).
They cover representative sunscreen and moisturiser searches, session-only optional inputs,
matching-product discovery, detail inspection and visible source evidence. These journeys are an
automated usability proxy; they do not measure human comprehension or task completion time.
