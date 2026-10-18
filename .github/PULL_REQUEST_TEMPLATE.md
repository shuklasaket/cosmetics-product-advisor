<!-- Follow docs/git-workflow.md. Keep every heading and field; fill with actual
evidence or N/A — reason. Use a draft until ready. Do not claim CI has passed
before it runs; GitHub tracks the required result separately. -->

## Summary

<!-- Explain the problem, resulting behavior, and why this approach fits. -->

## Traceability

<!-- Story branch: link [PRD-01] to its repository document and [US-NNN] to
https://github.com/shuklasaket/cosmetics-product-advisor/issues/N.
US-NNN is the issue number padded to at least three digits; use Closes #N
for a complete story or Refs #N for partial work that leaves it open.
Use a full GitHub file URL for the PRD document at the intended revision.
Repository maintenance: use N/A — reason for both fields. -->
PRD:
User story:
Related issue: N/A

## Scope

Included:
Excluded:
<!-- Assess code/tests, configuration and .env.example, dependencies/lock/exports,
schemas/migrations, data instructions, diagrams, ADRs, and Markdown guides.
Name affected artifacts and updates; explain categories that do not apply.
Follow CONTRIBUTING.md#changelog: include a CHANGELOG.md entry for notable
changes, or state Changelog: N/A — specific reason in Artifact updates. -->
<!-- Story PRs: include issue/Project links and read-back status:* label + Project
Status here, or the specific synchronization blocker and intended Status.
Maintenance PRs without a story: explain tracking N/A. Follow docs/story-workflow.md.
At review handoff, keep the story In review for the user's review/merge; do not mark Done from CI. -->
Artifact updates:

## Validation

<!-- Record commands AND results; identify fixtures versus genuine evidence.
Map each changed story AC-N to actual test/check references and observed results;
disclose unverified criteria. Include screenshots for UI changes,
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
