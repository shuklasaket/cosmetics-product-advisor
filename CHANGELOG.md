# Changelog

Notable product and development-workflow changes are recorded here using the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. See the
[maintenance policy](CONTRIBUTING.md#changelog) for when and how to update this file.

## Unreleased

No tagged or published releases have been recorded. The entries below describe the
requirements, development foundation, and repository workflow; no PRD feature release
has been delivered by this work.

### Added

- Scoped category and use-condition checks, explicit failed restrictions and exact
  concentration limits, conflicting-evidence withholding, and public evidence/rule
  fingerprints complete the deterministic PRD 03 evaluator. Findings retain the
  checked conditions, rule version and date; genuine India rules remain pending.
  ([#56](https://github.com/shuklasaket/cosmetics-product-advisor/issues/56))

- Deterministic, synthetic-first PRD 03 ingredient-rule contracts and evaluator with
  provenance-required rules, curated alias matching, conservative incomplete-evidence
  handling, and versioned eligibility outcomes. No genuine regulatory rules or personal
  exclusions are persisted. (Refs #56)

- Five exact, reviewed Open Beauty Facts mappings and accepted payload-free refresh
  outcomes for a bounded set of complete-formulation, exact-pack India variants. The
  release-evidence importer registers only the reviewed source metadata and allowlisted
  factual fields; records with missing, corrupted, or mismatched formulation data remain
  excluded. The PRD 02 release gate deliberately remains incomplete until legacy selected
  facts are refreshed and final release evidence is recorded. (Refs #35)

- Ten reviewed official-storefront variants expand the permitted India catalog to
  20 products, split evenly across sunscreen and moisturiser. Fact-level identity,
  pack, regular INR price, India availability, attribution and verification metadata
  remain explicit; unreviewed ingredients and Open Beauty Facts mappings stay unknown.
  (Refs #35)

- Payload-free persistence of returned, missing, and rejected field statuses when a
  PRD 02 exact-variant review requires further work. Candidate facts and mappings remain
  uncommitted, so last-valid catalog evidence is preserved while operators retain the
  genuine retrieval outcome for review. (Refs #35)

- A strict, read-only PRD 02 release verifier for the approved 20–30-variant catalog,
  reviewed refresh mappings, source permission/attribution, and the accepted 7-day
  price/availability and 30-day other-fact freshness limits. It fails closed and
  remains payload-free until genuine evidence is complete. (Refs #35)

- Explicit per-product Open Beauty Facts refresh controls, evidence freshness/conflict
  and validation details, and a read-only operator status view. Approved sources and
  reviewed mappings are required; failures retain dated local facts, and retrieved
  candidates remain unverified. Owned HTTP clients now close after each request.
  ([#37](https://github.com/shuklasaket/cosmetics-product-advisor/issues/37))

- Review-gated, transactional PRD 02 refresh commits with exact variant mappings,
  append-only unverified observations, durable payload-free outcomes, schema-v3 backup
  migration, unchanged last-valid catalog facts on rejected or failed input, and
  qualification withheld for unresolved critical conflicts.
  ([#39](https://github.com/shuklasaket/cosmetics-product-advisor/issues/39))
- Deterministic source-precedence, conflict-retention, freshness, and critical-evidence
  qualification policy for future recommendation inputs; catalog browsing remains unchanged.
  ([#38](https://github.com/shuklasaket/cosmetics-product-advisor/issues/38))
- A bounded, read-only Open Beauty Facts adapter with allowlisted v3 barcode lookups,
  10-second per-attempt limits, retry/backoff limits, payload-free validated candidates,
  explicit missing/partial/invalid outcomes, and a public-evidence-only fresh/stale
  in-memory cache. Exact catalog mapping and transactional commits remain separate work.
  ([#36](https://github.com/shuklasaket/cosmetics-product-advisor/issues/36))
- Approved-source registry persistence and strict HTTPS destination/redirect authorization,
  with disabled-by-default registrations, schema-v2 backup migration, external-ID mapping,
  and typed payload-free refresh outcomes with bounded attempts and sanitized error codes.
  ([#34](https://github.com/shuklasaket/cosmetics-product-advisor/issues/34))
- A reproducible offline PRD 01 release runbook and read-only verifier for the genuine
  India catalog, with target-Mac launch/restart evidence, genuine UI provenance checks,
  and validated backup/restore acceptance coverage.
  ([#20](https://github.com/shuklasaket/cosmetics-product-advisor/issues/20))
- A permitted, versioned India-online starter catalog with five genuine sunscreens and
  five genuine moisturisers, fact-level manufacturer/retailer provenance, documented
  non-commercial source boundaries, repeatable import and budget-search verification.
  ([#19](https://github.com/shuklasaket/cosmetics-product-advisor/issues/19))
- Sourced Streamlit catalog results and product details with stable ordering,
  field-level attribution and verification timestamps, explicit unknown/sponsorship
  states, declared-claim wording, inert external text, and recoverable empty or
  unavailable-catalog states. Genuine starter data remains pending.
  ([#18](https://github.com/shuklasaket/cosmetics-product-advisor/issues/18))
- A private Streamlit search form for supported category and skin-type choices,
  India/INR defaults, exact budget validation, optional exclusions/preferences,
  sanitized recovery errors, and complete session clearing. Catalog result display
  remains pending. ([#17](https://github.com/shuklasaket/cosmetics-product-advisor/issues/17))
- Read-only catalog search and detail services with exact category/India availability
  and inclusive integer-paise budget filters, stable case-sensitive name/ID ordering,
  field evidence/history, and distinct empty/unavailable outcomes. Catalog UI and
  genuine seed remain pending.
  ([#16](https://github.com/shuklasaket/cosmetics-product-advisor/issues/16))
- A local `catalog-v1` JSON import command with whole-batch validation, sanitized row
  reports, explicit resolution replacements, repeat-import handling, and atomic writes
  that reject stale snapshots while preserving evidence history.
  ([#15](https://github.com/shuklasaket/cosmetics-product-advisor/issues/15))
- SQLite catalog evidence storage with immutable observation history, explicit resolutions,
  integrity constraints, atomic schema initialization/upgrades, and validated backup/restore
  into a new path. Import/search/catalog UI and genuine seed remain pending.
  ([#14](https://github.com/shuklasaket/cosmetics-product-advisor/issues/14))
- Pydantic shopper-request and `catalog-v1` evidence contracts with exact integer-paise
  conversion, explicit unknowns, field-level provenance and conflict resolution, variant
  and rating-snapshot checks, and sanitized validation messages. Storage, imports and
  the catalog UI remain pending.
  ([#13](https://github.com/shuklasaket/cosmetics-product-advisor/issues/13))
- A `prd-to-stories` repository skill for drafting PRD story plans and creating or
  updating GitHub backlogs when requested, with requirement coverage, acceptance
  scenarios, verification, dependencies, and documented chat prompts.
  ([#11](https://github.com/shuklasaket/cosmetics-product-advisor/pull/11))
- A curated changelog and same-PR changelog review in the development completion process.
  ([#7](https://github.com/shuklasaket/cosmetics-product-advisor/pull/7))
- GitHub story and PRD tracking forms, managed labels and backlog views, readiness and
  ownership rules, dependency and parallel-work planning, and live story-issue verification
  in PR checks. ([#6](https://github.com/shuklasaket/cosmetics-product-advisor/pull/6))
- TDD guidance covering Red/Green/Refactor, test boundaries, evidence, and justified
  exemptions in PRs. ([#5](https://github.com/shuklasaket/cosmetics-product-advisor/pull/5))
- Seven project development skills with pinned provenance, local integration boundaries,
  and offline integrity checks. ([#4](https://github.com/shuklasaket/cosmetics-product-advisor/pull/4))
- A local Streamlit development preview, validated configuration, pinned Python/uv
  dependencies, offline quality checks and CI, data-intake templates, and setup/recovery
  guidance. The preview does not implement catalog search or recommendations.
  ([9046596](https://github.com/shuklasaket/cosmetics-product-advisor/commit/90465964e6278b811c35e011a35660d03c87b9b0))
- Nine incremental PRDs, shared technical requirements, editable architecture diagrams,
  and a proposed architecture decision record.
  ([862bef8](https://github.com/shuklasaket/cosmetics-product-advisor/commit/862bef8013150930b343b84418adaac9a6dc989b))

### Changed

- Rechecked all ten original India catalog products with append-only source and fact
  history. Selected regular prices now reflect ₹449 for Aqualogica Glow+ Dewy 50 g
  and ₹395 for Re'equil Ceramide & Hyaluronic Acid 100 g. The maintainer confirmed
  the Mamaearth Vitamin C Daily Glow 50 g PA++++ correction for the same exact
  variant; the new selected evidence lets the strict PRD 02 gate pass on a fresh
  catalog while the earlier PA+++ history remains inspectable. (Refs #35)

- Story PR issue validation now falls back to the repository's fixed public GitHub
  issue endpoint if the local `gh` credential is unavailable or expired. The fallback
  is read-only, bounded, and fails closed, while authenticated `gh` remains preferred.
  PRD 02 freshness checks now evaluate explicitly selected facts so immutable,
  superseded provenance remains auditable without being mistaken for current evidence.
  (Refs #35)

- Replanned the remaining PRD 02–09 work around a trusted LangGraph controller and
  exactly five fixed, least-privilege roles for intake/clarification, catalog evidence,
  review evidence, policy/ranking, and explanation/citation. The revision adds typed
  role handoffs, central limits/redaction, and role-attributed verification while keeping
  existing catalog behavior unchanged.

- Replanned the remaining PRD 02–09 work around the implemented catalog and
  source contracts, with smaller per-release delivery paths, a single editable
  architecture view, and a proposed incremental architecture decision. No runtime
  behavior or completed PRD 01 requirement changed.

- Defined the developer agent story lifecycle and linked the shared Kanban project,
  with required issue-label/Project Status updates and read-back verification,
  readiness and ownership gates, rework/blocker handling, and completion only after
  the user's merge and verified acceptance evidence.

- Reserved final PR review and merging for the user. Agents hand off open PRs with
  verification results and must not merge, enable auto-merge, or use merge queues,
  including for documentation and maintenance work.

- Added five PlantUML sequence diagrams for evidence refresh, bounded
  review analysis, conversational recommendation, cancellation, and opt-in preference
  memory, with requirement traceability in the architecture guide.
- Redesigned the architecture documentation into three editable views with inline
  previews: local system boundaries, recommendation decisions and fallback paths,
  and evidence/preference/session-data separation. The diagrams retain the planned
  MVP scope and proposed decision status.
- Standardized user stories on As a / I want / so that outcomes and stable numbered
  Given/When/Then acceptance scenarios, with explicit PRD requirement traceability and
  criterion-to-verification mapping in issue and PR guidance.
  ([#8](https://github.com/shuklasaket/cosmetics-product-advisor/pull/8))
- Standardized numbered story branches, PR titles and traceability, and required PR
  evidence/checklist validation.
  ([#3](https://github.com/shuklasaket/cosmetics-product-advisor/pull/3))
- Required the branch/PR/CI review workflow, an up-to-date base, resolved review
  conversations, and protected squash merges into `main`.
  ([#2](https://github.com/shuklasaket/cosmetics-product-advisor/pull/2))
- Updated the CI uv setup action from 9.0.0 to 10.3.0.
  ([#1](https://github.com/shuklasaket/cosmetics-product-advisor/pull/1))
