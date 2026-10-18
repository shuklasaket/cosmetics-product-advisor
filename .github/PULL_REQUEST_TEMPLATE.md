<!-- Follow docs/git-workflow.md. Keep every heading and field; fill with actual
evidence or N/A — reason. Use a draft until ready. Do not claim CI has passed
before it runs; GitHub tracks the required result separately. -->

## Summary

<!-- Explain the problem, resulting behavior, and why this approach fits. -->

## Traceability

<!-- Story branch: link [PRD-01] and [US-001] to actual repository Markdown
records, matching the branch/title. Use full GitHub file URLs to the PR
branch/commit so newly added records are accessible to reviewers.
Repository maintenance: use N/A — reason for both fields. -->
PRD:
User story:
Related issue: N/A

## Scope

Included:
Excluded:

## Validation

<!-- Record commands AND results; identify fixtures versus genuine evidence.
Link acceptance criteria and results. Include screenshots for UI changes,
or explain why UI evidence is not applicable. Disclose checks not run.
Follow docs/testing.md: for behavior changes, Checks must record the focused
test command/node ID, observed Red failure, Green result, and verification after
refactoring (or why none was needed), plus final repository checks. Group related
cases when useful. Disclose any test-first gap; never invent a failure result.
For changes without executable behavior, record TDD: N/A — reason in Checks
alongside the actual checks run. CI cannot prove test-first chronology. -->
Checks:
Acceptance criteria:
UI evidence:

## Risk and rollout

<!-- Cover relevant privacy, source rights, dependencies, configuration, and
schema/migration impacts. Give practical rollout and recovery instructions. -->
Impact:
Rollout:
Rollback:

## Review checklist

- [ ] I reviewed the diff and kept the PR focused on its stated scope.
- [ ] I ran the local checks and recorded actual results and limitations above.
- [ ] I updated affected documentation and contracts, or explained why no updates apply.
- [ ] I checked for secrets, personal data, generated files, and source-permission impacts.
