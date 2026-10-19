# India genuine starter catalog

`catalog-v1.json` is the reviewed US-019 starter catalog for the non-commercial
agentic-development demo. It contains ten exact products available for online purchase
in India: five sunscreens and five moisturisers. Prices are regular/MRP values in INR
paise, not temporary promotional prices. Optional ratings, review counts, claims and
sponsorship values are absent and therefore remain unknown.

## Source policy (`us-019-source-policy-v1`)

The repository maintainer approved manual use of the linked public India product pages
for this demo on 2026-10-19. The approval is limited to exact product identity, pack,
ingredient declaration, regular INR price, India-online availability, source URLs and
verification metadata. Images, review content/counts, marketing prose, certificates,
temporary promotions and personal data are excluded. No scraping or live adapter is
used, and no physical product purchase or back-of-pack inspection is required.

Each source record preserves the original HTTPS page, the access and reuse boundary,
attribution and check date. Manufacturer and retailer evidence have distinct source and
evidence IDs. For Minimalist Light Fluid SPF 50 50 ml, the complete ingredient list is
from the manufacturer page while price and online availability are from Nykaa.

The factual compilation and its original selection/resolution work are provided for this
repository's non-commercial demo. Underlying product names and page content remain the
property of their respective owners. Recheck the source policy and linked pages before
using the data for another purpose or redistributing it outside this repository.

## Verification and loading

The timestamps record manual page review, not continuous availability. Validate and load
into a newly initialized local database from the repository root:

```sh
uv run --frozen python -m scripts.import_catalog data/seed/catalog-v1.json \
  --database database/advisor.db
```

The first load reports `committed`; replaying the unchanged seed reports `unchanged` and
does not duplicate records. See [the importer guide](../../docs/catalog-import.md) for
database initialization, reports, recovery and resolution-change rules.

