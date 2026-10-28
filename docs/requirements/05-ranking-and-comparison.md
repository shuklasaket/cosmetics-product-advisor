# PRD 05 — Deterministic Ranking and Product Comparison

Status: Draft · Dependencies: [PRD 01](01-catalog-and-search.md), [PRD 03](03-ingredient-screening.md), [PRD 04](04-review-analysis.md) · Source: report §§1, 7–8, 15, 17

## Problem and outcome

Shoppers need a comparable shortlist that respects their hard constraints before considering preferences or ratings. A transparent calculation makes the selection reproducible and exposes where evidence is weak.

**Minimum deployable increment:** a “Find products” action that returns up to three eligible products, score breakdowns, exclusion/verification reasons, and a side-by-side comparison in Streamlit.

**Smallest delivery path:** implement one pure-Python Policy and Ranking role over the
existing catalog, PRD 03 screening outcome, and PRD 04 validated findings. The current
structured form calls the same typed service directly. Freeze and version the proposed
weights and component definitions before release; do not add a second recommendation
engine or model call for the later conversation.

## Goals and scope

- Satisfy every tested hard requirement before scoring.
- Return identical eligibility, scores, and ordering for identical versioned inputs.
- Explain fewer-than-three and zero-result outcomes without relaxing constraints.

Include deterministic selection and factual evidence labels. AI-written explanations belong to PRD 06. Do not introduce purchase/checkout, sponsored boosts, multi-country ranking, or unsupported medical suitability claims.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| RNK-01 | The Policy and Ranking role alone filters category, India availability, inclusive INR budget, confirmed user-exclusion matches, applicable prohibition/failed restriction, and unresolved critical ingredient checks before scoring. It consumes immutable validated snapshots. Unknown/conflicting price or availability prevents eligibility; once PRD 02 exists, stale critical facts do too. Return reason codes for every withheld candidate. |
| RNK-02 | Calculate `0.35S + 0.30R + 0.20I + 0.15P`, each component on 0–100, using Python and a versioned policy. This role makes no model call. Show component values, weights, total, and evidence references. Unknown evidence contributes zero to its component rather than receiving an invented positive value. |
| RNK-03 | Use the proposed initial component definitions below and record policy parameters with each run. Do not merge ratings/counts from incompatible variants or sources. A score means comparative fit within the catalog, not effectiveness or safety probability. |
| RNK-04 | Keep sponsorship outside eligibility and scoring. Display verified yes/no or unknown sponsorship metadata. Changing only sponsorship must leave scores and order identical. Resolve equal scores using stable product ID. |
| RNK-05 | Return at most three eligible candidates in score order; show one or two when that is all that qualifies. For zero results, explain the actual limiting checks and offer editable inputs without automatically relaxing them. Verification-required products appear separately, without recommendation numbering. |
| RNK-06 | Cards and comparison table show product/pack, sourced INR price and date, relevant claims, rating/scale, total versus analyzed review counts, benefits/drawbacks, ingredient status, sponsorship, and score breakdown. Unknown facts remain visible as unknown. |
| RNK-07 | Recompute when requirements or evidence versions change. Keep a non-sensitive audit record of role, product/evidence/rule/policy versions and component scores; sensitive request fields and detailed personal exclusion reasons stay session-only. Preserve a factual results view if review analysis is unavailable. |

## Proposed initial scoring policy

- **S — suitability:** percentage of requested attributes supported by sourced claims or validated review findings. Skin type counts as one attribute and each selected finish/texture preference as one. Missing support scores zero; label claims and review observations by origin.
- **R — review evidence:** smooth a compatible 1–5 aggregate rating as `(n*r + m*C)/(n+m)`, with proposed `m=50` and `C` the mean valid rating for that category in the catalog snapshot. Normalize as `100*(adjusted-1)/4` and multiply by a coverage factor: low `0.5`, medium `0.75`, high `1.0` from PRD 04. No valid rating or analyzed reviews gives `R=0`. Record `C`; no peer average uses a documented neutral `C=3`.
- **I — ingredient evidence:** proposed 100 for a complete, sourced, current declaration with resolved relevant checks; 50 for a complete sourced declaration whose age is unknown/stale; 0 for missing evidence. Ineligible products never reach scoring. This measures evidence completeness, not ingredient safety.
- **P — price/value:** proposed `100*(1-price/budget)`, bounded to 0–100, for eligible products. For a zero budget and verified zero price, use `P=100`. Label this an affordability proxy, not pack-normalized value.

## Release verification and measures

Run the deployed shortlist with the two source example budgets, an exclusion match, and a budget yielding fewer than three results. Repeat unchanged inputs and verify byte-equivalent numeric score/order fields. Use fixed vectors for component arithmetic, the zero-budget boundary, missing reviews, ties, and stale/conflicting critical evidence.

Release targets: 100% hard-rule compliance; 100% score reproducibility; 100% sponsorship-only comparisons leave ranking unchanged; all recommended products expose provenance and limitations. Product/data reviews the proposed scoring policy before release; weight calibration is an evaluation activity, not proof of clinical suitability.
