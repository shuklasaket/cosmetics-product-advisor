# Branch names and pull request standards

Every human-authored change uses these rules, the [PR template](../.github/PULL_REQUEST_TEMPLATE.md), and the branch → PR → required CI → squash merge workflow in [CONTRIBUTING.md](../CONTRIBUTING.md). Product work starts with the [GitHub story planning and pickup workflow](story-workflow.md). Keep each PR focused on one independently reviewable outcome. Draft PRs can show unfinished work; all requirements apply before merge.

## Branch naming

| Work | Required pattern | Illustrative example |
| --- | --- | --- |
| Numbered user story | `<type>/prd-<NN>-us-<NNN>-<description>` | `feat/prd-01-us-001-search-by-name` |
| Repository maintenance without a user story | `<type>/repo-<description>` | `chore/repo-branch-and-pr-standards` |

Rules:

- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`, or `revert`. Choose the change's main purpose.
- Use lowercase ASCII letters, numbers, and single hyphens in the description. Start the description with a letter. Use exactly one slash after the type; no spaces, underscores, repeated/trailing hyphens, personal names, or dates.
- Limit the full branch name to 100 characters. Describe the outcome concisely.
- Match `prd-01` to PRD 01 and `us-001` to the actual tracked story `US-001`. PRD numbers have two digits; story numbers have at least three, padded only to three digits (`001`, `042`, `123`, `1000`). Zero is not an ID.
- A story's ID is its actual GitHub issue number padded to at least three digits: issue #42 is `US-042`, and issue #1000 is `US-1000`. IDs remain stable when a story changes PRD. Gaps are expected because other issues and PRs share GitHub's numbering; never allocate a separate sequence.
- Keep the story in a same-repository GitHub issue using the [story form and readiness rules](story-workflow.md), with `type:story` and exactly its matching `prd:NN` label. Link that issue and the existing parent PRD document from the PR. Repository Markdown story copies are not required or accepted as the story reference.
- Use `repo-` only for shared repository work such as CI, tooling, process, or documentation. Explain why PRD/story references do not apply; it is not an alternative for untracked product work.
- Continue follow-up changes on an open PR's branch. Start a fresh branch from the latest `origin/main` after merge; do not reuse a merged branch.

Examples are naming illustrations, not assigned story IDs or a generated backlog. A story branch implementing another PRD could be `fix/prd-02-us-014-preserve-last-valid-price`; it must reference real issue #14, labeled for PRD 02, before it can pass the PR checks.

Genuine Dependabot PRs retain their generated `dependabot/...` names and descriptions. The automated exception checks the bot identity, GitHub account type, and same-repository origin; a human branch with that prefix receives no exception. Dependency changes still run the full required quality check and follow the merge protections.

## PR title and traceability

Use `<type>(<scope>): <outcome>` with a title of at most 100 characters. The type must match the branch. Story PRs use the uppercase story ID as scope; maintenance PRs use `repo`:

```text
feat(US-001): add catalog name search
fix(US-014): preserve the last valid price after refresh failure
chore(repo): enforce branch and pull request standards
```

For a story PR, link the actual GitHub issue and its repository PRD document. Use the issue's canonical HTTPS URL with no fragment, query, or padded issue number. Use a full GitHub file URL for the PRD at the intended branch/commit. Illustrative metadata for issue #42, after it actually exists:

```md
PRD: [PRD-01](https://github.com/shuklasaket/cosmetics-product-advisor/blob/main/docs/requirements/01-catalog-and-search.md)
User story: [US-042](https://github.com/shuklasaket/cosmetics-product-advisor/issues/42)
Related issue: Closes #42
```

For that example, use branch `feat/prd-01-us-042-search-by-name` and title `feat(US-042): add catalog name search`. The branch, title, story link label, and issue number must agree. The PRD link must target the corresponding document under `docs/requirements/`; its file references may be same-repository GitHub file URLs or repository-relative paths resolved against the checkout. Reviewers confirm published file URLs point to the intended revision. The story issue itself must also link that PRD and carry the matching label. Link the story's numbered acceptance criteria and record their verification in the validation section. Keep a PR focused on one primary story; reference related work separately rather than silently including more stories.

For story branches, **Related issue** must be `Closes #N` or `Refs #N` for the same story issue. Use `Closes` only for full story completion; a partial PR uses `Refs` and leaves the story open. Put additional issue links elsewhere in traceability. For `repo-` branches, write `PRD: N/A — <reason>` and `User story: N/A — <reason>`; related issues are optional and can be `N/A`. Do not invent issue numbers or story records to satisfy the template.

## Required PR description

Use all six headings in the [template](../.github/PULL_REQUEST_TEMPLATE.md); replace its guidance with evidence and keep the description current as scope changes:

| Section | Required information |
| --- | --- |
| Summary | Concrete problem, resulting behavior, and the reason for the change; highlight a meaningful trade-off if needed. |
| Traceability | Actual PRD document and GitHub story issue matching the branch, or a reasoned repository-maintenance exception; matching Closes/Refs link for stories. |
| Scope | Included/excluded behavior and **Artifact updates**: assess code/tests, config, dependencies/lock/exports, schemas/migrations, data instructions, diagrams, ADRs, and Markdown; explain unaffected categories. |
| Validation | Commands and observed results, acceptance/regression evidence, and UI screenshots or a reason they do not apply. Follow the [TDD evidence requirements](testing.md#pr-evidence-and-completion), including observed Red/Green results or a justified exemption. Distinguish synthetic fixtures from genuine source evidence; disclose checks not run and why. |
| Risk and rollout | Affected behavior, privacy/source-permission/dependency/configuration/schema impacts, rollout steps, and a practical rollback/recovery approach. For an inapplicable item, use `N/A — <reason>`. |
| Review checklist | Author self-review, recorded local checks, documentation/contract updates or explained exceptions, and review for sensitive/generated data. Check items only after doing the work. |

Do not paste the diff, repeat every changed filename, leave empty fields or `TODO`/`TBD`, or claim an unperformed check passed. Describe the final change for someone who has not seen the conversation. Use a draft while required work remains.

## Enforcement and review

The required **Python quality and offline verification** job runs [scripts/check_pr.py](../scripts/check_pr.py) for PR events. It validates branch/title formats, matching issue identifiers, existing local PRD documents, required description fields, and completed author checklist items. Its separate metadata step uses `--verify-issue` and a read-only GitHub token to confirm that each story is an open issue rather than a PR, has `type:story` and exactly the matching `prd:NN` label, and links the parent PRD. Inaccessible/missing issues or lookup failures fail the check. Repository-maintenance and genuine Dependabot PRs skip story lookup. Application tests and `make check` remain offline. An untouched PR template fails.

PR title/body edits rerun CI alongside code updates; issue edits alone do not. Rerun PR checks after material story changes and keep required checks green for the latest revision before merge. No label transition or Projects synchronization runs automatically.

Before publishing a PR, validate its prepared description locally:

```sh
uv run --frozen python -m scripts.check_pr \
  --branch chore/repo-branch-and-pr-standards \
  --title "chore(repo): enforce branch and pull request standards" \
  --body-file /tmp/pr-description.md --verify-issue
```

Use that same file with `gh pr create --base main --title "..." --body-file /tmp/pr-description.md`. If updating an existing PR, use `gh pr edit --title "..." --body-file /tmp/pr-description.md` and wait for its new CI run. The default template becomes available in GitHub's PR form after this change is merged into `main`.

Story validation with `--verify-issue` requires authenticated `gh` and repository issue-read access. Omitting the flag provides an offline structural preview and explicitly does not verify issue existence/labels; use the flag before publishing a story PR. CI always includes it.

Mechanical validation cannot prove evidence is truthful, scope is appropriate, or tests were written before implementation. Reviewers must assess acceptance coverage, recorded TDD evidence or exemptions, changes requested in review, data/source impacts, and rollback feasibility. GitHub enforces the latest required CI result and resolved conversations. This standard does not add an independent approval requirement to the current single-maintainer setup.

References: [GitHub guidance for reviewable PRs](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes), [GitHub PR templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).
