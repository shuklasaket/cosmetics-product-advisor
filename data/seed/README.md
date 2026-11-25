# India genuine starter catalog

`catalog-v1.json` is the reviewed catalog for the non-commercial agentic-development
demo. The original US-019 starter records remain intact, and US-035 adds ten exact
products reviewed on 25 November 2026. The current seed contains 20 products available
for online purchase in India: ten sunscreens and ten moisturisers. Prices are regular/MRP
values in INR paise, not temporary promotional prices. Optional ratings, review counts,
claims and sponsorship values are absent and therefore remain unknown.

## Source policy (`us-019-source-policy-v1`)

The repository maintainer approved manual use of the linked public India product pages
for this demo on 2026-10-19. The approval is limited to exact product identity, pack,
ingredient declaration, regular INR price, India-online availability, source URLs and
verification metadata. Images, review content/counts, marketing prose, certificates,
temporary promotions and personal data are excluded. No scraping or live adapter is
used, and no physical product purchase or back-of-pack inspection is required.

On 25 November 2026 the maintainer confirmed that this factual-only policy also covers
newly reviewed official brand storefront pages. The US-035 expansion uses only official
Minimalist, Foxtale, Re'equil and Aqualogica India pages. It does not use Bigbasket,
images, reviews, promotions or copied marketing claims. Identity, exact pack, regular
price and India-online availability are selected; ingredient declarations remain unknown
for these ten additions because this increment does not claim a complete formulation
review or an Open Beauty Facts match.

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

