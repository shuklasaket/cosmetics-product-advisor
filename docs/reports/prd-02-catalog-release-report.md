# PRD 02 catalog release evidence

Observed on 26 November 2026 in the target Apple-silicon Mac workspace. This report
records release evidence for [US-035](https://github.com/shuklasaket/cosmetics-product-advisor/issues/35)
in PR #60; user review and merge remain pending.
It does not make product-safety, regulatory-compliance, or source-permission claims
beyond the recorded source policy and fact-level provenance.

## Environment and startup

| Check | Observed result |
| --- | --- |
| Platform | macOS 26.5.2, arm64 |
| `uv` | 0.13.1 |
| Pinned Python through `uv` | 3.12.15 |
| Streamlit | 1.66.0 |
| SQLite | 3.53.1 |
| Bind address | `127.0.0.1:8508` |
| First launch health | `ok`; root response HTTP 200 |
| Restart health | `ok` |
| Post-restart PRD 02 verifier | `passed` |

The local workspace used the frozen lock. The app loaded the reviewed seed and
payload-free PRD 02 evidence into a fresh SQLite database before startup. No external
source fetch, LLM, account, credential, image, review text, or raw API payload was
used during this check.

## Observed release workflow

Fresh import reported `committed` for the catalog (537 accepted rows, zero rejected,
zero unresolved) and for the five reviewed release-evidence mappings/outcomes. The
read-only PRD 01 verifier passed for 25 products. The strict PRD 02 verifier passed
with 12 sunscreens, 13 moisturisers, five reviewed mappings, five accepted outcomes,
the approved 7-day price/availability and 30-day other-fact limits, and no failures.

The original ten products retain their October evidence alongside 72 newly selected
observations and 20 dated source records. The selected product identity for Mamaearth
Vitamin C Daily Glow 50 g now states SPF 50 PA++++ after the maintainer confirmed the
current official-page label corrects the same exact variant. Its earlier PA+++ record
remains available as immutable history. A pre-correction database rejects this changed
product identity even with `--update-resolutions`; its prior observations and selected
PA+++ identity remain readable. The documented recovery path is to create a fresh
database from the corrected seed rather than overwriting the last-valid catalog.

## Acceptance mapping

| Criterion | Evidence |
| --- | --- |
| AC-1 — permitted genuine evidence | 25 reviewed India variants; source policy and exact-pack review in `data/seed/README.md`; `tests/test_prd02_genuine_catalog.py`. |
| AC-2 — real retrieval outcomes | Five reviewed Open Beauty Facts mappings and accepted payload-free outcomes; `tests/test_prd02_release_evidence.py`; passed PRD 02 verifier. |
| AC-3 — provenance, conflict, freshness, UI | Fresh selected evidence for all original products, including the corrected Mamaearth PA rating; `tests/test_prd02_release.py`; existing Streamlit AppTests and the two loopback startup checks. |
| AC-4 — recovery matrix | Existing deterministic failure/replay/offline suite in `make check`; pre-correction import rejection preserves the previous catalog in `tests/test_prd02_release.py`; restart retains the fresh catalog and passes the read-only verifier. |

`make check` passed with 399 tests, Ruff, mypy, documentation, skill inventory and
dependency-export checks. GitHub CI validates the same quality suite for the pull
request's latest revision.
