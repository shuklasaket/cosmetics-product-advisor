# Contributing

## Product planning and story pickup

Follow the [PRD and GitHub story workflow](docs/story-workflow.md) for decomposition, dependency/parallel-work planning, readiness, clarification, ownership, artifact updates, and completion. GitHub issues hold stories; PRDs and durable technical/operating documentation stay in the repository. Issue #42 maps to `US-042`; use the actual issue number, not a separate sequence. Use the issue forms and label-based backlog views, and keep tracking status current through merge. Parallel implementations require separate branches and working directories/worktrees plus shared-file coordination.

Developer agents must follow the [story lifecycle and transition procedure](docs/story-workflow.md#developer-agent-lifecycle). The [Kanban project](https://github.com/users/shuklasaket/projects/2) and issue `status:*` labels must be updated and read back together at readiness, pickup, review, rework and verified completion. `blocked` stays separate; no label-to-Project synchronization is automated. Record and report any unavailable board update rather than claiming synchronization.

## Review and merge ownership

The user (repository maintainer) performs final PR review and every merge. Agents
implement, self-review, verify, push branches, and open/update PRs, then hand off
the open PR with verification results and remaining concerns. This applies to
product work, documentation, maintenance, and dependency changes.

Agent self-review, successful CI, a task-completion request, and this workflow do
not authorize an agent to merge. Agents must not merge through CLI/API/browser,
enable auto-merge, or enqueue a PR for a later merge. Leave the PR open and its
story in review until the user merges it. After observing the user's merge,
completion tracking may be updated; do not claim completion from passing CI alone.

## Local workflow

Every change, including documentation and dependency updates, goes through a dedicated branch and a pull request to `main`. Direct commits/pushes to `main` are prohibited. Keep follow-up changes for an open PR on that PR's branch; start a new branch after it is merged.

Start with a clean working tree and the latest remote base:

```sh
git fetch origin
git switch --no-track -c feat/prd-01-us-042-search-by-name origin/main
make setup
```

The example requires actual GitHub issue #42 to be a ready story mapped to `US-042`; it does not assign that number. Substitute the selected story's actual ID, or use a `repo-` branch for maintenance. Follow the mandatory [branch naming and PR standards](docs/git-workflow.md). Use Python 3.12.15 and uv 0.13.1 from the [root setup guide](README.md).

Use a descriptive commit title. PR titles must match `<type>(US-042): <outcome>` for the illustrated story or `<type>(repo): <outcome>` for maintenance, with a type matching the branch. Inspect and stage the intended files, then run the shared checks before pushing:

```sh
make check
git diff --check
git add path/to/changed-file
git diff --cached
git commit -m "feat(US-042): add catalog name search"
git push --set-upstream origin HEAD
gh pr create --base main --template .github/PULL_REQUEST_TEMPLATE.md
gh pr checks --watch --fail-fast
```

Replace the staging path and commit message with the actual change. The PR command prompts for a title and description using the repository template. Every human PR must fill its six sections, required fields, and author checklist; the required CI job validates them. For scripted PR creation, prepare a temporary body file, run the [local PR validator](docs/git-workflow.md#enforcement-and-review), and publish that same file with `--body-file`. Title/body edits rerun CI. Genuine Dependabot PRs retain their generated metadata and still run the quality checks.

Review the diff and wait for **Python quality and offline verification** from GitHub Actions to pass on the latest PR revision. Failed, pending, cancelled, or outdated checks do not satisfy this workflow. `main` must be up to date before merging; use GitHub's update-branch action or merge `origin/main` into the working branch, then push and wait for CI again. Resolve review conversations. Changes requested in review must be addressed before merging.

The user squash-merges the reviewed PR through GitHub. Agents stop at the open-PR handoff and must not perform or schedule this merge. Never use `--admin` to bypass requirements. GitHub deletes the remote working branch after the user merges. Once that merge is verified, return to a current local base:

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

The current GitHub configuration requires zero independent approvals; it does not technically enforce the user-only review/merge rule above. That rule remains mandatory for agents regardless of what the authenticated account can do. A separate approving reviewer is not enforced; raise this requirement when another maintainer joins. PR and CI requirements still apply.

These JSON files document the managed settings; committing them does not configure GitHub. Maintainers can inspect actual enforcement with `gh api repos/shuklasaket/cosmetics-product-advisor/branches/main/protection` and repository merge settings with `gh api repos/shuklasaket/cosmetics-product-advisor`. When changing protection, preserve any additional restrictions that have since been introduced. The required check name is a contract: update branch protection along with any CI job rename. The required job's PR metadata step has read-only issue access for live story verification; application verification remains offline.

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

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) and the [readiness/completion criteria](docs/development.md). Link the affected PRD document and GitHub story issue, record artifact updates/non-applicability, and include runnable verification. Update a relevant ADR for a significant new architectural decision; a tooling change does not automatically accept an existing Proposed ADR. After merge, confirm story completion and update its status/evidence plus parent PRD coverage under the [story workflow](docs/story-workflow.md#pr-review-and-completion).

Never commit `.env`, credentials, real user profiles, raw conversations, generated databases, logs, model files, or exports. Review `git diff` and `git status` before staging. `.git` is maintained by Git; ordinary project setup belongs in the working tree.

## Changelog

Maintain the root [CHANGELOG.md](CHANGELOG.md) in the same PR as each notable product or development-workflow change. Include new capabilities, changed behavior, fixes, removals/deprecations, meaningful dependency/tooling changes, migration/configuration requirements, and security changes where applicable. Small wording, formatting, test-only, or internal refactoring changes with no meaningful reader impact may omit an entry; explain that decision in the PR's **Artifact updates** field. Every human PR must record its changelog update or a specific `Changelog: N/A — <reason>` there.

Add a concise outcome and relevant impact under **Unreleased**, using only the categories needed: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**, and **Security**. Link actual related issues/PRs when available; historical work without a PR can link its verified commit. Keep newer entries first within a category, avoid empty headings and implementation transcripts, and keep delivery status accurate. Unmerged work becomes part of the canonical history when its PR merges; planned features and completed PRD releases must not be conflated. Git history retains commit details and PRs retain implementation/test evidence.

When an actual release is prepared, move its completed entries into a section headed `## [version] - YYYY-MM-DD`, using the real version/tag and release date. Leave **Unreleased** for subsequent work and add the release/tag link. A PRD number or the scaffold's package version does not by itself establish a release. Backfill only verified changes; never invent historical versions, dates, or delivery claims.

For parallel stories, add each entry on its own branch, coordinate edits to shared headings, and reconcile the changelog after base updates. Review the final entries for duplicates, ordering, and issue/PR links before merging. `make docs` checks the changelog's local links; reviewers assess its completeness and accuracy rather than requiring artificial edits for every PR.
