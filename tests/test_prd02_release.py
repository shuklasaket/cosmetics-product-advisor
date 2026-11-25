"""US-035 strict PRD 02 release-gate checks."""

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
