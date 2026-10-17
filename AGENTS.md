# Repository instructions

## Git workflow

- Create a dedicated branch from the latest `origin/main` before changing files for each task. Continue on the existing task branch for follow-up changes to its open PR.
- Use `feat/`, `fix/`, `docs/`, `chore/`, or `refactor/` with a short descriptive suffix. Never commit or push directly to `main`.
- Run `make check` before pushing. Open a pull request to `main` and include the change's purpose and verification evidence.
- Confirm the required GitHub CI check passes for the latest PR revision before merging. Recheck after new commits or base-branch updates; local success alone is insufficient.
- Follow the review and squash-merge procedure in [CONTRIBUTING.md](CONTRIBUTING.md). Do not bypass branch protection or use administrator overrides.

## Python style

Use the Ruff configuration in [pyproject.toml](pyproject.toml). Run `make format` to apply formatting and automatic lint fixes, and `make check` to verify the result. The project uses four-space indentation and a 100-character line limit; do not describe it as strict PEP 8 compliance.
