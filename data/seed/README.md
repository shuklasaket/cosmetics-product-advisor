# India genuine starter catalog

`catalog-v1.json` is the reviewed catalog for the non-commercial agentic-development
demo. The original US-019 starter records remain intact. US-035 adds ten exact
storefront-reviewed products and five formulation-reviewed products on 25 November
2026. The current seed contains 25 products available for online purchase in India:
twelve sunscreens and thirteen moisturisers. Prices are regular/MRP values in INR paise,
not temporary promotional prices. Optional ratings, review counts, claims and
sponsorship values are absent and therefore remain unknown.

## Source policy (`us-019-source-policy-v1`)

The repository maintainer approved manual use of the linked public India product pages
for this demo on 2026-10-19. The approval is limited to exact product identity, pack,
ingredient declaration, regular INR price, India-online availability, source URLs and
verification metadata. Images, review content/counts, marketing prose, certificates,
temporary promotions and personal data are excluded. No scraping or live adapter is
used, and no physical product purchase or back-of-pack inspection is required.

On 25 November 2026 the maintainer confirmed that this factual-only policy also covers
newly reviewed official brand storefront pages. The first US-035 expansion uses only
official Minimalist, Foxtale, Re'equil and Aqualogica India pages. It does not use
Bigbasket, images, reviews, promotions or copied marketing claims. Identity, exact pack,
regular price and India-online availability are selected; ingredient declarations remain
unknown for those ten additions because that increment did not claim a formulation review.

Each source record preserves the original HTTPS page, the access and reuse boundary,
attribution and check date. Manufacturer and retailer evidence have distinct source and
evidence IDs. For Minimalist Light Fluid SPF 50 50 ml, the complete ingredient list is
from the manufacturer page while price and online availability are from Nykaa.

The factual compilation and its original selection/resolution work are provided for this
repository's non-commercial demo. Underlying product names and page content remain the
property of their respective owners. Recheck the source policy and linked pages before
using the data for another purpose or redistributing it outside this repository.

## US-035 expanded source policy (`us-035-expanded-source-policy-v1`)

The maintainer's 25 November 2026 factual-only approval also covers a bounded manual
review of five exact-pack Open Beauty Facts records and the corresponding India retailer
or manufacturer identity, price and availability pages. The reviewed mapping is recorded
in `prd02-release-evidence-v1.json`; it retains only the allowlisted exact identity,
pack and ingredient declaration required by the refresh contract, never a raw source
payload. Open Beauty Facts contributors receive the attribution and ODbL terms recorded
in the source registration. Product images, reviews, marketing content, personal data,
and unreviewed candidate records are excluded.

The five reviewed mappings are La Shield Fisico Matte Sunscreen Gel 50 g, CeraVe Oil
Control Moisturising Gel-Cream 52 ml, CeraVe Moisturising Lotion 236 ml, Bioderma
Atoderm Cream Ultra 200 ml, and CeraVe Facial Moisturising Lotion AM SPF 30 52 ml.
Candidate records with a missing, corrupted, or formulation-mismatched declaration were
deliberately excluded. These records establish mapping and accepted-outcome evidence;
they do not refresh the pre-existing selected catalog facts.

## Legacy fact recheck — 26 November 2026

