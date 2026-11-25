"""US-035: reviewed release mappings persist without a raw source payload."""

from datetime import date
from pathlib import Path

from repositories.catalog import migrate
from scripts.import_prd02_release_evidence import import_prd02_release_evidence
from scripts.verify_prd02_release import verify_prd02_release
from services.catalog_import import import_catalog

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data/seed/catalog-v1.json"
EVIDENCE = ROOT / "data/seed/prd02-release-evidence-v1.json"


def test_reviewed_evidence_persists_five_exact_mappings_and_outcomes(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"

    report = import_prd02_release_evidence(EVIDENCE, database)

    assert report.status == "committed"
    assert (report.mappings, report.accepted_outcomes) == (5, 5)
    gate = verify_prd02_release(database, today=date(2026, 11, 25))
    assert (gate.reviewed_mapping_count, gate.accepted_refresh_count) == (5, 5)
    assert gate.failures == ("catalog facts exceed the approved freshness window",)


def test_reviewed_evidence_replay_is_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"

    assert import_prd02_release_evidence(EVIDENCE, database).status == "committed"
    assert import_prd02_release_evidence(EVIDENCE, database).status == "committed"
