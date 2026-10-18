# Repository instructions

Follow [CONTRIBUTING.md](CONTRIBUTING.md) for shared development standards.

Project skills live in [`.agents/skills/`](.agents/skills/). Use the [skill catalog and integration boundaries](docs/skills.md) to select relevant guidance; skills support the existing project requirements and do not expand the user's requested scope.

## Product workflow

- Follow the [PRD → GitHub stories → implementation workflow](docs/story-workflow.md). PRDs remain in the repository; GitHub issues hold the story backlog, acceptance criteria, decisions, dependencies, ownership, and status. Do not create duplicate Markdown story records.
- Derive `US-NNN` from the actual same-repository GitHub issue number, padded to at least three digits. Plan stories with requirement coverage and explicit dependencies; coordinate shared contracts/files before parallel work. Use separate branches and worktrees for simultaneous implementations.
- Pick up a ready, unblocked story, confirm ownership/dependencies, and ask only material unresolved questions. Record decisions and maintain issue status through completion.
- Use an As a / I want / so that story outcome and stable `AC-N` Given/When/Then scenarios under the [story format](docs/story-workflow.md#story-structure-and-acceptance-criteria). Trace each criterion to its PRD requirement and planned/actual verification.
- Implement with the TDD guide and review affected code/tests, configuration, dependencies, schemas/migrations, data instructions, diagrams, ADRs, and Markdown. Update affected artifacts in the same PR and explain non-applicability in its Artifact updates field.
- Follow the [changelog policy](CONTRIBUTING.md#changelog): update `CHANGELOG.md` for notable changes in the same PR, or record a specific changelog N/A reason in Artifact updates. Preserve verified history and actual release status.

## Git workflow

- Create a dedicated branch from the latest `origin/main` before changing files for each task. Continue on the existing task branch for follow-up changes to its open PR.
- Follow the [branch and PR standards](docs/git-workflow.md): use `<type>/prd-<NN>-us-<NNN>-<description>` for numbered story work and `<type>/repo-<description>` for repository maintenance. Reference actual story issues; never invent a story or issue number. Never commit or push directly to `main`.
- Run `make check` before pushing. Every human-authored PR must use all sections and fields in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md). Fill them with actual evidence or a justified `N/A`; complete the author checklist truthfully. Keep the description current. Validate the prepared PR with `scripts.check_pr` before publishing; use `--verify-issue` for story PRs.
- Confirm the required GitHub CI check passes for the latest PR revision before merging. Recheck after new commits or base-branch updates; local success alone is insufficient.
- Follow the review and squash-merge procedure in [CONTRIBUTING.md](CONTRIBUTING.md). Do not bypass branch protection or use administrator overrides.
