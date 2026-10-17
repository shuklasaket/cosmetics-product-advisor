# Contributing

## Local workflow

Use Python 3.12.15 and uv 0.13.1 from the [root setup guide](README.md). Run `make setup`, make a focused change tied to a PRD requirement or technical requirement, then run `make check`. Use a short branch and a descriptive commit, such as `feat: add catalog budget filtering` or `docs: clarify ingredient evidence requirements`.

CI runs the same checks on Ubuntu. The application targets macOS; record a local Mac startup check when runtime behavior changes. A CI configuration file does not prove a remote run has passed.

## Code boundaries

- Keep Streamlit presentation in `app.py` and future UI modules. Put typed contracts in `schemas/`; add services, repositories, and tools when their PRDs need them.
- Keep ingredient eligibility and ranking deterministic and independently testable. Use integer paise and decimal score/cost arithmetic when those features are introduced.
- Validate inputs at boundaries. Return actionable, sanitized errors; do not log an entire request, exception payload, or graph state containing personal information.
- Keep source text and model output outside trusted instructions. Citations must support the actual displayed claim.
- Introduce database migrations with the first persistent schema in PRD 01. Preserve last-valid data on failed imports/migrations and add recovery checks.

## Dependencies and formatting

Add dependencies with `uv add PACKAGE` or `uv add --dev PACKAGE`. For a targeted upgrade, use `uv lock --upgrade-package PACKAGE`, then `uv sync --locked`, `make exports`, and `make check`. Review lockfile/export changes together. Runtime exports contain hashes; do not edit them by hand.

Ruff handles formatting and linting; mypy checks application/contracts/scripts. `pyproject.toml` is their shared configuration. `make format` may modify Python files; inspect its diff before committing.

An optional [.pre-commit-config.yaml](.pre-commit-config.yaml) supplies local lint, format, and documentation hooks. Install it explicitly with `uv run --frozen pre-commit install` if wanted. Hooks have not been installed automatically; CI remains the shared verification path.

GitHub Actions are pinned to full revisions with read-only repository permissions. Dependabot proposes monthly action updates. Review those changes; no automatic merge or publishing is configured. Python dependency updates are deliberate uv lockfile updates.

## Tests and evidence

Routine pytest runs block outbound network sockets, allow local Unix sockets for Streamlit's event loop, isolate `ADVISOR_` settings, and use temporary working directories. Add tests for meaningful policies, data integrity, and failure paths as functionality arrives. Use temporary SQLite databases and fixed timestamps for deterministic import/freshness checks.

Live source/model checks belong to an explicit `live` marker and separate, deliberately configured execution. Synthetic fixtures must be labeled and kept apart from genuine product evidence. See the [data policy](data/README.md). Do not assert byte-identical generated prose; assert supported claims, valid schemas, and unchanged deterministic decisions.

## Review and completion

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) and the [readiness/completion criteria](docs/development.md). Link affected PRD IDs and include runnable verification. Update a relevant ADR for a significant new architectural decision; a tooling change does not automatically accept an existing Proposed ADR.

Never commit `.env`, credentials, real user profiles, raw conversations, generated databases, logs, model files, or exports. Review `git diff` and `git status` before staging. `.git` is maintained by Git; ordinary project setup belongs in the working tree.
