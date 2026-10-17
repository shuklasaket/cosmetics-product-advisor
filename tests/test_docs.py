from pathlib import Path

from scripts.check_docs import check_documentation, check_drawio, check_markdown


def test_repository_documentation_has_valid_local_references() -> None:
    assert check_documentation(Path(__file__).resolve().parents[1]) == []


def test_missing_and_machine_specific_links_are_reported(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text("[missing](absent.md)\n[local](/private/document.md)\n", encoding="utf-8")

    errors = check_markdown(document, tmp_path)

    assert len(errors) == 2
    assert "missing" in errors[0]
    assert "portable" in errors[1]


def test_code_examples_and_web_links_do_not_require_network(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text(
        "```md\n[example](not-a-real-file.md)\n```\n[reference](https://example.org/)\n",
        encoding="utf-8",
    )

    assert check_markdown(document, tmp_path) == []


def test_dangling_diagram_connector_is_reported(tmp_path: Path) -> None:
    diagram = tmp_path / "broken.drawio"
    diagram.write_text(
        '<mxfile><diagram name="Broken"><mxGraphModel><root>'
        '<mxCell id="0"/><mxCell id="1" parent="0"/>'
        '<mxCell id="edge" edge="1" parent="1" source="absent" target="1">'
        '<mxGeometry relative="1" as="geometry"/></mxCell>'
        "</root></mxGraphModel></diagram></mxfile>",
        encoding="utf-8",
    )

    assert any("dangling connector" in error for error in check_drawio(diagram))
