# Development readiness and completion

This guide governs implementation of the [nine PRDs](requirements/README.md).
PRD 01 has a verified catalog release, and the first PRD 02 source contracts are
implemented. See the PRD index for the current baseline and remaining plan.

## Before a PRD starts

- Decompose the PRD through the [GitHub story workflow](story-workflow.md): create/find its tracking issue, map requirements to story issues, and record dependencies, execution waves, and shared-file ownership. Stories live in issues rather than duplicate Markdown records.
- Identify the PRD's deployable outcome, acceptance criteria, dependencies, and excluded scope.
- Identify observable test cases and the necessary fixtures or release evidence using the [testing and TDD guide](testing.md).
- Confirm earlier required releases work. Choose the smallest set of contracts and modules needed for this increment.
- Resolve inputs needed for the release: permitted data/source access, verified evidence, or model capability. Record unresolved assumptions and their effect on scope.
- Confirm the applicable ADR status. Create a focused ADR when a concrete implementation choice materially changes the architecture.

Before picking up a story, apply the [story readiness and ownership checks](story-workflow.md#readiness-and-pickup). Confirm its user outcome and numbered Given/When/Then scenarios, with each `AC-N` mapped to planned verification. Ask material unanswered questions, establish the required evidence, and claim an unblocked story before implementation. Shared-contract prerequisites must be merged before dependent branches start.

## Story progress and review handoff

Follow the mandatory [developer agent lifecycle](story-workflow.md#developer-agent-lifecycle)
and keep the issue's `status:*` label and shared Project Status aligned. Readiness
review precedes Ready; ownership/branch recording and In Progress precede code edits.
When the implemented increment is ready for user review, its open PR moves the
story to In review to await the user's review/merge. An early unfinished draft
remains In Progress. Rework returns to In Progress. `blocked` remains a separate flag;
report any synchronization failure with the intended board status.

Implementation handoff is not story completion. After verifying the user's actual
merge and all story acceptance evidence, mark the issue and board Done, update the
parent and recheck dependents. Cancelled stories are closed as not planned and
archived, never counted as Done. Release acceptance remains a separate check.

## Definition of Done

- The release runs from a clean environment using pinned dependencies and documented data preparation.
- Its visible workflow and acceptance criteria pass, including applicable invalid, empty, failure, and boundary cases.
- Behavior changes follow the [TDD cycle and PR evidence requirements](testing.md#pr-evidence-and-completion); bug fixes include regression tests. Record justified exemptions or any test-first gap honestly.
- Affected earlier behavior remains usable; `make check` and the required GitHub CI check pass on the latest PR revision before merge.
- Data changes include provenance, attribution, permissions, versions, and necessary migration/recovery instructions.
- Persistent stores, logs, and exports satisfy the technical requirements' privacy boundaries.
- Documentation reflects actual behavior. Record which checks used genuine sources, recorded responses, or synthetic fixtures.
- Notable changes have a same-PR [changelog entry](../CHANGELOG.md); justified omissions are recorded in Artifact updates under the [changelog policy](../CONTRIBUTING.md#changelog). Release headings use actual versions and dates.
- The PR records updates or justified non-applicability for affected code/tests, config, dependencies, schemas/migrations, data instructions, diagrams, ADRs, and Markdown under [artifact review](story-workflow.md#implementation-and-affected-artifacts).
- The user performs final PR review and merging; agents hand off an open PR after self-review and verification, without merging or scheduling a merge. The review checks the resulting behavior and evidence before merging. Record material limitations rather than implying an unperformed check passed.
- After verifying the user’s merge, confirm story acceptance, update the issue's evidence/status, Project Status and parent requirement coverage, and complete release-level checks before closing the parent PRD issue. Issue closure does not itself establish release acceptance.

## Readiness by release

| Release | Input to establish |
| --- | --- |
| 01 | At least 10 genuine sourced products, five per category; identity/provenance schema; transactional import and initial migration |
| 02 | Approved API contract/access and variant mapping; refresh/conflict/freshness fixtures |
| 03 | Domain-reviewed authoritative rule references, aliases, applicability, and coverage limits |
| 04 | Permitted genuine review samples; target-Mac local-model benchmark and structured-output validation |
| 05–06 | Versioned scoring vectors, evidence manifests, claim vocabulary, and unsupported-claim fixtures |
| 07–08 | Typed run/cancellation behavior, reviewed memory-save actions, and persistent-store inspection |
| 09 | Frozen permitted evaluation evidence, labeled synthetic profiles, usage reconciliation, and actual scenario results |

The genuine catalog, external collectors, regulatory rules, model installation, and PRD workflows are still implementation deliverables. The [data templates](../data/README.md) support evidence collection without fabricating records.

## Foundation verification

`make check` verifies code quality, types, startup/configuration behavior, repository links, draw.io structure, and generated dependency exports. It does not verify product suitability, regulatory correctness, real API availability, or final model quality. Those checks enter with the relevant PRD.

All changes use a dedicated branch and a PR to `main`; follow the [contributor workflow](../CONTRIBUTING.md). GitHub branch protection requires the named CI check and an up-to-date base before merge, including for administrators. Git hooks remain optional; local hook installation is separate from GitHub enforcement. The checked-in settings files document managed configuration, while GitHub's actual settings determine enforcement.
