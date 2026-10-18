"""Ordered catalog schema migrations; statements execute inside one transaction."""

# JSON retains exact Decimal text/UTC timestamps and nullable/tuple facts from catalog-v1.
# Generated keys cannot drift from the payload and permit native relational constraints.
FIELDS = (
    "brand",
    "name",
    "category",
    "variant",
    "pack_size",
    "availability",
    "price_paise",
    "skin_type_claims",
    "rating",
    "review_count",
    "ingredient_declaration",
    "ingredient_completeness",
    "sponsorship",
)
FIELD_SQL = ",".join(f"'{field}'" for field in FIELDS)


def key(name: str) -> str:
    return f"{name} TEXT GENERATED ALWAYS AS (json_extract(payload, '$.{name}')) STORED NOT NULL"


SCHEMA_V1 = (
    f"""CREATE TABLE products (
        payload TEXT NOT NULL CHECK(json_valid(payload)),
        {key("product_id")}, {key("brand")}, {key("name")},
        {key("category")}, {key("variant")},
        UNIQUE(product_id), UNIQUE(brand, name, category, variant),
        CHECK(category IN ('sunscreen','moisturiser')),
        CHECK(length(trim(brand)) > 0 AND length(trim(name)) > 0 AND length(trim(variant)) > 0)
    )""",
    f"""CREATE TABLE sources (
        payload TEXT NOT NULL CHECK(json_valid(payload)),
        {key("source_id")}, {key("source_type")},
        UNIQUE(source_id),
        CHECK(source_type IN ('manufacturer','retailer','dataset','document')),
        CHECK(json_type(payload, '$.enabled') IN ('true','false'))
    )""",
    f"""CREATE TABLE observations (
        payload TEXT NOT NULL CHECK(json_valid(payload)),
        {key("evidence_id")}, {key("product_id")}, {key("source_id")},
        {key("field_name")}, {key("validation_status")},
        UNIQUE(evidence_id), UNIQUE(evidence_id, product_id, field_name),
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        FOREIGN KEY(source_id) REFERENCES sources(source_id),
        CHECK(field_name IN ({FIELD_SQL})),
        CHECK(validation_status IN ('verified','unverified')),
        CHECK(json_type(payload, '$.value') IS NOT NULL),
        CHECK(json_type(payload, '$.value') = 'null' OR CASE
            WHEN field_name IN ('price_paise','review_count') THEN
                json_type(payload, '$.value') = 'integer' AND
                json_extract(payload, '$.value') >= 0
            WHEN field_name = 'category' THEN
                json_extract(payload, '$.value') IN ('sunscreen','moisturiser')
            WHEN field_name = 'ingredient_completeness' THEN
                json_extract(payload, '$.value') IN ('complete','partial','unknown')
            WHEN field_name = 'sponsorship' THEN
                json_extract(payload, '$.value') IN ('yes','no','unknown')
            WHEN field_name IN ('availability','skin_type_claims') THEN
                json_type(payload, '$.value') = 'array'
            WHEN field_name = 'rating' THEN json_type(payload, '$.value') = 'object'
                AND coalesce(
                    CAST(json_extract(payload, '$.value.scale_min') AS REAL) >= 0 AND
                    CAST(json_extract(payload, '$.value.scale_max') AS REAL) >=
                        CAST(json_extract(payload, '$.value.scale_min') AS REAL) AND
                    CAST(json_extract(payload, '$.value.score') AS REAL) BETWEEN
                        CAST(json_extract(payload, '$.value.scale_min') AS REAL) AND
                        CAST(json_extract(payload, '$.value.scale_max') AS REAL), 0)
            ELSE json_type(payload, '$.value') = 'text' AND
                length(trim(json_extract(payload, '$.value'))) > 0 END),
        CHECK(CASE WHEN field_name = 'price_paise' THEN
            json_extract(payload, '$.country') IS 'India' AND
            json_extract(payload, '$.currency') IS 'INR'
            ELSE json_extract(payload, '$.country') IS NULL AND
                 json_extract(payload, '$.currency') IS NULL END)
    )""",
    f"""CREATE TABLE resolutions (
        payload TEXT NOT NULL CHECK(json_valid(payload)),
        {key("product_id")}, {key("field_name")}, {key("status")},
        UNIQUE(product_id, field_name),
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        CHECK(field_name IN ({FIELD_SQL})), CHECK(status IN ('selected','unresolved')),
        CHECK(json_extract(payload, '$.policy_version') IS 'explicit-selection-v1'),
        CHECK(json_type(payload, '$.evidence_ids') IS 'array' AND
              json_array_length(payload, '$.evidence_ids') > 0)
    )""",
    """CREATE TABLE resolution_evidence (
        product_id TEXT NOT NULL, field_name TEXT NOT NULL, evidence_id TEXT NOT NULL,
        PRIMARY KEY(product_id, field_name, evidence_id),
        FOREIGN KEY(product_id, field_name) REFERENCES resolutions(product_id, field_name),
        FOREIGN KEY(evidence_id, product_id, field_name)
            REFERENCES observations(evidence_id, product_id, field_name)
    )""",
    """CREATE TRIGGER supported_skin_claims BEFORE INSERT ON observations
        WHEN NEW.field_name = 'skin_type_claims'
        AND json_type(NEW.payload, '$.value') != 'null' AND EXISTS (
            SELECT 1 FROM json_each(NEW.payload, '$.value')
            WHERE type != 'text' OR value NOT IN ('oily','dry','combination','normal','sensitive')
        ) BEGIN SELECT RAISE(ABORT, 'Unsupported skin claim'); END""",
    *(
        f"""CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table}
        BEGIN SELECT RAISE(ABORT, 'Catalog history is immutable'); END"""
        for table in ("products", "sources", "observations")
        for action in ("UPDATE", "DELETE")
    ),
)

MIGRATIONS: tuple[tuple[str, ...], ...] = (SCHEMA_V1,)
