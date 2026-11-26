"""US-057 rule-manifest validation and recovery checks."""

import json
from pathlib import Path

from services.ingredient_rules import RULE_MANIFEST_PATH, RuleManifestStore


def valid_manifest() -> dict[str, object]:
    return {
        "rule_set_id": "india-limited-v1",
        "version": "2026-11-26",
        "rules": [
            {
                "rule_id": "india-hexachlorophene-rule-39-4",
                "canonical_ingredient": "Hexachlorophene",
                "aliases": [],
                "rule_type": "prohibited",
                "categories": ["sunscreen", "moisturiser"],
                "required_conditions": [],
                "max_concentration_percent": None,
                "source_reference": "https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/cos_rules/Cosmetics%20Rules%202020.pdf",
                "source_section": "Cosmetics Rules, 2020, rule 39(4)",
                "version": "G.S.R. 763(E), 15 December 2020",
                "checked_on": "2026-11-26",
            }
        ],
    }


def test_invalid_manifest_retains_the_last_valid_rule_set(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(valid_manifest()), encoding="utf-8")
    store = RuleManifestStore()

    initial = store.refresh(path)
    assert initial.status == "loaded"
    assert initial.rules is not None

    path.write_text('{"rule_set_id": "bad"}', encoding="utf-8")
    recovered = store.refresh(path)

    assert recovered.status == "retained_last_valid"
    assert recovered.rules == initial.rules
    assert recovered.message == "Rule update was rejected; the last valid rule set remains active."


def test_bundled_manifest_has_the_reviewed_rule_and_exact_primary_source() -> None:
    outcome = RuleManifestStore().refresh(RULE_MANIFEST_PATH)

    assert outcome.status == "loaded"
    assert outcome.rules is not None
    assert outcome.rules.rule_set_id == "india-limited-v1"
    assert outcome.rules.rules[0].canonical_ingredient == "Hexachlorophene"
    assert outcome.rules.rules[0].source_section == "Cosmetics Rules, 2020, rule 39(4)"
    assert outcome.rules.rules[0].source_reference.startswith("https://cdsco.gov.in/")


def test_invalid_provenance_is_rejected_without_exposing_source_content(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    manifest = valid_manifest()
    manifest["rules"][0]["source_reference"] = "not-a-reference"  # type: ignore[index]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    outcome = RuleManifestStore().refresh(path)

    assert outcome.status == "unavailable"
    assert outcome.rules is None
    assert (
        outcome.message
        == "Reviewed ingredient rules are unavailable. Try again after the rule file is restored."
    )
