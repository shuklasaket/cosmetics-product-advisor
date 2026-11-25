"""US-035 strict PRD 02 release-gate checks."""

import json
from datetime import date
from pathlib import Path

from repositories.catalog import migrate
from scripts.verify_prd02_release import verify_prd02_release
from services.catalog_import import import_catalog

SEED = Path(__file__).resolve().parents[1] / "data/seed/catalog-v1.json"


def test_prd02_gate_fails_closed_until_genuine_catalog_and_refresh_history_exist(
    tmp_path: Path,
) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"

    report = verify_prd02_release(database, today=date(2026, 11, 25))

    assert report.status == "failed"
    assert report.product_count == 10
    assert report.freshness_limits_days == {"price_availability": 7, "other_facts": 30}
    assert "catalog must contain between 20 and 30 exact product variants" in report.failures
    assert "at least five exact reviewed variant mappings are required" in report.failures


def test_prd02_gate_checks_selected_facts_not_retained_superseded_history(tmp_path: Path) -> None:
    """Old evidence remains inspectable without failing a current-fact freshness check."""
    refreshed = json.loads(SEED.read_text(encoding="utf-8"))
    replacement_ids: dict[str, str] = {}
    for observation in list(refreshed["observations"]):
        replacement_id = f"fresh-{observation['evidence_id']}"
        replacement_ids[observation["evidence_id"]] = replacement_id
        refreshed["observations"].append(
            {
                **observation,
                "evidence_id": replacement_id,
                "retrieved_at": "2026-11-25T12:00:00Z",
                "verified_at": "2026-11-25T12:00:00Z",
                "content_version": "manual-page-review:2026-11-25",
                "snapshot_id": f"fresh-{observation['snapshot_id']}",
            }
        )
    for resolution in refreshed["resolutions"]:
        resolution["evidence_ids"] = [replacement_ids[item] for item in resolution["evidence_ids"]]

    batch = tmp_path / "fresh-selected-catalog.json"
    batch.write_text(json.dumps(refreshed), encoding="utf-8")
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(batch, database).status == "committed"

    report = verify_prd02_release(database, today=date(2026, 11, 25))

    assert "catalog facts exceed the approved freshness window" not in report.failures
