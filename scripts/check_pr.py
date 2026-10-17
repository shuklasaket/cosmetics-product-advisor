"""Validate human PR conventions using metadata as data, never executable commands."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts.check_docs import strip_html_comments

TYPES = "feat|fix|docs|refactor|test|chore|ci|build|perf|revert"
GITHUB_FILES = "/shuklasaket/cosmetics-product-advisor/blob/"
BRANCH = re.compile(
    rf"(?P<type>{TYPES})/"
    r"(?:prd-(?P<prd>[0-9]{2})-us-(?P<story>[0-9]{3,})-|repo-)"
    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
)
FIELDS = {
    "Summary": (),
    "Traceability": ("PRD", "User story"),
    "Scope": ("Included", "Excluded"),
    "Validation": ("Checks", "Acceptance criteria", "UI evidence"),
    "Risk and rollout": ("Impact", "Rollout", "Rollback"),
    "Review checklist": (),
}
CHECKLIST = (
    "I reviewed the diff and kept the PR focused on its stated scope.",
    "I ran the local checks and recorded actual results and limitations above.",
    "I updated affected documentation and contracts, or explained why no updates apply.",
    "I checked for secrets, personal data, generated files, and source-permission impacts.",
)


def is_not_applicable(value: str) -> bool:
    return re.fullmatch(r"N/A\s*[-—–:]\s*\S.+", value, flags=re.IGNORECASE) is not None


def is_complete(value: str) -> bool:
    if not value or re.fullmatch(
        r"TODO|TBD|<[^>]+>|\.\.\.", value.strip("`*_ "), flags=re.IGNORECASE
    ):
        return False
    if value.upper().startswith("N/A"):
        return is_not_applicable(value)
    return True


def has_reference(value: str, identifier: str, root: Path, *, prd: str | None = None) -> bool:
    """Require a matching label and an existing Markdown file inside this checkout."""
    for target in re.findall(rf"\[{re.escape(identifier)}\]\(([^)\s]+)\)", value):
        parsed = urlsplit(target)
        if (
            parsed.scheme == "https"
            and parsed.netloc == "github.com"
            and parsed.path.startswith(GITHUB_FILES)
        ):
            # Refs may contain slashes; locate a suffix that is a real checkout file.
            parts = unquote(parsed.path.removeprefix(GITHUB_FILES)).split("/")
            candidates = [Path(*parts[index:]) for index in range(1, len(parts))]
        elif not parsed.scheme and not parsed.netloc and not Path(parsed.path).is_absolute():
            candidates = [Path(unquote(parsed.path))]
        else:
            continue
        for local in candidates:
            path = (root / local).resolve()
            if (
                not path.is_relative_to(root.resolve())
                or not path.is_file()
                or path.suffix != ".md"
            ):
                continue
            if prd is not None:
                if path.parent == (root / "docs/requirements").resolve() and path.name.startswith(
                    f"{prd}-"
                ):
                    return True
            elif path.name.startswith(f"{identifier}-"):
                return True
    return False


def check_pull_request(
    branch: str,
    title: str,
    body: str,
    root: Path,
    *,
    author: str = "",
    author_type: str = "",
    same_repository: bool = False,
) -> list[str]:
    if (
        author == "dependabot[bot]"
        and author_type == "Bot"
        and same_repository
        and re.fullmatch(r"dependabot/[a-z_]+/.+", branch)
    ):
        return []

    errors: list[str] = []
    match = BRANCH.fullmatch(branch)
    prd = match.group("prd") if match else None
    story = match.group("story") if match else None
    if (
        match is None
        or len(branch) > 100
        or prd == "00"
        or (story is not None and (int(story) == 0 or str(int(story)).zfill(3) != story))
    ):
        errors.append(
            "Use the story or repository-maintenance branch format in docs/git-workflow.md."
        )
    elif match:
        scope = f"US-{story}" if story else "repo"
        prefix = f"{match.group('type')}({scope}): "
        if len(title) > 100 or not title.startswith(prefix) or not title[len(prefix) :].strip():
            errors.append("Use a PR title matching the branch type and story ID (or repo scope).")

    visible = strip_html_comments(body.replace("\r\n", "\n"))
    visible = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", visible)
    parts = re.split(r"(?m)^## ([^\n]+)\n?", visible)
    sections: dict[str, str] = {}
    for heading, content in zip(parts[1::2], parts[2::2], strict=True):
        heading = heading.strip()
        if heading in sections:
            errors.append("Keep each required PR heading exactly once.")
        sections[heading] = content.strip()

    values: dict[str, str] = {}
    for heading, fields in FIELDS.items():
        content = sections.get(heading, "")
        if not is_complete(content):
            errors.append(f"Fill the required section: {heading}.")
        for field in fields:
            entries = re.findall(rf"(?m)^{re.escape(field)}:[ \t]*(.*)$", content)
            value = entries[0].strip() if len(entries) == 1 else ""
            values[field] = value
            if not is_complete(value):
                errors.append(f"Fill {field}: with evidence or N/A — reason on the same line.")

    if match and prd and story:
        if not has_reference(values.get("PRD", ""), f"PRD-{prd}", root, prd=prd):
            errors.append("Link the branch's parent PRD to its existing repository document.")
        if not has_reference(values.get("User story", ""), f"US-{story}", root):
            errors.append("Link the branch's story ID to its existing US-numbered Markdown record.")
    elif match and not story:
        if not all(is_not_applicable(values.get(field, "")) for field in ("PRD", "User story")):
            errors.append(
                "Repository maintenance needs a reasoned N/A for both PRD and User story."
            )

    checklist = sections.get("Review checklist", "")
    for item in CHECKLIST:
        if not re.search(rf"(?m)^- \[[xX]\] {re.escape(item)}[ \t]*$", checklist):
            errors.append("Complete all four author checklist items after doing the work.")
            break
    if re.search(r"(?m)^- \[ \] ", checklist):
        errors.append("Resolve unfinished checklist items before merging.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--event", type=Path, help="GitHub pull_request event JSON")
    source.add_argument("--branch", help="Branch name for a local preview")
    parser.add_argument("--title")
    parser.add_argument("--body-file", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.event:
            event = json.loads(args.event.read_text(encoding="utf-8"))
            pr = event["pull_request"]
            errors = check_pull_request(
                str(pr["head"]["ref"]),
                str(pr["title"]),
                str(pr["body"] or ""),
                root,
                author=str(pr["user"]["login"]),
                author_type=str(pr["user"]["type"]),
                same_repository=pr["head"]["repo"]["full_name"] == event["repository"]["full_name"],
            )
        else:
            if not args.title or not args.body_file:
                parser.error("--branch also requires --title and --body-file")
            errors = check_pull_request(
                args.branch, args.title, args.body_file.read_text(encoding="utf-8"), root
            )
    except (OSError, ValueError, KeyError, TypeError):
        print("Could not read the PR metadata; supply a valid event or local description file.")
        return 1
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Branch and pull request standards: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
