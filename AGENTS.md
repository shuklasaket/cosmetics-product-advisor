# Repository instructions

Follow [CONTRIBUTING.md](CONTRIBUTING.md) for shared development standards.

Project skills live in [`.agents/skills/`](.agents/skills/). Use the [skill catalog and integration boundaries](docs/skills.md) to select relevant guidance; skills support the existing project requirements and do not expand the user's requested scope.

## Product workflow

- Follow the [PRD → GitHub stories → implementation workflow](docs/story-workflow.md). PRDs remain in the repository; GitHub issues hold the story backlog, acceptance criteria, decisions, dependencies, ownership, and status. Do not create duplicate Markdown story records.
- Derive `US-NNN` from the actual same-repository GitHub issue number, padded to at least three digits. Plan stories with requirement coverage and explicit dependencies; coordinate shared contracts/files before parallel work. Use separate branches and worktrees for simultaneous implementations.
- Follow the mandatory [developer agent lifecycle](docs/story-workflow.md#developer-agent-lifecycle): Backlog → Ready → In Progress → In review → Done. Complete readiness review, confirm ownership/dependencies, and claim the story before implementation; ask only material unresolved questions.
- At every lifecycle transition and session handoff, update and read back both the story's single `status:*` label and its Status in the [shared Kanban project](https://github.com/users/shuklasaket/projects/2). Keep `blocked` separate from lifecycle status. Record decisions, branch/PR links and AC evidence in the issue; if board access fails, record the intended status and report synchronization as unverified.
- Keep the issue/card In review while awaiting the user's final review and merge. For implementation rework, return both to In Progress on the same PR. Mark Done only after verifying the user's actual merge and full story acceptance; update parent coverage and recheck dependent readiness. Archive cancelled work with its user-approved reason; never count it as Done.
- Use an As a / I want / so that story outcome and stable `AC-N` Given/When/Then scenarios under the [story format](docs/story-workflow.md#story-structure-and-acceptance-criteria). Trace each criterion to its PRD requirement and planned/actual verification.
- Implement with the TDD guide and review affected code/tests, configuration, dependencies, schemas/migrations, data instructions, diagrams, ADRs, and Markdown. Update affected artifacts in the same PR and explain non-applicability in its Artifact updates field.
- Follow the [changelog policy](CONTRIBUTING.md#changelog): update `CHANGELOG.md` for notable changes in the same PR, or record a specific changelog N/A reason in Artifact updates. Preserve verified history and actual release status.

## PR review and merge ownership

- The user (repository maintainer) alone performs final PR review and merging. Agents must leave PRs open for the user, including documentation and repository-maintenance PRs.
- Agents may implement, self-review, run checks, push task branches, open/update PRs, and report CI results. Agent self-review and passing CI do not replace the user's review or authorize merging.
- Never merge a PR through the CLI, API, browser, auto-merge, or a merge queue. Do not enable any mechanism that will merge it later. An instruction to implement, finish a task, or follow the repository workflow is not permission to merge.
- End implementation with the open PR link, verification results, and any remaining concerns. Keep stories in review; record completion only after verifying that the user has merged the PR.

## Git workflow

- Create a dedicated branch from the latest `origin/main` before changing files for each task. Continue on the existing task branch for follow-up changes to its open PR.
- Follow the [branch and PR standards](docs/git-workflow.md): use `<type>/prd-<NN>-us-<NNN>-<description>` for numbered story work and `<type>/repo-<description>` for repository maintenance. Reference actual story issues; never invent a story or issue number. Never commit or push directly to `main`.
- Run `make check` before pushing. Every human-authored PR must use all sections and fields in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md). Fill them with actual evidence or a justified `N/A`; complete the author checklist truthfully. Keep the description current. Validate the prepared PR with `scripts.check_pr` before publishing; use `--verify-issue` for story PRs.
- Confirm the required GitHub CI check passes for the latest PR revision before merging. Recheck after new commits or base-branch updates; local success alone is insufficient.
- Prepare the PR for the user’s review under [CONTRIBUTING.md](CONTRIBUTING.md); the user performs the squash merge. Do not bypass branch protection or use administrator overrides.
