# Branch names and pull request standards

Every human-authored change uses these rules, the [PR template](../.github/PULL_REQUEST_TEMPLATE.md), and the branch → PR → required CI → squash merge workflow in [CONTRIBUTING.md](../CONTRIBUTING.md). Keep each PR focused on one independently reviewable outcome. Draft PRs can show unfinished work; all requirements apply before merge.

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
- Story IDs are unique across the repository, remain stable when a story changes PRD, and are never reused. A GitHub issue number is a separate identifier unless explicitly mapped to the story.
- Keep the story's Markdown record in the repository with a filename starting `US-001-` and ending `.md`; link that actual file from the PR. The parent PRD must also be linked. No story records are created by this standards setup.
- Use `repo-` only for shared repository work such as CI, tooling, process, or documentation. Explain why PRD/story references do not apply; it is not an alternative for untracked product work.
- Continue follow-up changes on an open PR's branch. Start a fresh branch from the latest `origin/main` after merge; do not reuse a merged branch.

Examples are naming illustrations, not assigned story IDs or a generated backlog. A story branch implementing another PRD could be `fix/prd-02-us-014-preserve-last-valid-price`; it must reference its real `US-014` record before it can pass the PR checks.

Genuine Dependabot PRs retain their generated `dependabot/...` names and descriptions. The automated exception checks the bot identity, GitHub account type, and same-repository origin; a human branch with that prefix receives no exception. Dependency changes still run the full required quality check and follow the merge protections.

## PR title and traceability

Use `<type>(<scope>): <outcome>` with a title of at most 100 characters. The type must match the branch. Story PRs use the uppercase story ID as scope; maintenance PRs use `repo`:

```text
feat(US-001): add catalog name search
fix(US-014): preserve the last valid price after refresh failure
chore(repo): enforce branch and pull request standards
```

For a story PR, fill the template's traceability fields with links to the actual repository records. In the published PR, use full GitHub file URLs pointing to the PR branch or a commit containing the record, especially for newly added files. For example, once the illustrated story record actually exists:

```md
PRD: [PRD-01](https://github.com/shuklasaket/cosmetics-product-advisor/blob/main/docs/requirements/01-catalog-and-search.md)
User story: [US-001](https://github.com/shuklasaket/cosmetics-product-advisor/blob/feat/prd-01-us-001-search-by-name/docs/user-stories/US-001-search-by-name.md)
Related issue: Refs #123
```

The branch, title, story label, and linked story filename must agree. The PRD link must target the corresponding document under `docs/requirements/`. The validator accepts same-repository GitHub file URLs and repository-relative paths, resolving them against the checked-out PR files without making network requests; reviewers must confirm published URLs point to the intended revision. Link the story's acceptance criteria and record the verification in the validation section. Keep a PR focused on one primary story; reference related work separately rather than silently including more stories.

For `repo-` branches, write `PRD: N/A — <reason>` and `User story: N/A — <reason>`. Related issues are optional; use `N/A` when there is none. Use `Closes #123` only when merging should close that actual GitHub issue; use `Refs #123` for partial or related work. Do not invent issue numbers or story records to satisfy the template.

## Required PR description

Use all six headings in the [template](../.github/PULL_REQUEST_TEMPLATE.md); replace its guidance with evidence and keep the description current as scope changes:

| Section | Required information |
| --- | --- |
| Summary | Concrete problem, resulting behavior, and the reason for the change; highlight a meaningful trade-off if needed. |
| Traceability | Actual PRD and story links matching the branch, or a reasoned repository-maintenance exception; related issues if any. |
| Scope | What is included and deliberately excluded so a reviewer can assess the boundary. |
| Validation | Commands and observed results, acceptance/regression evidence, and UI screenshots or a reason they do not apply. Distinguish synthetic fixtures from genuine source evidence; disclose checks not run and why. |
| Risk and rollout | Affected behavior, privacy/source-permission/dependency/configuration/schema impacts, rollout steps, and a practical rollback/recovery approach. For an inapplicable item, use `N/A — <reason>`. |
| Review checklist | Author self-review, recorded local checks, documentation/contract updates or explained exceptions, and review for sensitive/generated data. Check items only after doing the work. |

Do not paste the diff, repeat every changed filename, leave empty fields or `TODO`/`TBD`, or claim an unperformed check passed. Describe the final change for someone who has not seen the conversation. Use a draft while required work remains.

## Enforcement and review

The required **Python quality and offline verification** job runs [scripts/check_pr.py](../scripts/check_pr.py) for PR events. It validates branch/title formats, matching story identifiers and existing local reference files, required description fields, and completed author checklist items. An untouched template fails. PR title/body edits rerun CI alongside code updates; required checks must be green for the latest revision before merge.

Before publishing a PR, validate its prepared description locally:

```sh
uv run --frozen python -m scripts.check_pr \
  --branch chore/repo-branch-and-pr-standards \
  --title "chore(repo): enforce branch and pull request standards" \
  --body-file /tmp/pr-description.md
```

Use that same file with `gh pr create --base main --title "..." --body-file /tmp/pr-description.md`. If updating an existing PR, use `gh pr edit --title "..." --body-file /tmp/pr-description.md` and wait for its new CI run. The default template becomes available in GitHub's PR form after this change is merged into `main`.

Mechanical validation cannot prove evidence is truthful or scope is appropriate. Reviewers must assess acceptance coverage, changes requested in review, data/source impacts, and rollback feasibility. GitHub enforces the latest required CI result and resolved conversations. This standard does not add an independent approval requirement to the current single-maintainer setup.

References: [GitHub guidance for reviewable PRs](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes), [GitHub PR templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).