All ten original products were manually checked against their linked official
India storefronts and the reviewed Nykaa exact-pack offer. The seed appends 72 new
observations and 20 dated source records, then explicitly selects the new evidence;
the October observations remain available for provenance and comparison. The current
regular/MRP prices changed for Aqualogica Glow+ Dewy 50 g from ₹499 to ₹449 and
Re'equil Ceramide & Hyaluronic Acid 100 g from ₹295 to ₹395. Discounted sale prices
were not selected. The current [Foxtale Glow page](https://foxtale.in/products/glow-sunscreen)
and [Nykaa Minimalist 50 ml offer](https://www.nykaa.com/minimalist-light-fluid-spf-50-face-sunscreen/p/20540004?redirectpath=slug)
are recorded as new source snapshots rather than rewriting earlier source records.

| Rechecked exact pack | Reviewed source | Selected regular/MRP |
| --- | --- | ---: |
| Aqualogica Glow+ Dewy 50 g | [Official storefront](https://aqualogica.in/products/glow-dewy-sunscreen-50g) | ₹449 |
| Foxtale Glow 50 ml | [Official storefront](https://foxtale.in/products/glow-sunscreen) | ₹375 |
| Foxtale Hydrating Ceramide 50 ml | [Official storefront](https://foxtale.in/products/hydrating-moisturizer-with-ceramide-copy-1) | ₹335 |
| Mamaearth Beetroot Hydraful 50 g | [Official storefront](https://mamaearth.in/products/beetroot-hydraful-hyaluronic-acid-face-moisturizer-50ml) | ₹349 |
| Mamaearth Cocoa Rich 50 g | [Official storefront](https://mamaearth.in/products/cocoa-rich-moisturizing-cream-with-cocoa-butter-vitamin-e-for-deep-nourishment-50-g) | ₹149 |
| Mamaearth Vitamin C Daily Glow SPF 50 PA++++ 50 g | [Official storefront](https://mamaearth.in/products/vitamin-c-daily-glow-sunscreen-with-vitamin-c-turmeric-for-sun-protection-glow-50-g) | ₹399 |
| Minimalist Light Fluid SPF 50 50 ml | [Official formulation](https://beminimalist.co/products/light-fluid-spf-50-sunscreen?variant=45875483115681), [Nykaa offer](https://www.nykaa.com/minimalist-light-fluid-spf-50-face-sunscreen/p/20540004?redirectpath=slug) | ₹499 |
| Minimalist Vitamin B5 50 g | [Official storefront](https://beminimalist.co/products/vitamin-b5-10-moisturizer) | ₹349 |
| Re'equil Ceramide & Hyaluronic Acid 100 g | [Official storefront](https://www.reequil.com/collections/all/products/ceramide-hyaluronic-acid-moisturiser-for-normal-to-dry-skin) | ₹395 |
| Re'equil Ultra Matte SPF 50 50 g | [Official storefront](https://www.reequil.com/products/ultra-matte-dry-touch-sunscreen-gel-spf-50-pa) | ₹645 |

The 50 g Mamaearth Vitamin C Daily Glow sunscreen has a new dated source snapshot. The
maintainer confirmed the current official page's SPF 50 **PA++++** label corrects the
same exact catalog variant. Its 2026-10 PA+++ observation remains immutable history;
the current PA++++ identity, price, and India availability evidence is selected.

## Verification and loading

The timestamps record manual page review, not continuous availability. Validate and load
into a newly initialized local database from the repository root:

```sh
uv run --frozen python -m scripts.import_catalog data/seed/catalog-v1.json \
  --database database/advisor.db
uv run --frozen python -m scripts.import_prd02_release_evidence \
  data/seed/prd02-release-evidence-v1.json database/advisor.db
```

The first load reports `committed`; replaying either unchanged input reports `unchanged`
for its stored evidence and does not duplicate records. The evidence importer reports
five committed (or replayed) mappings and accepted outcomes. See [the importer guide]
(../../docs/catalog-import.md) for database initialization, reports, recovery and
resolution-change rules.

For an existing database loaded from the older seed, stop the app, make a validated
backup, and review the new source observations before importing with
`--update-resolutions`. Without that explicit flag the importer rejects changed
selections and leaves the prior catalog intact. The PA-rating correction changes the
immutable product identity, so an existing database retains its prior catalog and
rejects this seed; initialize a fresh database from the corrected seed instead.
Re-run both release verifiers after loading it.

```sh
uv run --frozen python -m scripts.import_catalog data/seed/catalog-v1.json \
  --database database/advisor.db --update-resolutions
```

