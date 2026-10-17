# Development readiness and completion

This guide governs implementation of the [nine PRDs](requirements/README.md). The repository foundation supplies tooling and a development preview; it does not mark a PRD as delivered.

## Before a PRD starts

- Identify the PRD's deployable outcome, acceptance criteria, dependencies, and excluded scope.
- Confirm earlier required releases work. Choose the smallest set of contracts and modules needed for this increment.
- Resolve inputs needed for the release: permitted data/source access, verified evidence, or model capability. Record unresolved assumptions and their effect on scope.
- Confirm the applicable ADR status. Create a focused ADR when a concrete implementation choice materially changes the architecture.

## Definition of Done

- The release runs from a clean environment using pinned dependencies and documented data preparation.
- Its visible workflow and acceptance criteria pass, including applicable invalid, empty, failure, and boundary cases.
- Affected earlier behavior remains usable; `make check` passes and the CI result is recorded when available.
- Data changes include provenance, attribution, permissions, versions, and necessary migration/recovery instructions.
- Persistent stores, logs, and exports satisfy the technical requirements' privacy boundaries.
- Documentation reflects actual behavior. Record which checks used genuine sources, recorded responses, or synthetic fixtures.
- A code review checks the resulting behavior and evidence before merging. Record material limitations rather than implying an unperformed check passed.

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

Git hooks are optional and require explicit installation. CI is configured but runs remotely only after the workflow is pushed to GitHub. Branch protection and repository settings are not changed by local configuration files.
