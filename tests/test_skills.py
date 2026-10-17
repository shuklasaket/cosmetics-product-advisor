import json
from pathlib import Path

import pytest

from scripts.check_skills import check_skills, file_hashes


@pytest.fixture
def skill_repository(tmp_path: Path) -> Path:
    folder = tmp_path / ".agents/skills/example"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        "---\nname: example\ndescription: A synthetic validation fixture.\n---\nRead inputs.\n",
        encoding="utf-8",
    )
    registry = {
        "schema_version": 1,
        "skills": [
            {"name": "example", "source": {"kind": "project"}, "sha256": file_hashes(folder)}
        ],
    }
    (tmp_path / ".agents/skills-sources.json").write_text(json.dumps(registry), encoding="utf-8")
    return tmp_path


def test_reviewed_project_skill_inventory_is_valid() -> None:
    assert check_skills(Path(__file__).resolve().parents[1]) == []


def test_edited_or_unrecorded_skill_content_is_detected(skill_repository: Path) -> None:
    assert check_skills(skill_repository) == []
    folder = skill_repository / ".agents/skills/example"
    (folder / "unreviewed.py").write_text("print('synthetic fixture')\n", encoding="utf-8")

    assert any("hash drift" in error for error in check_skills(skill_repository))


def test_hash_refresh_does_not_make_invalid_helper_syntax_valid(skill_repository: Path) -> None:
    folder = skill_repository / ".agents/skills/example"
    (folder / "invalid.py").write_text("if:\n", encoding="utf-8")
    path = skill_repository / ".agents/skills-sources.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["skills"][0]["sha256"] = file_hashes(folder)
    path.write_text(json.dumps(registry), encoding="utf-8")

    assert any("invalid helper Python syntax" in error for error in check_skills(skill_repository))


def test_external_skill_symlink_is_rejected(skill_repository: Path, tmp_path: Path) -> None:
    external = tmp_path / "external.txt"
    external.write_text("Synthetic external reference\n", encoding="utf-8")
    (skill_repository / ".agents/skills/example/external.txt").symlink_to(external)

    assert check_skills(skill_repository)


def test_upstream_skills_need_immutable_revision_and_preserved_license(
    skill_repository: Path,
) -> None:
    path = skill_repository / ".agents/skills-sources.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    entry = registry["skills"][0]
    entry.update(
        source={
            "kind": "github",
            "repository": "example/synthetic",
            "commit": "main",
            "path": "example",
        },
        license="MIT",
        license_files=["LICENSE"],
        upstream_sha256=entry["sha256"].copy(),
        modified_files=[],
    )
    path.write_text(json.dumps(registry), encoding="utf-8")

    errors = check_skills(skill_repository)

    assert any("immutable" in error for error in errors)
    assert any("license/notice file missing" in error for error in errors)
