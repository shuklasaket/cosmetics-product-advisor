"""Merge-gate regressions; all story references here are temporary synthetic stubs."""

import json
import sys
from pathlib import Path

import pytest

from scripts.check_docs import strip_html_comments
from scripts.check_pr import check_pull_request, main

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "chore/repo-branch-and-pr-standards"
TITLE = "chore(repo): enforce branch and pull request standards"


@pytest.fixture
def completed_description() -> str:
    body = (ROOT / ".github/PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    entries = {
        "PRD": "N/A — repository workflow maintenance only.",
        "User story": "N/A — no product story is implemented.",
        "Included": "Branch naming and required PR metadata validation.",
        "Excluded": "Product features and new story records.",
        "Checks": "make check — passed using synthetic policy fixtures.",
        "Acceptance criteria": "Valid PRs pass; incomplete or mismatched metadata fails.",
        "UI evidence": "N/A — application screens do not change.",
        "Impact": "Merge-gate behavior changes; no product or personal data changes.",
        "Rollout": "Merge the reviewed PR and use the updated template.",
        "Rollback": "Revert the policy change through another reviewed PR.",
    }
    for field, value in entries.items():
        body = body.replace(f"\n{field}:\n", f"\n{field}: {value}\n")
    return body.replace(
        "<!-- Explain the problem, resulting behavior, and why this approach fits. -->",
        "Require traceable PRs because undocumented changes are difficult to review.",
    ).replace("- [ ]", "- [x]")


def test_completed_repository_template_passes(completed_description: str) -> None:
    assert check_pull_request(BRANCH, TITLE, completed_description, ROOT) == []


def test_evidence_can_discuss_placeholder_handling(completed_description: str) -> None:
    body = completed_description.replace(
        "Require traceable PRs because undocumented changes are difficult to review.",
        "Reject the literal placeholder `TBD` in empty fields; preserve substantive evidence.",
    )

    assert check_pull_request(BRANCH, TITLE, body, ROOT) == []


def test_story_ids_must_match_existing_repository_records(
    tmp_path: Path, completed_description: str
) -> None:
    requirements = tmp_path / "docs/requirements"
    requirements.mkdir(parents=True)
    (requirements / "01-synthetic-prd.md").write_text("# Synthetic reference stub\n")
    story = tmp_path / "US-001-synthetic-reference.md"
    story.write_text("# Synthetic reference stub; not a product user story\n")
    body = completed_description.replace(
        "PRD: N/A — repository workflow maintenance only.",
        "PRD: [PRD-01](docs/requirements/01-synthetic-prd.md)",
    ).replace(
        "User story: N/A — no product story is implemented.",
        "User story: [US-001](US-001-synthetic-reference.md)",
    )

    assert (
        check_pull_request("feat/prd-01-us-001-search", "feat(US-001): add search", body, tmp_path)
        == []
    )

    github_body = body.replace(
        "(US-001-synthetic-reference.md)",
        "(https://github.com/shuklasaket/cosmetics-product-advisor/blob/"
        "feat/prd-01-us-001-search/US-001-synthetic-reference.md)",
    )
    assert not check_pull_request(
        "feat/prd-01-us-001-search", "feat(US-001): add search", github_body, tmp_path
    )
    assert check_pull_request(
        "feat/prd-01-us-001-search",
        "feat(US-001): add search",
        github_body.replace("github.com/shuklasaket", "github.com/another-owner"),
        tmp_path,
    )

    story.unlink()
    errors = check_pull_request(
        "feat/prd-01-us-001-search", "feat(US-001): add search", body, tmp_path
    )
    assert any("existing US-numbered" in error for error in errors)


@pytest.mark.parametrize(
    "branch",
    [
        "feat/catalog-search",
        "feat/prd-00-us-001-search",
        "feat/prd-01-us-000-search",
        "feat/prd-01-us-0001-search",
        "feat/prd-01-us-001-Search",
        "chore/repo-snake_case",
        "chore/repo-double--hyphen",
        "chore/repo-" + "a" * 100,
    ],
)
def test_invalid_branch_conventions_block_merge(branch: str, completed_description: str) -> None:
    errors = check_pull_request(branch, TITLE, completed_description, ROOT)
    assert any("branch format" in error for error in errors)


def test_title_scope_must_match_the_branch(completed_description: str) -> None:
    errors = check_pull_request(
        BRANCH, "feat(US-001): unrelated scope", completed_description, ROOT
    )
    assert any("PR title matching" in error for error in errors)


def test_untouched_template_and_hidden_metadata_do_not_pass(completed_description: str) -> None:
    template = (ROOT / ".github/PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    visible = strip_html_comments(completed_description)
    hidden = f"<!--\n{visible}\n-->\n```md\n{visible}\n```"

    assert check_pull_request(BRANCH, TITLE, template, ROOT)
    assert check_pull_request(BRANCH, TITLE, hidden, ROOT)


@pytest.mark.parametrize(
    "before,after",
    [
        ("- [x] I reviewed", "- [ ] I reviewed"),
        ("UI evidence: N/A — application screens do not change.", "UI evidence: N/A"),
        ("Checks: make check — passed using synthetic policy fixtures.", "Checks: TBD"),
    ],
)
def test_incomplete_evidence_is_rejected(
    before: str, after: str, completed_description: str
) -> None:
    assert check_pull_request(BRANCH, TITLE, completed_description.replace(before, after), ROOT)


@pytest.mark.parametrize(
    "author,author_type,same_repository,allowed",
    [
        ("dependabot[bot]", "Bot", True, True),
        ("maintainer", "User", True, False),
        ("dependabot[bot]", "User", True, False),
        ("dependabot[bot]", "Bot", False, False),
    ],
)
def test_dependabot_exception_cannot_be_claimed_by_a_human_or_fork(
    author: str, author_type: str, same_repository: bool, allowed: bool
) -> None:
    errors = check_pull_request(
        "dependabot/github_actions/example-1.2.3",
        "chore(deps): update action",
        "Generated dependency update.",
        ROOT,
        author=author,
        author_type=author_type,
        same_repository=same_repository,
    )
    assert (errors == []) is allowed


def test_edited_event_uses_metadata_as_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, completed_description: str
) -> None:
    repository = {"full_name": "example/synthetic-repository"}
    marker = tmp_path / "must-not-be-executed"
    body = completed_description.replace(
        "Merge-gate behavior", f"$(touch {marker}) Merge-gate behavior"
    )
    event = {
        "action": "edited",
        "repository": repository,
        "pull_request": {
            "head": {"ref": BRANCH, "repo": repository},
            "title": TITLE,
            "body": body,
            "user": {"login": "maintainer", "type": "User"},
        },
    }
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_pr", "--event", str(path)])

    assert main() == 0
    assert not marker.exists()

    changed_event = json.loads(path.read_text(encoding="utf-8"))
    changed_event["pull_request"]["body"] = "Required metadata removed after opening the PR."
    path.write_text(json.dumps(changed_event), encoding="utf-8")
    assert main() == 1
