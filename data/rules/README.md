# India limited ingredient rules

`india-limited-v1.json` is the bounded PRD 03 rule manifest. It is a reviewed
primary-source transcription for the application's two supported categories only:
sunscreen and moisturiser. It does not represent a complete list of prohibited,
restricted, safe, compliant, or suitable ingredients.

## Source review

The sole rule is checked against the Central Drugs Standard Control Organisation
(CDSCO) publication of **The Cosmetics Rules, 2020**, G.S.R. 763(E), dated
15 December 2020. Rule 39(4) prohibits hexachlorophene in cosmetics, with a narrow
soap exception. Because this application only evaluates sunscreen and moisturiser,
the exception is outside the rule's declared category scope and is not inferred.

- Official source: <https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/cos_rules/Cosmetics%20Rules%202020.pdf>
- Exact cited section: Rule 39(4), page 26 in the CDSCO PDF rendering.
- Manifest version and review date: `2026-11-26`.

The manifest preserves the authoritative document URL and section in each rule. A
future rule must name its exact source section, category/use applicability, version,
and checked date. Rules with conditions that the current typed evaluator cannot
represent stay out of the manifest; missing or conflicting product evidence remains
unresolved. Do not add regulatory facts from search snippets, marketing pages, or
model output.

## Loading and recovery

`RuleManifestStore` validates the entire local JSON file before replacing its
in-memory rule set. A malformed, duplicate-key, oversized, or provenance-invalid
update leaves the last validated public rule set active. If no valid set has loaded,
the screening panel reports that reviewed rules are unavailable and makes no finding.

The manifest contains no shopper data. Avoid-list entries are evaluated from Streamlit
session state only and are never added to this file, a catalog record, a log, or an
export.
