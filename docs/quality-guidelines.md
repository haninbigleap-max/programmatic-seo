# Quality Guidelines for Programmatic Pages

Programmatic SEO works when every generated page would deserve to exist even if it had been written by hand. Use these guidelines before you add data, before you launch, and after you go live.

## 1. Validate demand first

- [ ] The query pattern has real search demand. Check keyword tools, GSC queries and People Also Ask.
- [ ] You only generate combinations with demand **and** a real offering. Don't create "Pest Control in Jeddah" if you don't serve Jeddah.
- [ ] Start with the highest-value 10–20% of combinations rather than every possible permutation.
- [ ] Every page targets a distinct intent. If two combinations would show the same SERP, merge them into one page.

## 2. Make each page genuinely unique

The template is shared. The **data** must make each page different and useful.

Good sources of page-specific value:

- Local prices and currency (AED vs SAR vs GBP)
- Areas or districts served, response times and availability
- Local conditions that change the service (dust in Riyadh, humidity in Jeddah, free-zone access in Dubai)
- Local regulations, permits or approvals
- Real FAQs asked by customers in that location
- Inventory, specifications, reviews or case studies for that specific item or place

Rules of thumb:

- [ ] At least **60 words** of row-specific content per page (the default `--min-unique-words`). Raise this for competitive niches.
- [ ] Row-specific content overlaps less than **60%** with any other page (the `--max-similarity` check).
- [ ] No sentence is identical across pages except navigation, CTAs and legal text.
- [ ] Don't spin text or swap synonyms to fake uniqueness. Search engines and readers both notice.
- [ ] Facts are verified. A wrong price or a service area you don't cover is worse than no page.

## 3. On-page elements

- [ ] **Title**: unique, about 60 characters or fewer, with the primary pattern first (`Commercial Cleaning in Riyadh | ...`).
- [ ] **Meta description**: unique and includes a page-specific detail (price, response time, area).
- [ ] **H1**: matches the intent and is unique across the set.
- [ ] **Canonical**: self-referencing and absolute. Never point all pages at one canonical.
- [ ] **Language and direction**: `lang` matches the locale, and `dir="rtl"` is set for Arabic.
- [ ] **hreflang**: if you have the same page in several locales (`en-ae` / `ar-ae`), add reciprocal hreflang plus `x-default`.

## 4. Structured data

- [ ] JSON-LD is generated from the same data that's visible on the page.
- [ ] FAQ schema only includes questions and answers that appear on the page.
- [ ] No ratings or reviews unless they are real and shown on the page.
- [ ] Spot-check 5–10 pages in the Rich Results Test before launch.

## 5. Internal linking

- [ ] Every generated page is linked from at least one hub page (such as `/en-ae/commercial-cleaning/`).
- [ ] Pages link sideways to related combinations (same service in other cities, other services in the same city).
- [ ] Hub pages are linked from the main navigation or other key pages.
- [ ] No orphan pages. Verify with a crawl after publishing.

## 6. Indexation control

- [ ] Only pages that pass the quality gates go into `sitemap.xml`.
- [ ] Rows that fail are either skipped or published with `noindex, follow` until the data is improved.
- [ ] Removed combinations return 404/410 or 301 to the closest relevant page. Don't leave them as empty pages.

## 7. Launch and monitor

1. **Pilot.** Publish 10–30 pages and submit the sitemap.
2. **Wait 4–8 weeks.** Watch the GSC Pages report for "Crawled – currently not indexed" and "Duplicate without user-selected canonical". These are signs of thin or duplicate content.
3. **Measure.** Track impressions, clicks and conversions per page and per template group.
4. **Improve or prune.** Enrich pages that get impressions but no clicks. Noindex or remove pages that get nothing.
5. **Scale** only once the pilot pages are indexed and performing.

## Red flags to stop and rethink

- More than about 30% of pilot pages are not indexed after two months.
- Pages are getting impressions for the wrong locations or intents.
- You're tempted to lower `--min-unique-words` just to get more pages through.
- The only difference between two pages is the city name.
