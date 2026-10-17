# PRD 01 — Verified Catalog and Product Search

Status: Draft · Dependencies: None · Source: report §§1–4, 12–14, 20–21

## Problem and outcome

Shoppers need a way to compare real cosmetic products without receiving invented facts. The first release provides a locally runnable Streamlit catalog: enter basic requirements, see matching genuine products, and inspect their evidence.

**Minimum deployable increment:** a searchable catalog and product-detail screen backed by SQLite, usable without an LLM or live internet access after initial data preparation.

## Goals and scope

- Return only products matching the requested category, country, and maximum price in every acceptance fixture.
- Make the source and verification date of every displayed product fact inspectable.
- Make both categories usable with a proposed starter dataset of at least 10 genuine products, at least five per category; expand toward 20–30 in PRD 02.

This release provides discovery, not a suitability recommendation. Ingredient evaluation, review summaries, weighted ranking, conversation, and preference persistence belong to later releases.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| CAT-01 | Provide a local launch guide, pinned dependencies, and a repeatable catalog-loading path. A clean supported environment can launch the catalog with the supplied verified seed data; database creation does not require an LLM. |
| CAT-02 | Validate category, supported skin type, India, and a required non-negative INR budget with Pydantic. Blank/negative/non-numeric budgets and unsupported values show actionable errors before search; zero is accepted. Collect optional exclusions/preferences as session data for later use. |
| CAT-03 | Store stable product IDs, brand/name, category, country availability, INR price, pack size, declared skin-type claims, rating and rating scale, total review count, ingredient declaration/completeness, sponsorship status, and provenance. Missing optional facts remain null/unknown; missing identity or source information rejects the imported record. |
| CAT-04 | Retain field-level source IDs and dates, so a retailer price and manufacturer ingredient list can coexist without implying the same origin. Validate records on import, report rejected rows, and prevent duplicate product IDs from silently creating duplicate products. |
| CAT-05 | Search by exact category, supported availability, and inclusive maximum price. Products with unknown price or availability stay outside budget-qualified results. Skin-type claims remain labeled claims and do not silently become hard eligibility rules. |
| CAT-06 | Display matching product cards/list entries and a detail view with original source links, dates, unknown fields, and sponsorship as yes/no/unknown when supported by evidence. Default order is name then stable product ID, without a suitability score. |
| CAT-07 | Show explicit empty, invalid-data, and unavailable-database states. A zero-result search explains the active filters and lets the shopper change them; it never fills results from model knowledge. A failed import preserves the last valid catalog. |

## Release verification

Deploy the local app and search sunscreen at ₹800 and moisturiser at ₹600 using the verified seed dataset. Check that a product exactly at the price ceiling is included, an over-budget product is omitted, and unknown availability is not treated as India availability. Inspect one product whose price and ingredients have different sources.

Repeat with a zero budget, a negative budget, an unsupported country, a duplicate ID, and a missing database. Expected results are a truthful empty state or a clear validation/recovery message. Restart the app and verify the imported catalog remains searchable.

## Success measures

- 100% hard-filter correctness across the release fixtures.
- 100% of displayed non-null product facts have traceable provenance.
- Proposed usability target: at least four of five pilot users find and inspect a matching product within two minutes; collect a baseline rather than claiming prior performance.

## Dependencies and decisions

The operator must prepare genuine product evidence and record permitted reuse before distribution. No example record from the report counts as seed evidence. Local deployment is the release target; hardware/model selection can wait until PRD 04.
