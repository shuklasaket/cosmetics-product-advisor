# PRDs, GitHub stories, and implementation

Use this sequence for product work: **PRD → story issues and dependency plan → ready story and clarification → TDD implementation and affected artifacts → detailed PR → CI/review → merge and completion evidence**.

PRD documents under [requirements/](requirements/README.md) remain the versioned product requirements. GitHub issues are the source of truth for story scope, acceptance criteria, questions, ownership, dependencies, and status. Keep implementation rationale and verification in the linked PR and durable operating guidance in the repository. Do not maintain a second Markdown copy of each story.

## Backlog and identity

Use these live views as the backlog/index; an empty view means no matching issues have been planned yet:

| View | Purpose |
| --- | --- |
| [PRD tracking issues](https://github.com/shuklasaket/cosmetics-product-advisor/issues?q=is%3Aissue%20label%3Atype%3Aprd) | Parent release outcomes, requirement coverage, and execution waves |
| [Open stories](https://github.com/shuklasaket/cosmetics-product-advisor/issues?q=is%3Aissue%20is%3Aopen%20label%3Atype%3Astory) | Entire active story backlog |
| [Ready to pick up](https://github.com/shuklasaket/cosmetics-product-advisor/issues?q=is%3Aissue%20is%3Aopen%20label%3Atype%3Astory%20label%3Astatus%3Aready%20-label%3Ablocked%20no%3Aassignee) | Unassigned stories whose readiness was reviewed |
| [Blocked work](https://github.com/shuklasaket/cosmetics-product-advisor/issues?q=is%3Aissue%20is%3Aopen%20label%3Ablocked) | Missing inputs, decisions, or dependencies |
| [In progress](https://github.com/shuklasaket/cosmetics-product-advisor/issues?q=is%3Aissue%20is%3Aopen%20label%3Astatus%3Ain-progress) | Claimed implementation work |
| [In review](https://github.com/shuklasaket/cosmetics-product-advisor/issues?q=is%3Aissue%20is%3Aopen%20label%3Astatus%3Ain-review) | Stories with implementation PRs |

Filter any view by `prd:01` through `prd:09`, or by assignee. A GitHub Projects board may display these same issues when Projects access is configured; keep its columns aligned with the issue status labels. The label-based backlog works without Projects permissions. No Projects synchronization or issue-status automation is configured by these templates.

Every story has `type:story`, exactly one `prd:NN` label, and exactly one `status:*` label. Its identity is derived from its actual same-repository issue number, padded to at least three digits: **issue #42 → US-042**; issue #1000 → US-1000. Numbers used by PRs, bugs, and PRD tracking issues create harmless gaps. Never allocate a separate story sequence, predict the next issue number, or reuse a cancelled story's identity. Keep stories in this repository so the mapping stays stable.

Use a concise outcome title; including `US-NNN` in an issue title after creation is optional. Branches and PR titles use the mapped ID under the [Git standards](git-workflow.md). Examples in this guide illustrate naming and do not create or assign actual stories.

## Decompose a PRD

For a reusable chat entry point, use the repository's [prd-to-stories skill](../.agents/skills/prd-to-stories/SKILL.md). See [chat examples](skills.md#plan-stories-in-chat) for drafting a plan, creating issues, or updating an existing backlog. This workflow remains the authority for the skill's output.

1. Read the PRD, shared technical contracts, release prerequisites, and relevant ADRs. Resolve material scope questions with the user; record the resulting decisions and remaining blockers.
2. Create one parent issue with the [PRD tracking form](../.github/ISSUE_TEMPLATE/prd-tracking.yml), link the existing PRD document, and add `type:prd`, its `prd:NN`, and `status:backlog`. Search for an existing parent before creating another.
3. Create focused stories with the [user story form](../.github/ISSUE_TEMPLATE/user-story.yml). Each needs PRD/parent/requirement-ID traceability, an **As a / I want / so that** user outcome with priority and rough size, included/excluded scope, [numbered Given/When/Then acceptance scenarios](#story-structure-and-acceptance-criteria), dependencies, questions/decisions, artifact impact, and a verification plan. Split outcomes too large for one independently reviewable PR. Technical prerequisites can be stories when they explain the user or operator outcome they enable.
4. Attach stories as native sub-issues of the parent. Maintain a requirement-ID → story-issue coverage table in the parent so omissions and release-level checks remain visible. Do not force a fixed story count or split tests/documentation away from the behavior they verify.
5. Mark native **blocked by / blocking** relationships for actual prerequisites, including earlier PRD releases where necessary. Parent-child relationships group work; blocking relationships express execution order. Record non-issue inputs such as permitted data, model availability, or a needed decision in the story and add `blocked`.
6. Record execution waves in the parent: shared-contract prerequisites first, independent stories next, and integration/release checks when their dependencies are available. Record shared-file owners and integration order. A wave is a planning aid, not a substitute for actual dependency checks.

Maximize useful parallel work by removing unnecessary coupling. Stories may run together only when their prerequisites are satisfied, interfaces are agreed, and shared-file changes have an owner and coordination plan. Code/schema prerequisites must be merged before dependent branches start. Keep one branch and one working directory or worktree per active story; use the latest `origin/main` for each. A shared checkout cannot safely hold simultaneous story edits. Use separate worktrees under the workspace when needed. Coordinate edits to `app.py`, schemas, dependency files, diagrams, and guides; rerun integration checks after merging changes to shared contracts.

These rules permit parallel implementation when requested; they do not automatically launch multiple agents or expand product scope.

## Story structure and acceptance criteria

Keep the issue's traceability, user outcome, scope, acceptance criteria, dependencies/parallel work, questions/decisions, artifact impact, and verification as structured fields. The user outcome uses **As a [user], I want [capability], so that [benefit]**. Include priority and its reason plus rough size and assumptions. Copy actual covered requirement IDs from the parent PRD into the form's dedicated field.

Write acceptance criteria as scenarios with stable IDs such as `AC-1`, `AC-2`, and a short behavior title referencing the relevant PRD requirement ID:

- **Given** establishes the initial state, required inputs, and evidence conditions.
- **When** describes one main user or system action.
- **Then** states concrete, observable outcomes a test or recorded check can verify. Use **And** for additional preconditions or related outcomes when needed.

Cover the relevant successful, boundary, invalid-input, empty-result, and failure/recovery cases. Choose cases from the story's actual requirements and risks; there is no fixed scenario count. State thresholds, units, and expected errors/results explicitly where applicable. Keep internal implementation choices in technical notes and describe user-visible or contracted behavior in the scenarios. Infrastructure stories can describe an operator or system action and its observable result.

This illustrative criterion is derived from [CAT-05](requirements/01-catalog-and-search.md), uses synthetic evidence, and does not create a story or claim the search is implemented:

```text
AC-1 — Include a product at the budget ceiling (CAT-05)
Given the shopper supplies valid sunscreen requirements for India with a ₹800 maximum
And a synthetic sunscreen is available in India at a known price of ₹800
When the shopper searches the catalog
Then that sunscreen appears in the matching results
```

Map every `AC-N` to a planned test/check and identify synthetic, recorded, or genuine evidence in **Verification and evidence**. At completion, replace planned references with actual tests/checks, observed results, remaining limitations, and the implementation PR. Retain IDs once referenced by tests or PRs; append new IDs instead of renumbering existing criteria. Revisit coverage when criteria change.

Given/When/Then is the issue-writing convention and maps to the existing pytest/AppTest workflow described in [testing.md](testing.md); it does not require a BDD runner or executable `.feature` files. Dependencies, artifact reviews, and the shared Definition of Done remain structured fields/checklists. Reviewers assess scenario quality and coverage; the PR metadata validator does not parse scenario grammar or establish acceptance.

Reference: [Gherkin's Given/When/Then semantics](https://cucumber.io/docs/gherkin/reference/).

## Readiness and pickup

An issue can move to `status:ready` only after a readiness review establishes:

- Its parent PRD/tracking issue, requirement coverage, bounded user outcome, and numbered Given/When/Then acceptance scenarios are clear under the [story format](#story-structure-and-acceptance-criteria).
- Every `AC-N` maps to observable planned verification, including applicable invalid, empty, failure, and boundary cases.
- Blocking implementation dependencies are merged, required evidence/access is available, and shared interfaces/files are coordinated.
- Material questions about behavior, scope, data rights, architecture, or acceptance have recorded answers. Document reversible assumptions; unresolved material decisions keep the story blocked.
- Artifact impacts and rollout/recovery needs have been assessed. The story is small enough for a focused PR.

At pickup, re-read the issue and linked documents, check its current dependencies and assignment, then assign one accountable implementation owner and replace `status:ready` with `status:in-progress`. Link the branch or draft PR on the issue so others can see the claim. For an agent, the assignee is the responsible human account; record the working branch to identify the active task. Check again before claiming to avoid duplicate work.

Ask the user only for missing information that materially affects the outcome. Record answers and their scope impact in the issue; continue independent work while a question is pending. If blocked, retain the current lifecycle status, add `blocked`, and record the blocker, decision owner, and next action. Remove `blocked` only after resolution and recheck readiness. Updating acceptance criteria requires revisiting the verification plan and keeping the PR current.

## Implementation and affected artifacts

Use the [TDD guide](testing.md) and relevant [project skills](skills.md). Implement the complete story increment, including its tests and operating changes. Review each category below, update affected artifacts in the same PR, and record justified non-applicability in the PR's **Artifact updates** field:

| Category | Review and update when affected |
| --- | --- |
| Behavior and verification | Application/services/adapters, typed contracts, unit/integration/UI tests, and acceptance evidence |
| Configuration | Validated settings, defaults, `.env.example`, startup errors, and configuration documentation |
| Dependencies and tooling | `pyproject.toml`, `uv.lock`, generated dependency exports, Make targets, and CI |
| Persistent data | Schemas/migrations, provenance, permitted fixtures/data instructions, and backup/recovery |
| Architecture | Editable draw.io pages, their guide, technical contracts, and relevant ADRs when the design changes |
| Documentation | README, affected PRD requirements if agreed scope changes, setup/run/recovery guides, and linked references |
| Changelog | A concise `CHANGELOG.md` entry for notable changes, or a specific N/A reason in Artifact updates under the [maintenance policy](../CONTRIBUTING.md#changelog) |
| Tracking | Issue decisions, acceptance/verification mapping, parent requirement coverage, and dependencies |

Do not mark target architecture as implemented or a Proposed ADR as Accepted merely because a story touches a related module. Documentation-only workflow changes need not alter the product architecture diagram; explain why it is unaffected.

## PR, review, and completion

1. Run `make check` and inspect the diff, including the [changelog update or justified omission](../CONTRIBUTING.md#changelog). Prepare every field in the [PR template](../.github/PULL_REQUEST_TEMPLATE.md): problem/result, PRD/issue traceability, scope, artifact updates, observed TDD/check results, acceptance coverage, UI evidence where relevant, impacts, rollout, and rollback.
2. Validate the prepared body with `scripts.check_pr`; for story work include `--verify-issue` with authenticated `gh`. Publish that same body, link the implementation PR, and replace the issue's current status with `status:in-review`. Keep a draft while work remains. A partial PR uses `Refs #N` and leaves the story open; use `Closes #N` only when the story's full criteria will be met by merge.
3. Review the behavior, evidence, current issue criteria, artifact completeness, and recovery plan. Wait for required CI on the latest PR revision, address feedback, update the base as needed, and recheck CI. Issue edits alone do not rerun PR CI; rerun the PR's checks after material issue changes. Mechanical checks do not prove readiness or acceptance coverage.
4. Hand the open PR to the user for final review and squash merge through the [contributor workflow](../CONTRIBUTING.md#review-and-merge-ownership). Agents must not merge or enable auto-merge/merge queues, even after CI passes. Leave the story in review until the user’s merge is verified. A `Closes #N` link closes the issue when merged into `main`; it does not update custom status labels. After confirming the merged behavior and evidence, replace the current status with `status:done`, remove `blocked`, and record the final PR/result in the issue. These tracking updates are manual.
5. Complete the parent release only after all required child outcomes and the PRD's full runnable increment/release checks pass. Update its coverage/evidence and status, then close it. Closing child issues alone does not prove release acceptance. Deferred requirements need an explicit recorded scope decision and follow-up issue.

For cancelled or superseded work, record the reason/replacement, close as not planned, and use `status:cancelled`; do not claim completion. Reopened work returns to the appropriate active status and needs a new readiness check. Use a fresh issue for new work after a completed story, and a fresh task branch after a merged PR.

## Repository setup and enforcement

The forms and [label definitions](../.github/issue-labels.json) are repository configuration. Forms become available from the default branch after merge; labels must also exist on GitHub. With repository issue-management access, apply the managed labels from the repository root:

```sh
uv run --frozen python - <<'PY'
import json
import subprocess
from pathlib import Path

for label in json.loads(Path(".github/issue-labels.json").read_text()):
    subprocess.run(
        ["gh", "label", "create", label["name"], "--repo",
         "shuklasaket/cosmetics-product-advisor", "--color", label["color"],
         "--description", label["description"], "--force"],
        check=True,
    )
PY
```

This updates only managed label names; preserve unrelated labels. Forms apply the type and initial backlog labels. The planner adds the correct PRD label, parent/blocking relationships, and assignee; lifecycle changes remain manual. Form requirements guide interactive creation, while CLI/API-created issues must follow the same fields through review. This setup does not itself generate a product story backlog.

Offline PR validation checks the branch/title, matching canonical issue link/number, local PRD document, and completed PR fields. Required GitHub CI additionally uses read-only issue access to confirm that the reference is an open issue rather than a PR, has `type:story` and exactly the matching `prd:NN` label, and links its parent PRD. A missing/inaccessible issue or failed lookup blocks the check. Repository-maintenance and genuine Dependabot PRs do not need a product story. These checks do not prove issue content, ownership, dependencies, or results are correct; review remains necessary.

References: [GitHub issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms), [sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues), [issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies), and [PR closing links](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
