"""US-016: model-free search against temporary SQLite and synthetic evidence only."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from test_catalog_contracts import catalog

from repositories.catalog import CatalogRepository, migrate
from schemas.catalog import CatalogEnvelope
from schemas.requirements import UserRequirements
from services.catalog_search import CatalogSearchService, CatalogUnavailableError


def product(product_id: str, **facts: object) -> dict:
    data = catalog()
    identity = data["products"][0]
    identity.update(product_id=product_id, variant=f"synthetic-{product_id}")
    for field in ("name", "category"):
        if field in facts:
            identity[field] = facts[field]
    for item in data["observations"]:
        field = item["field_name"]
        item["product_id"] = product_id
        item["evidence_id"] = f"{product_id}-{field}"
        if field in identity:
            item["value"] = identity[field]
        elif field in facts:
            item["value"] = facts[field]
    for item in data["resolutions"]:
        item["product_id"] = product_id
        item["evidence_ids"] = [f"{product_id}-{item['field_name']}"]
    return data


def store(tmp_path: Path, *products: dict) -> CatalogRepository:
    data = catalog()
    for table in ("products", "observations", "resolutions"):
        data[table] = [item for part in products for item in part[table]]
    path = tmp_path / "synthetic-catalog.db"
    migrate(path)
    repo = CatalogRepository(path)
    repo.save(CatalogEnvelope.model_validate(data))
    return repo


def request(**changes: object) -> UserRequirements:
    return UserRequirements.model_validate(
        dict(category="sunscreen", skin_type="oily", budget_inr="800") | changes
    )


def ids(result) -> list[str]:
    return [p.product_id for p in result.catalog.products]


def test_inclusive_ceiling_and_exact_category(tmp_path: Path) -> None:
    repo = store(
        tmp_path,
        product("sun-below", price_paise=79_999),
        product("sun-at", price_paise=80_000),
        product("sun-over", price_paise=80_001),
        product("moist-at", category="moisturiser", price_paise=60_000),
        product("moist-over", category="moisturiser", price_paise=60_001),
    )
    service = CatalogSearchService(repo)
    result = service.search(request())
    assert result.status == "matches"
    assert ids(result) == ["sun-at", "sun-below"]
    assert ids(service.search(request(category="moisturiser", budget_inr="600"))) == ["moist-at"]


@pytest.mark.parametrize(
    "changes",
    [
        {"price_paise": None},
        {"availability": None},
        {"availability": []},
        {"availability": ["Nepal"]},
        {"availability": ["india"]},
        {"availability": ["Indian Ocean"]},
        {"category": "moisturiser"},
    ],
)
def test_unknown_or_unsupported_facts_cannot_qualify(tmp_path: Path, changes: dict) -> None:
    repo = store(tmp_path, product("excluded", **changes), product("included"))
    assert ids(CatalogSearchService(repo).search(request())) == ["included"]


@pytest.mark.parametrize("field", ["price_paise", "availability"])
@pytest.mark.parametrize("state", ["missing", "unresolved", "other-selected"])
def test_no_fallback_to_matching_historical_facts(tmp_path: Path, field: str, state: str) -> None:
    data = product("history")
    selected = next(r for r in data["resolutions"] if r["field_name"] == field)
    if state == "missing":
        data["observations"] = [o for o in data["observations"] if o["field_name"] != field]
        data["resolutions"].remove(selected)
    else:
        original = next(o for o in data["observations"] if o["field_name"] == field)
        alternative = dict(
            original,
            evidence_id=f"history-{field}-alternative",
            value=80_001 if field == "price_paise" else ["Nepal"],
        )
        data["observations"].append(alternative)
        selected["evidence_ids"] = [alternative["evidence_id"]]
        if state == "unresolved":
            selected["status"] = "unresolved"
            selected["evidence_ids"].append(original["evidence_id"])
    repo = store(tmp_path, data)
    assert CatalogSearchService(repo).search(request()).status == "empty"


def test_zero_budget_and_multi_country_membership(tmp_path: Path) -> None:
    repo = store(
        tmp_path,
        product("free", price_paise=0, availability=["Nepal", "India"]),
        product("one-paisa", price_paise=1),
        product("unknown-price", price_paise=None),
        product("unknown-country", price_paise=0, availability=None),
    )
    assert ids(CatalogSearchService(repo).search(request(budget_inr=0))) == ["free"]


def test_case_sensitive_name_then_id_order_and_claim_invariance(tmp_path: Path) -> None:
    repo = store(
        tmp_path,
        product("tie-z", name="Alpha", skin_type_claims=["dry"]),
        product("lower", name="alpha", skin_type_claims=[]),
        product("tie-A", name="Alpha", skin_type_claims=None),
        product("accent", name="Álpha", skin_type_claims=["sensitive"]),
        product("middle", name="Beta", sponsorship="yes"),
        product("tie-a", name="Alpha"),
    )
    service = CatalogSearchService(repo)
    expected = ["tie-A", "tie-a", "tie-z", "middle", "lower", "accent"]
    for skin_type in ("oily", "dry", "combination", "normal", "sensitive"):
        result = service.search(request(skin_type=skin_type))
        assert ids(result) == expected
        assert ids(service.search(request(skin_type=skin_type))) == expected
        assert set(type(result).model_fields) == {"catalog", "filters"}
        assert result.catalog.resolved_value("tie-z", "skin_type_claims") == ("dry",)


def test_empty_result_has_active_filters_without_personal_inputs(tmp_path: Path, caplog, capsys):
    repo = store(tmp_path, product("over", price_paise=80_001))
    before = repo.path.read_bytes()
    entries = set(tmp_path.iterdir())
    result = CatalogSearchService(repo).search(
        request(exclusions=["private-exclusion-sentinel"], preferences={"finish": "private-finish"})
    )
    assert result.status == "empty"
    assert not result.catalog.products
    assert not result.catalog.observations
    assert not result.catalog.sources
    assert result.filters.model_dump() == {
        "category": "sunscreen",
        "country": "India",
        "currency": "INR",
        "budget_paise": 80_000,
    }
    assert "private" not in result.model_dump_json()
    assert "80000" not in repr(result) + repr(result.filters)
    assert repo.path.read_bytes() == before
    assert set(tmp_path.iterdir()) == entries
    assert not caplog.text
    assert capsys.readouterr() == ("", "")


def test_valid_empty_catalog_is_empty_and_detail_is_absent(tmp_path: Path) -> None:
    service = CatalogSearchService(store(tmp_path))
    result = service.search(request(budget_inr=0))
    assert result.status == "empty"
    assert result.filters.budget_paise == 0
    assert service.detail("missing") is None


def test_detail_preserves_variant_field_provenance_unknowns_and_history(tmp_path: Path) -> None:
    first = product("first", review_count=None, sponsorship=None)
    historical = dict(
        next(o for o in first["observations"] if o["field_name"] == "price_paise"),
        evidence_id="first-old-price",
        value=1,
    )
    first["observations"].append(historical)
    second = product("second", price_paise=80_001)
    repo = store(tmp_path, first, second)
    service = CatalogSearchService(repo)
    result = service.search(request())
    detail = service.detail("first")
    assert detail == result.catalog
    assert detail is not None
    assert [p.product_id for p in detail.products] == ["first"]
    assert detail.resolved_value("first", "price_paise") == 80_000
    assert detail.resolved_value("first", "review_count") is None
    assert detail.resolved_value("first", "sponsorship") is None
    by_id = {o.evidence_id: o for o in detail.observations}
    assert by_id["first-price_paise"].source_id == "retailer"
    assert by_id["first-ingredient_declaration"].source_id == "maker"
    assert by_id["first-price_paise"].source_reference == "https://example.test/facts"
    assert by_id["first-old-price"] == CatalogEnvelope.model_validate(first).observations[-1]
    assert detail.sources == CatalogEnvelope.model_validate(first).sources
    assert service.detail("second") is not None  # Detail is independent of the prior budget.
    assert service.detail("FIRST") is None
    assert not repo.detail("first' OR 1=1 --").products  # Bound as a literal, never SQL.
    assert repo.read() == CatalogEnvelope.model_validate(
        {
            **catalog(),
            **{t: first[t] + second[t] for t in ("products", "observations", "resolutions")},
        }
    )


@pytest.mark.parametrize("kind", ["missing", "corrupt", "directory", "foreign", "newer", "links"])
def test_unavailable_and_invalid_catalog_are_distinct_from_empty(tmp_path: Path, kind: str) -> None:
    import sqlite3

    path = tmp_path / "private-path-sentinel.db"
    if kind == "corrupt":
        path.write_text("private-payload-sentinel SQL")
    elif kind == "directory":
        path.mkdir()
    elif kind == "foreign":
        with sqlite3.connect(path) as con:
            con.execute("CREATE TABLE other(x)")
    elif kind in ("newer", "links"):
        repo = store(tmp_path, product("over", price_paise=80_001))
        path = repo.path
        with sqlite3.connect(path) as con:
            con.execute(
                "PRAGMA user_version = 999"
                if kind == "newer"
                else "DELETE FROM resolution_evidence"
            )
    before = path.read_bytes() if path.is_file() else None
    service = CatalogSearchService(CatalogRepository(path))
    for action in (lambda: service.search(request()), lambda: service.detail("missing")):
        with pytest.raises(CatalogUnavailableError, match="restore a verified backup") as caught:
            action()
        assert "private" not in str(caught.value)
        assert "SQL" not in str(caught.value)
        assert caught.value.__suppress_context__
    if before is not None:
        assert path.read_bytes() == before
    if kind == "missing":
        assert not path.exists()


def test_invalid_request_is_rejected_before_database_access(tmp_path: Path) -> None:
    service = CatalogSearchService(CatalogRepository(tmp_path / "missing.db"))
    from decimal import Decimal

    for changes in ({"country": "Nepal"}, {"budget_inr": Decimal(-1)}, {"category": "other"}):
        forged = request().model_copy(update=changes)
        with pytest.raises(ValidationError):
            service.search(forged)


def test_paise_above_sqlite_integer_range_stays_exact(tmp_path: Path) -> None:
    ceiling = 2**63 + 123
    repo = store(
        tmp_path,
        product("at", price_paise=ceiling),
        product("over", price_paise=ceiling + 1),
    )
    assert ids(
        CatalogSearchService(repo).search(
            request(budget_inr=f"{ceiling // 100}.{ceiling % 100:02}")
        )
    ) == ["at"]


def test_forged_request_does_not_emit_raw_serializer_warnings(tmp_path: Path) -> None:
    import warnings

    service = CatalogSearchService(CatalogRepository(tmp_path / "missing.db"))
    forged = request().model_copy(update={"budget_inr": {"private-sentinel": 1}})
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError):
            service.search(forged)
    assert not recorded


def test_search_uses_one_snapshot_during_concurrent_import(tmp_path: Path, monkeypatch) -> None:
    from repositories import catalog as storage

    data = product("changing")
    repo = store(tmp_path, data)
    later = dict(
        next(o for o in data["observations"] if o["field_name"] == "price_paise"),
        evidence_id="later-price",
        value=80_001,
    )
    data["observations"].append(later)
    next(r for r in data["resolutions"] if r["field_name"] == "price_paise")["evidence_ids"] = [
        "later-price"
    ]
    updated = CatalogEnvelope.model_validate(data)
    # WAL permits a writer to commit while the reader retains its original snapshot.
    with storage.connection(repo.path) as con:
        con.execute("PRAGMA journal_mode = WAL")
    original_read = storage._read
    changed = False

    def read_then_update(con):
        nonlocal changed
        snapshot = original_read(con)
        if not changed:
            changed = True
            repo.save(updated)
        return snapshot

    monkeypatch.setattr(storage, "_read", read_then_update)
    service = CatalogSearchService(repo)
    result = service.search(request())
    assert ids(result) == ["changing"]
    assert result.catalog.resolved_value("changing", "price_paise") == 80_000
    assert service.search(request()).status == "empty"
    assert service.detail("changing").resolved_value("changing", "price_paise") == 80_001


def test_permission_failure_is_sanitized(tmp_path: Path, monkeypatch) -> None:
    from repositories import catalog as storage

    def denied(*args, **kwargs):
        raise PermissionError("private-path-and-payload")

    repo = store(tmp_path, product("present"))
    monkeypatch.setattr(storage, "connection", denied)
    service = CatalogSearchService(repo)
    for action in (lambda: service.search(request()), lambda: service.detail("present")):
        with pytest.raises(
            CatalogUnavailableError, match="Check the configured database"
        ) as caught:
            action()
        assert "private" not in str(caught.value)


@pytest.mark.parametrize("product_id", ["", " ", "first' OR 1=1 --", 1, None])
def test_detail_validates_stable_id_before_database_access(tmp_path: Path, product_id) -> None:
    service = CatalogSearchService(CatalogRepository(tmp_path / "missing.db"))
    with pytest.raises(ValidationError):
        service.detail(product_id)
