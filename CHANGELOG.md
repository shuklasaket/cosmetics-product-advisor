# Changelog

Notable product and development-workflow changes are recorded here using the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. See the
[maintenance policy](CONTRIBUTING.md#changelog) for when and how to update this file.

## Unreleased

No tagged or published releases have been recorded. The entries below describe the
requirements, development foundation, and repository workflow; no PRD feature release
has been delivered by this work.

### Added

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
