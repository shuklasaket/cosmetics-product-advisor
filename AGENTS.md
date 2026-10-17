# Repository instructions

## Git workflow

- Create a dedicated branch from the latest `origin/main` before changing files for each task. Continue on the existing task branch for follow-up changes to its open PR.
- Follow the [branch and PR standards](docs/git-workflow.md): use `<type>/prd-<NN>-us-<NNN>-<description>` for numbered story work and `<type>/repo-<description>` for repository maintenance. Reference actual story records; never invent a story or issue number. Never commit or push directly to `main`.
- Run `make check` before pushing. Every human-authored PR must use all sections and fields in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md). Fill them with actual evidence or a justified `N/A`; complete the author checklist truthfully. Keep the description current. Validate the prepared PR with `scripts.check_pr` before publishing.
- Confirm the required GitHub CI check passes for the latest PR revision before merging. Recheck after new commits or base-branch updates; local success alone is insufficient.
- Follow the review and squash-merge procedure in [CONTRIBUTING.md](CONTRIBUTING.md). Do not bypass branch protection or use administrator overrides.

## Python style

Use the Ruff configuration in [pyproject.toml](pyproject.toml). Run `make format` to apply formatting and automatic lint fixes, and `make check` to verify the result. The project uses four-space indentation and a 100-character line limit; do not describe it as strict PEP 8 compliance.
