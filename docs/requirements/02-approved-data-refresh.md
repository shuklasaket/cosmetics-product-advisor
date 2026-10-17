# PRD 02 — Approved Product Data Refresh

Status: Draft · Dependencies: [PRD 01](01-catalog-and-search.md) · Source: report §§4, 11, 14, 17, 20

## Problem and outcome

Catalog facts change, and individual sources may be incomplete or unavailable. The operator needs to refresh evidence while shoppers can identify its age and inspect disagreements.

**Minimum deployable increment:** an operator refresh action in the existing app, with a real Open Beauty Facts lookup, validated updates, and visible refresh/freshness states on product details.

## Goals and scope

- Demonstrate real external retrieval for at least five genuine products and distinguish returned, missing, and rejected fields.
- Grow the verified catalog to approximately 20–30 genuine products across both supported categories.
- Preserve a usable catalog when retrieval fails and prevent conflicting facts from being silently promoted as verified.

Scope includes one external API integration and manually verified imports from official brand pages and one permitted retailer or review dataset. Automated retailer/brand scraping, scheduled refresh, and unrestricted web research are deferred.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| REF-01 | Maintain a registry of approved source endpoints, source type, attribution, access/reuse conditions, and date checked. Only configured sources are eligible for retrieval; arbitrary user-supplied URLs cannot trigger a collector. |
| REF-02 | Implement a real Open Beauty Facts lookup through a structured product-detail tool. Use stable external IDs, record requested source and outcome, and display the returned evidence. API absence or incomplete India coverage stays explicit. |
| REF-03 | Offer a manual refresh action and a validated import path for permitted brand/retailer evidence. Map source records to stable catalog IDs and require operator review for uncertain identity, pack-size, or variant matches. |
| REF-04 | Validate candidate updates before committing them. Preserve old and new provenance and a refresh outcome; rejected or partial payloads cannot erase valid fields. Repeating an identical import/refresh produces no duplicate product or evidence entries. |
| REF-05 | Retain conflicting observations. Proposed precedence: manufacturer evidence for ingredient/pack claims and an identified retailer offer for INR price/availability; Open Beauty Facts supplements gaps. Unresolved identity, ingredient, price, or availability conflicts are flagged and withheld from qualified recommendation inputs until resolved. |
| REF-06 | Show fact dates and freshness. Proposed defaults are 7 days for price/availability and 30 days for other product facts. Expired facts remain inspectable with a stale label; a failed refresh does not change their verification date. Stale price/availability cannot support a budget-qualified recommendation. |
| REF-07 | Apply proposed bounds of a 10-second timeout per attempt and at most two retries for transient failures, honoring a source's longer backoff by ending/deferring the refresh. Reuse cached responses within the freshness window; report whether evidence was fetched, cached, missing, or stale. |
| REF-08 | Expose refresh status and source errors in product details and a small operator view. On failure, retain dated local facts with a visible warning; never replace them with generated facts or mark a source as successful without an actual successful result. |

## Release verification

Launch the updated catalog, refresh a real product, and inspect its changed fact provenance. Demonstrate actual retrieval outcomes for five real product IDs; retain dated evidence of these checks. Use deterministic recorded responses for repeatable failure tests, clearly labeled as fixtures.

Exercise a timeout, rate limit, malformed payload, missing product, repeated refresh, and contradictory ingredient lists. Confirm bounded attempts, no duplicated records, unchanged last-valid facts, and visible conflict/staleness labels. Browsing verified local records still works offline.

## Success measures

- 100% of refreshed facts identify source, time, and validation outcome.
- 100% of failure fixtures preserve the last valid catalog.
- Every critical-conflict fixture is withheld from recommendation eligibility until resolved; future ranking consumes this status.

## Dependencies and decisions

The operator confirms source access and attribution before each connector/import is enabled. Engineering validates the actual API contract during implementation; this PRD does not assume complete product or review coverage. Product/data review the proposed freshness defaults before release. Manual genuine review evidence remains an allowed path for PRD 04.
