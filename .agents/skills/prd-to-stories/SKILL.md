---
name: prd-to-stories
description: "Decompose this repository's PRDs into user stories with requirement coverage, acceptance scenarios, verification, and dependencies. Use to draft a story plan or create/update its GitHub backlog when requested; not to implement stories or author new PRDs."
---

# PRD to stories

Turn a selected PRD into independently reviewable outcomes using the existing
[story workflow](../../../docs/story-workflow.md). That guide and the
[PRD tracking](../../../.github/ISSUE_TEMPLATE/prd-tracking.yml) and
[user story](../../../.github/ISSUE_TEMPLATE/user-story.yml) forms define the fields
and lifecycle; read them instead of maintaining another template here. Follow
[CONTRIBUTING.md](../../../CONTRIBUTING.md) and the
[skill boundaries](../../../docs/skills.md).

## Establish scope and current state

- Resolve the requested PRD number or path against the
  [requirements index](../../../docs/requirements/README.md). Read that PRD, its
  release prerequisites, applicable
  [technical contracts](../../../docs/requirements/TECHNICAL_REQUIREMENTS.md),
  and relevant [ADRs](../../../docs/adr/README.md). Inspect current implementation
  and verification where they affect what work remains; planned architecture is
  not proof of delivered behavior.
- Honor the requested mode. Draft or preview requests produce a plan in chat.
  A request to create, publish, or update GitHub stories authorizes those scoped
  issue changes; reuse that authorization without another confirmation. If the
  request only says to generate stories, draft them in chat. Do not begin
  implementation or launch parallel agents as a side effect of planning.
- Use the repository's existing authenticated `gh` access. Confirm the target
  repository from its remote, then search open and closed PRD/story issues,
  including existing parent relationships and overlapping requirement coverage.
  Read matching issue bodies, decisions, and linked completion evidence; retrieve
  all relevant results rather than relying on a truncated first page. Reuse the
  existing parent and distinguish completed, active, cancelled, and missing work.
- If GitHub cannot be read, a local draft can still proceed. Identify duplicate,
  ownership, and dependency checks as unverified; do not claim a publishable,
  duplicate-free backlog. Ask only material unresolved scope questions and
  continue independent planning while awaiting answers.

## Decompose and verify coverage

Use the story workflow's decomposition and acceptance-criteria sections to fill
all fields from the current forms. Keep each story small enough for one focused
PR, with its tests and documentation included. Do not force a story count.

For each outcome, provide As a / I want / so that, priority with rationale, rough
size with assumptions, scope boundaries, and stable `AC-N` Given/When/Then
scenarios. Copy actual PRD requirement IDs and map each criterion to a planned
observable check with its evidence type. Distinguish synthetic fixtures from the
genuine data/model evidence needed for release acceptance. Record artifact
impacts, questions/decisions, and rollout/recovery needs in the form's fields.

Build a requirement-to-story coverage table that accounts for every must-have
requirement and release-level acceptance check. Identify gaps or explicit prior
deferrals; do not silently drop requirements or invent scope decisions. Use
provisional titles such as `Draft: catalog import` before issue creation, never
predicted issue numbers or invented `US-NNN` IDs.

Separate parent-child grouping from actual blocking dependencies. Check for
cycles and account for earlier PRD prerequisites and non-issue inputs. Record
execution waves, shared contracts/files, ownership where known, and integration
order. Unknown owners remain unresolved. Apply the workflow's readiness review;
newly generated stories start in backlog and only move to ready when its criteria
are verified. Planning an implementation dependency does not satisfy it.

## Publish or reconcile when requested

Prepare complete parent/story bodies and the coverage/dependency plan before
mutating GitHub. Use temporary body files with `gh --body-file` where supported;
keep GitHub issues as the authoritative backlog, without committed Markdown story
copies. Consult current tool/API documentation if relationship operations are
unclear rather than guessing commands.

Re-read affected issues before applying changes. Reuse matching open stories and
preserve existing ownership, decisions, lifecycle status, and referenced `AC-N`
IDs. Update only the requested planning scope. Completed stories remain historical;
new follow-up work gets a new issue. Flag ambiguous overlaps instead of creating
competing stories or replacing human edits.

Create the parent if missing, then missing stories with the form's fields and
required labels. Derive each `US-NNN` from the actual returned same-repository issue
number. Attach native sub-issues and blocking relationships, and reconcile the
parent's coverage table and execution waves using the real issue links. Mark
unresolved blockers according to the workflow rather than claiming readiness.

Read back issue bodies, labels, parent/blocking relationships, and coverage to
verify the result. If a write times out or partly succeeds, inspect GitHub before
retrying; resume from confirmed state without duplicate issues. Stop mutations
on authentication/permission failures or repeated unexplained errors and report
completed changes plus remaining work. A text dependency list alone does not
prove native relationships were created.

## Report the result

For a draft, show the proposed parent, full story drafts, coverage, dependencies,
and unresolved decisions in chat. For published work, link the parent and stories,
summarize what was created, reused, or updated, and report verified readiness and
remaining blockers. State which checks could not be performed; issue creation is
not implementation or release completion.
