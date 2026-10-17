"""Check local documentation links and native draw.io structure without network access."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

LINK = re.compile(r"\]\((<[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)")


def check_markdown(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK.finditer(line):
            target = match.group(1).strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme in {"http", "https", "mailto"} or not parsed.path:
                continue
            if parsed.scheme or Path(parsed.path).is_absolute():
                errors.append(f"{path}:{number}: use a portable repository link: {target}")
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                errors.append(f"{path}:{number}: missing or external local target: {target}")
    return errors


def check_drawio(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        document = ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return [f"{path}: invalid XML"]
    diagrams = document.findall("diagram")
    if not diagrams:
        return [f"{path}: no editable diagram pages"]
    for diagram in diagrams:
        label = f"{path}: {diagram.get('name', 'unnamed page')}"
        cells = diagram.findall("mxGraphModel/root/mxCell")
        identifiers = [cell.get("id") for cell in cells]
        if None in identifiers or len(set(identifiers)) != len(identifiers):
            errors.append(f"{label}: missing or duplicate cell IDs")
        if not {"0", "1"}.issubset(identifiers):
            errors.append(f"{label}: missing root layers")
        for cell in cells:
            parent = cell.get("parent")
            if parent is not None and (parent not in identifiers or parent == cell.get("id")):
                errors.append(f"{label}: invalid parent for {cell.get('id')}")
            if cell.get("edge") == "1":
                geometry = cell.find("mxGeometry")
                if cell.get("source") not in identifiers or cell.get("target") not in identifiers:
                    errors.append(f"{label}: dangling connector {cell.get('id')}")
                if geometry is None or geometry.get("relative") != "1":
                    errors.append(f"{label}: invalid connector geometry {cell.get('id')}")
    return errors


def check_documentation(root: Path) -> list[str]:
    documents = [root / "README.md", root / "CONTRIBUTING.md", root / "data" / "README.md"]
    documents.extend(sorted((root / "docs").rglob("*.md")))
    errors: list[str] = []
    for path in documents:
        if not path.is_file():
            errors.append(f"{path}: required document missing")
            continue
        errors.extend(check_markdown(path, root))
    for path in sorted((root / "docs").rglob("*.drawio")):
        errors.extend(check_drawio(path))
    return errors


def main() -> int:
    errors = check_documentation(Path(__file__).resolve().parents[1])
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Documentation links and draw.io structure: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
