# Development foundation completion report

**Date:** 17 October 2026

**Status:** Foundation implemented and verified locally.

**Scope:** Prepare the repository for incremental PRD implementation and provide a runnable development preview. No user stories were created.

## Outcome

The repository now has a reproducible Python environment, a minimal Streamlit entry point, validated configuration, automated quality checks, a GitHub Actions workflow, and contribution/data guidance. The preview starts without a catalog, model, external source, or credentials.

This completes the development foundation. PRD 01 remains to be implemented: the preview does not provide catalog search, import data, create a database, or make product recommendations.

## Changes and reasons

| Area | Files | What changed and why |
| --- | --- | --- |
| Reproducible environment | [pyproject.toml](../../pyproject.toml), [uv.lock](../../uv.lock), [.python-version](../../.python-version), [requirements.txt](../../requirements.txt), [requirements-dev.txt](../../requirements-dev.txt) | Selected Python 3.12.15 and uv 0.13.1. Locked runtime/development dependencies; generated hashed pip compatibility exports from the same lockfile to prevent divergent dependency lists. |
| Runnable preview | [app.py](../../app.py), [.streamlit/config.toml](../../.streamlit/config.toml) | Added an honest development status page. Bound the server to loopback and disabled Streamlit usage statistics for the local application. |
| Configuration | [schemas/settings.py](../../schemas/settings.py), [.env.example](../../.env.example) | Added typed settings, documented path overrides, rejected blank paths and unsupported hosted inference, and kept configuration values out of validation errors shown to users. Loading settings creates no runtime files. |
| Repeatable commands | [Makefile](../../Makefile) | Added setup, run, formatting, linting, typing, tests, documentation checks, and dependency-export commands for a consistent local/CI workflow. |
| Automated verification | [tests/](../../tests/), [scripts/check_docs.py](../../scripts/check_docs.py), [scripts/check_exports.py](../../scripts/check_exports.py) | Covered preview startup, invalid configuration, environment precedence, and documentation failures. Added checks for repository links, draw.io structure, and exports matching the lockfile. |
| CI and review | [ci.yml](../../.github/workflows/ci.yml), [Dependabot configuration](../../.github/dependabot.yml), [PR template](../../.github/PULL_REQUEST_TEMPLATE.md), [.pre-commit-config.yaml](../../.pre-commit-config.yaml) | Configured the same checks for GitHub, pinned action revisions with read-only permissions, and added review prompts and optional local hooks. Dependabot proposes monthly action updates. |
| Repository hygiene | [.gitignore](../../.gitignore), [.gitattributes](../../.gitattributes), [.editorconfig](../../.editorconfig) | Excluded local environments, secrets, runtime data, logs, exports, and model files. Standardized text encoding, whitespace, and line endings. These files belong in the working tree; Git manages `.git` itself. |
| Data preparation | [data/README.md](../../data/README.md), [CSV templates](../../data/templates/) | Documented provenance, source permissions, variant matching, and separation of synthetic fixtures from genuine evidence. Added header-only collection templates; no product records were fabricated. |
| Implementation guidance | [README](../../README.md), [CONTRIBUTING](../../CONTRIBUTING.md), [development guide](../development.md), [ADR-0002](../adr/0002-python-and-development-tooling.md) | Documented setup, completion criteria, code boundaries, dependency updates, and the tooling decision. Updated the technical requirements and ADR index, and replaced a machine-specific source-document link with portable attribution. |

The environment was installed in the ignored project `.venv`. No global Python installation was changed. Database, model, graph, and retrieval dependencies will be introduced when the relevant PRD needs them.

## Verification results

Verified on the development Mac with Python 3.12.15 and uv 0.13.1.

| Check | Result |
| --- | --- |
| Locked environment installation | Passed with `uv sync --locked --no-python-downloads` |
| Lockfile consistency | Passed with `uv lock --check --offline` |
| Ruff formatting and linting | Passed |
| Strict mypy checks | Passed for application, settings, and verification scripts |
| Pytest | **16 passed** |
| Documentation | Local Markdown targets and editable draw.io structure passed |
| Dependency exports | Both checked-in pip exports matched `uv.lock` |
| Optional hook configuration | `pre-commit validate-config` passed |
| Git whitespace check | `git diff --check` passed |
| Actual server startup | `make run` started successfully on a temporary loopback port; `/_stcore/health` returned HTTP 200 and `ok`. The temporary server was stopped afterward. |

`make check` runs the shared lockfile, formatting, linting, typing, test, documentation, and export checks. The tests isolate configuration in temporary directories and block network sockets; local Unix sockets are allowed because Streamlit's event loop requires them.

The Streamlit AppTest cases execute the page and verify both normal startup and a sanitized configuration failure. The HTTP smoke check verifies server startup separately. These checks do not constitute a completed catalog workflow, a visual browser review, or validation of real source/model behavior. Documentation checks validate local references and diagram structure rather than remote URLs or diagram appearance.

## Delivery status and remaining work

- This report records the local verification snapshot. Commit/push history and subsequent remote CI results are recorded in Git and GitHub.
- GitHub Actions is configured; no remote run was observed during local verification. Branch protection and remote repository settings were not changed.
- Optional Git hooks are configured but have not been installed. ADR-0001 and ADR-0002 retain **Proposed** status.
- Genuine catalog data, database migrations/imports, search/filtering, source refresh, deterministic screening/ranking, and model features remain PRD deliverables.

Start PRD 01 with its [catalog and search requirements](../requirements/01-catalog-and-search.md): establish at least 10 genuine sourced products, five per category, implement the initial schema and transactional import, and deliver the searchable local catalog. Apply the [readiness and completion criteria](../development.md) to that increment.

## Run and verify

From the repository root:

```sh
make setup
make check
make run
```

Open `http://127.0.0.1:8501` after starting the preview. Defaults work without `.env`; copy [.env.example](../../.env.example) only when local path overrides are needed. Use Ctrl+C to stop the server.
