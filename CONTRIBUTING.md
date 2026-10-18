# Contributing

## Local workflow

Every change, including documentation and dependency updates, goes through a dedicated branch and a pull request to `main`. Direct commits/pushes to `main` are prohibited. Keep follow-up changes for an open PR on that PR's branch; start a new branch after it is merged.

Start with a clean working tree and the latest remote base:

```sh
git fetch origin
git switch --no-track -c feat/prd-01-us-001-search-by-name origin/main
make setup
```

The example requires an actual tracked `US-001` story; it does not assign that number. Follow the mandatory [branch naming and PR standards](docs/git-workflow.md) for numbered stories and repository maintenance. Use Python 3.12.15 and uv 0.13.1 from the [root setup guide](README.md).

Use a descriptive commit title. PR titles must match `<type>(US-001): <outcome>` for story work or `<type>(repo): <outcome>` for maintenance, with a type matching the branch. Inspect and stage the intended files, then run the shared checks before pushing:

```sh
make check
git diff --check
git add path/to/changed-file
git diff --cached
git commit -m "feat(US-001): add catalog name search"
git push --set-upstream origin HEAD
gh pr create --base main --template .github/PULL_REQUEST_TEMPLATE.md
gh pr checks --watch --fail-fast
```

Replace the staging path and commit message with the actual change. The PR command prompts for a title and description using the repository template. Every human PR must fill its six sections, required fields, and author checklist; the required CI job validates them. For scripted PR creation, prepare a temporary body file, run the [local PR validator](docs/git-workflow.md#enforcement-and-review), and publish that same file with `--body-file`. Title/body edits rerun CI. Genuine Dependabot PRs retain their generated metadata and still run the quality checks.

Review the diff and wait for **Python quality and offline verification** from GitHub Actions to pass on the latest PR revision. Failed, pending, cancelled, or outdated checks do not satisfy this workflow. `main` must be up to date before merging; use GitHub's update-branch action or merge `origin/main` into the working branch, then push and wait for CI again. Resolve review conversations. Changes requested in review must be addressed before merging.

Squash merge the reviewed PR through GitHub, or with `gh pr merge --squash --delete-branch`. Never use `--admin` to bypass requirements. GitHub deletes the remote working branch after merge. To return to a current local base:

```sh
git switch main
git pull --ff-only origin main
git fetch --prune origin
```

The next task starts with another dedicated branch. Avoid force-pushing shared branches; merge the base into a working branch when it needs an update.

CI runs the same checks on Ubuntu. The application targets macOS; record a local Mac startup check when runtime behavior changes. A CI configuration file does not prove a remote run has passed.

## GitHub enforcement

The managed configuration is recorded in [main-branch-protection.json](.github/main-branch-protection.json) and [repository-settings.json](.github/repository-settings.json):

- Require a PR, the named CI check from GitHub Actions, and an up-to-date base before merging into `main`.
- Apply protection to administrators, block force pushes/deletion of `main`, and require resolved review conversations.
- Allow squash merges only and delete merged working branches automatically.

The current single-maintainer setup requires zero independent approvals so the author can merge a reviewed PR after CI. A separate approving reviewer is not enforced; raise this requirement when another maintainer joins. PR and CI requirements still apply.

These JSON files document the managed settings; committing them does not configure GitHub. Maintainers can inspect actual enforcement with `gh api repos/shuklasaket/cosmetics-product-advisor/branches/main/protection` and repository merge settings with `gh api repos/shuklasaket/cosmetics-product-advisor`. When changing protection, preserve any additional restrictions that have since been introduced. The required check name is a contract: update branch protection along with any CI job rename.

## Code boundaries

- Keep Streamlit presentation in `app.py` and future UI modules. Put typed contracts in `schemas/`; add services, repositories, and tools when their PRDs need them.
- Keep ingredient eligibility and ranking deterministic and independently testable. Use integer paise and decimal score/cost arithmetic when those features are introduced.
- Validate inputs at boundaries. Return actionable, sanitized errors; do not log an entire request, exception payload, or graph state containing personal information.
- Keep source text and model output outside trusted instructions. Citations must support the actual displayed claim.
- Introduce database migrations with the first persistent schema in PRD 01. Preserve last-valid data on failed imports/migrations and add recovery checks.

## Dependencies and formatting

Add dependencies with `uv add PACKAGE` or `uv add --dev PACKAGE`. For a targeted upgrade, use `uv lock --upgrade-package PACKAGE`, then `uv sync --locked`, `make exports`, and `make check`. Review lockfile/export changes together. Runtime exports contain hashes; do not edit them by hand.

Ruff handles formatting and linting; mypy checks application/contracts/scripts. [pyproject.toml](pyproject.toml) is their shared configuration. `make format` applies Ruff lint fixes before formatting; inspect its diff before committing. `make check` verifies formatting and linting without modifying files, including in CI.

Python style follows Ruff's Black-compatible formatter and selected PEP 8/pycodestyle `E` checks, with four-space indentation, double quotes, LF endings, and a **100-character** line limit. The `I` rules check import order; `F`, `UP`, `B`, and `SIM` cover correctness and other code-quality policies. PEP 8 normally specifies 79-character code lines and 72-character prose lines, so this is a documented project style rather than strict enforcement of every PEP 8 recommendation. Naming and prose quality remain part of code review; no separate Black or autopep8 formatter is needed. See [PEP 8](https://peps.python.org/pep-0008/) and the [Ruff formatter documentation](https://docs.astral.sh/ruff/formatter/).

An optional [.pre-commit-config.yaml](.pre-commit-config.yaml) supplies local lint, format, and documentation hooks. Install it explicitly with `uv run --frozen pre-commit install` if wanted. Hooks have not been installed automatically; CI remains the shared verification path.

GitHub Actions are pinned to full revisions with read-only repository permissions. Dependabot proposes monthly action updates. Review those changes; no automatic merge or publishing is configured. Python dependency updates are deliberate uv lockfile updates.

## Tests and evidence

Follow the [testing and TDD guide](docs/testing.md) for behavior changes and bug fixes: work through Red, Green, and Refactor, then record the observed evidence in the PR. The guide defines test boundaries, fixture isolation, live-check separation, coverage priorities, and justified exemptions for changes without executable behavior.

Run `make check` before pushing and wait for the required GitHub CI result before merge. Synthetic fixtures must remain distinct from genuine release evidence under the [data policy](data/README.md); passing offline tests alone does not establish catalog validity or model quality.

## Project skills

Repository-local agent skills live in `.agents/skills/`; see the [catalog, integration boundaries, and update procedure](docs/skills.md). Keep source revisions, licenses/notices, and reviewed local adaptations with imports. `make skills` verifies the registry offline and is included in `make check`. Imported helper/example formatting is preserved separately from application Ruff checks. Skills are development guidance rather than runtime product agents or an authorization to perform unrelated actions.

## Review and completion

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) and the [readiness/completion criteria](docs/development.md). Link affected PRD IDs and include runnable verification. Update a relevant ADR for a significant new architectural decision; a tooling change does not automatically accept an existing Proposed ADR.

Never commit `.env`, credentials, real user profiles, raw conversations, generated databases, logs, model files, or exports. Review `git diff` and `git status` before staging. `.git` is maintained by Git; ordinary project setup belongs in the working tree.
