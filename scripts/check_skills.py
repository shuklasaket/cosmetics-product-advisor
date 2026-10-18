"""Verify the project skill inventory and recorded integrity without running helpers."""

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def file_hashes(folder: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if folder.is_symlink():
        raise ValueError("Skill folders must be checked-in files, not external symlinks.")
    for path in sorted(folder.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("Skill resources must not be symlinks.")
        if path.is_file():
            result[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def check_skills(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        registry = json.loads((root / ".agents/skills-sources.json").read_text(encoding="utf-8"))
        if registry["schema_version"] != 1 or not registry["skills"]:
            return ["Invalid or empty project skill registry."]
        names: set[str] = set()
        skills_root = root / ".agents/skills"
        for entry in registry["skills"]:
            name = entry["name"]
            if not isinstance(name, str) or not NAME.fullmatch(name) or name in names:
                return ["Skill names must be unique lowercase directory names."]
            names.add(name)
            folder = skills_root / name
            actual = file_hashes(folder)
            if not actual or actual != entry["sha256"]:
                errors.append(
                    f"{name}: file inventory/hash drift; review changes and refresh hashes."
                )
            content = (folder / "SKILL.md").read_text(encoding="utf-8")
            frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
            if not frontmatter or not re.search(
                rf"(?m)^name:[ \t]*(['\"]?){re.escape(name)}\1[ \t]*$", frontmatter[1]
            ):
                errors.append(f"{name}: missing frontmatter or name does not match directory.")
            elif not re.search(r"(?m)^description:[ \t]*\S", frontmatter[1]):
                errors.append(f"{name}: missing discovery description.")
            for relative in actual:
                if relative.endswith(".py"):
                    try:
                        ast.parse((folder / relative).read_text(encoding="utf-8"))
                    except SyntaxError:
                        errors.append(f"{name}: invalid helper Python syntax in {relative}.")
            source = entry["source"]
            if source["kind"] == "github":
                if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
                    errors.append(f"{name}: upstream must use an immutable full Git revision.")
                if not re.fullmatch(r"[\w.-]+/[\w.-]+", source["repository"]):
                    errors.append(f"{name}: invalid upstream repository.")
                upstream_path = Path(source["path"])
                if upstream_path.is_absolute() or ".." in upstream_path.parts:
                    errors.append(f"{name}: invalid upstream skill path.")
                if not entry["license"] or not entry["license_files"]:
                    errors.append(f"{name}: record the upstream license and notice files.")
                for license_file in entry["license_files"]:
                    if license_file not in actual:
                        errors.append(f"{name}: required license/notice file missing.")
                changed = {
                    path
                    for path, digest in entry["upstream_sha256"].items()
                    if actual.get(path) != digest
                }
                if changed != set(entry["modified_files"]):
                    errors.append(f"{name}: upstream differences must match declared adaptations.")
            elif source["kind"] != "project":
                errors.append(f"{name}: unsupported skill source.")
        installed = {path.name for path in skills_root.iterdir() if path.is_dir()}
        if installed != names:
            errors.append("Installed skill directories must match the reviewed registry.")
    except (OSError, ValueError, KeyError, TypeError):
        errors.append(
            "Could not validate the skill registry; check its schema, files, and symlinks."
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-hashes", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.refresh_hashes:
        path = root / ".agents/skills-sources.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        for entry in registry["skills"]:
            if not NAME.fullmatch(entry["name"]):
                raise ValueError("Invalid skill directory name.")
            entry["sha256"] = file_hashes(root / ".agents/skills" / entry["name"])
        path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        print("Installed skill hashes refreshed; review the manifest diff before committing.")
    errors = check_skills(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Project skill inventory, provenance, integrity, and helper syntax: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
