"""Merge-gate regressions using synthetic PRDs and issue metadata."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_pr as pr_checks
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
        "Artifact updates": "Workflow docs and metadata checks; other artifacts unaffected.",
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


@pytest.fixture
def story_description(tmp_path: Path, completed_description: str) -> str:
    requirements = tmp_path / "docs/requirements"
    requirements.mkdir(parents=True)
    (requirements / "01-synthetic-prd.md").write_text("# Synthetic reference stub\n")
    return (
        completed_description.replace(
            "PRD: N/A — repository workflow maintenance only.",
            "PRD: [PRD-01](docs/requirements/01-synthetic-prd.md)",
        )
        .replace(
            "User story: N/A — no product story is implemented.",
            "User story: [US-042](https://github.com/shuklasaket/cosmetics-product-advisor/issues/42)",
        )
        .replace("Related issue: N/A", "Related issue: Closes #42")
    )


@pytest.mark.parametrize("number", [42, 1000])
@pytest.mark.parametrize("action", ["Closes", "Refs"])
def test_story_issue_links_pass_without_a_duplicate_markdown_record(
    number: int, action: str, tmp_path: Path, story_description: str
) -> None:
    story = str(number).zfill(3)
    body = (
        story_description.replace("US-042", f"US-{story}")
        .replace("/issues/42", f"/issues/{number}")
        .replace("Closes #42", f"{action} #{number}")
    )
    assert not check_pull_request(
        f"feat/prd-01-us-{story}-search", f"feat(US-{story}): add search", body, tmp_path
    )


@pytest.mark.parametrize(
    "target",
    [
        "https://github.com/another-owner/cosmetics-product-advisor/issues/42",
        "https://github.com/shuklasaket/cosmetics-product-advisor/issues/43",
        "https://github.com/shuklasaket/cosmetics-product-advisor/pull/42",
        "https://github.com/shuklasaket/cosmetics-product-advisor/issues/042",
        "https://github.com/shuklasaket/cosmetics-product-advisor/issues/42?other=1",
        "https://github.com/shuklasaket/cosmetics-product-advisor/issues/42#issuecomment-1",
        "http://github.com/shuklasaket/cosmetics-product-advisor/issues/42",
        "US-042-synthetic-reference.md",
    ],
)
def test_story_links_require_the_matching_canonical_repository_issue(
    target: str, tmp_path: Path, story_description: str
) -> None:
    (tmp_path / "US-042-synthetic-reference.md").write_text("# Obsolete synthetic stub\n")
    body = story_description.replace(
        "https://github.com/shuklasaket/cosmetics-product-advisor/issues/42", target
    )
    errors = check_pull_request(
        "feat/prd-01-us-042-search", "feat(US-042): add search", body, tmp_path
    )
    assert any("GitHub issue" in error for error in errors)


def test_story_pr_still_requires_the_existing_parent_prd(
    tmp_path: Path, story_description: str
) -> None:
    (tmp_path / "docs/requirements/01-synthetic-prd.md").unlink()
    errors = check_pull_request(
        "feat/prd-01-us-042-search", "feat(US-042): add search", story_description, tmp_path
    )
    assert any("parent PRD" in error for error in errors)


def test_related_issue_must_match_the_story(tmp_path: Path, story_description: str) -> None:
    errors = check_pull_request(
        "feat/prd-01-us-042-search",
        "feat(US-042): add search",
        story_description.replace("Closes #42", "Closes #43"),
        tmp_path,
    )
    assert any("Related issue" in error for error in errors)


@pytest.fixture
def story_issue() -> dict[str, object]:
    return {
        "number": 42,
        "state": "open",
        "labels": [{"name": "type:story"}, {"name": "prd:01"}],
        "body": "### PRD\n[PRD-01](docs/requirements/01-synthetic-prd.md)",
    }


def test_live_story_metadata_matches_the_parent_prd(
    tmp_path: Path, story_description: str, story_issue: dict[str, object]
) -> None:
    assert pr_checks.check_story_issue(story_issue, "01", 42, tmp_path) == []


@pytest.mark.parametrize(
    "changed",
    [
        {"number": 43},
        {"pull_request": {}},
        {"state": "closed"},
        {"labels": []},
        {"labels": None},
        {"labels": [{"name": "type:story"}, {"name": "prd:02"}]},
        {"labels": [{"name": "type:story"}, {"name": "prd:01"}, {"name": "prd:02"}]},
        {"body": "[PRD-02](docs/requirements/02-synthetic-prd.md)"},
    ],
)
def test_invalid_live_story_metadata_cannot_pass(
    changed: dict[str, object],
    tmp_path: Path,
    story_description: str,
    story_issue: dict[str, object],
) -> None:
    assert pr_checks.check_story_issue(story_issue | changed, "01", 42, tmp_path)


def test_live_lookup_uses_the_fixed_repository_and_issue_number(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    story_description: str,
    story_issue: dict[str, object],
) -> None:
    def github_api(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command == ["gh", "api", "repos/shuklasaket/cosmetics-product-advisor/issues/42"]
        assert kwargs.get("timeout") == 30
        return subprocess.CompletedProcess(command, 0, json.dumps(story_issue), "")

    monkeypatch.setattr(subprocess, "run", github_api)
    assert pr_checks.verify_story_issue("feat/prd-01-us-042-search", tmp_path) == []


@pytest.mark.parametrize("output,returncode", [("secret remote error", 1), ("not json", 0)])
def test_live_lookup_fails_closed_without_exposing_remote_payloads(
    monkeypatch: pytest.MonkeyPatch, output: str, returncode: int, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode, output, output),
    )
    errors = pr_checks.verify_story_issue("feat/prd-01-us-042-search", tmp_path)
    assert errors
    assert output not in " ".join(errors)


def test_live_lookup_timeout_is_a_sanitized_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def timeout(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, 30, output="private remote response")

    monkeypatch.setattr(subprocess, "run", timeout)
    errors = pr_checks.verify_story_issue("feat/prd-01-us-042-search", tmp_path)
    assert errors
    assert "private remote response" not in " ".join(errors)


def test_cli_runs_live_verification_only_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    story_description: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    body_file = tmp_path / "body.md"
    body_file.write_text(story_description)
    monkeypatch.setattr(pr_checks, "__file__", str(tmp_path / "scripts/check_pr.py"))
    arguments = [
        "check_pr",
        "--branch",
        "feat/prd-01-us-042-search",
        "--title",
        "feat(US-042): add search",
        "--body-file",
        str(body_file),
    ]

    def inaccessible_issue(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "", "not found")

    monkeypatch.setattr(subprocess, "run", inaccessible_issue)
    monkeypatch.setattr(sys, "argv", arguments)
    assert main() == 0
    assert "Offline metadata only" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", [*arguments, "--verify-issue"])
    assert main() == 1
    assert "Could not read the story issue" in capsys.readouterr().out


def test_verified_dependabot_event_does_not_require_a_story(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repository = {"full_name": "shuklasaket/cosmetics-product-advisor"}
    event = {
        "repository": repository,
        "pull_request": {
            "head": {"ref": "dependabot/github_actions/example-1.2.3", "repo": repository},
            "title": "chore(deps): update action",
            "body": "Generated dependency update.",
            "user": {"login": "dependabot[bot]", "type": "Bot"},
        },
    }
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event))
    monkeypatch.setattr(sys, "argv", ["check_pr", "--event", str(path), "--verify-issue"])
    assert main() == 0


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
        (
            "Artifact updates: Workflow docs and metadata checks; other artifacts unaffected.",
            "Artifact updates:",
        ),
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
