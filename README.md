# Programmatic SEO

A small, transparent programmatic SEO pipeline: a CSV dataset of service × city combinations, a Jinja2 page template, and a Python generator with built-in quality gates that stop thin or duplicate pages from being published.

## What it does

`generate_pages.py`:

1. Reads `data/locations.csv` (one row = one landing page, such as *Commercial Cleaning in Riyadh*)
2. Runs **quality gates** on every row: required fields, valid slugs, numeric prices, and a minimum amount of row-specific content
3. Renders `templates/page_template.html` with a title, meta description, canonical, H1, unique content blocks, an FAQ section, related links and JSON-LD (`Service`, `BreadcrumbList`, `FAQPage`)
4. Checks published pages for **near-duplicate** row-specific content
5. Writes the pages to `output/<locale>/<service>/<city>/index.html`, plus `sitemap.xml` (indexable pages only) and `quality_report.csv`

## The approach

Programmatic SEO means building many pages from **structured data + a template**, where each page targets a specific long-tail query that follows a pattern (`{service} in {city}`, `{product} price in {country}`, `{tool} alternatives`).

The template provides the consistent structure. **The data has to provide the value.** If the only thing that changes between pages is the city name, you haven't built 100 useful pages. You've built one page 100 times, and search engines treat it that way.

## When programmatic SEO makes sense

Good fit:

- There's real search demand for a **repeatable query pattern**: many people search `service + city` or `product + spec`.
- You have (or can collect) **genuinely different data per page**: local prices, availability, areas covered, response times, local regulations, inventory, reviews.
- Each page can **answer the query better than a single generic page**.
- You operate in many markets, such as UAE (`en-ae`, `ar-ae`) and KSA (`en-sa`, `ar-sa`), where local details really differ.

Poor fit:

- You'd be swapping a keyword into otherwise identical text ("doorway pages").
- You don't actually offer the service in those locations.
- There's no meaningful search demand for most combinations. Check volumes and GSC data first, and launch only the combinations that matter.

## Avoiding thin and duplicate content

This repo builds the safeguards into the pipeline:

| Risk | Safeguard in this repo |
|---|---|
| Pages with no real local content | `--min-unique-words` gate counts only row-specific fields (`local_intro`, `local_insight`, FAQ answers). Rows below the threshold are skipped, or noindexed with `--noindex-thin`. |
| Missing data rendering as empty sections | Required-field check and Jinja2 `StrictUndefined`, so missing variables fail loudly instead of rendering blank |
| Near-duplicate pages | Jaccard similarity check between pages' unique content, flagged in `quality_report.csv` above `--max-similarity` |
| Thin pages getting indexed | Noindexed pages are excluded from `sitemap.xml` |
| Duplicate URLs | Duplicate locale/service/city combinations are rejected |
| Orphan pages | Every page links to related services in the same city and the same service in other cities |
| Invalid schema | JSON-LD is built in Python with `json.dumps`, so it is always valid JSON |

See [`docs/quality-guidelines.md`](docs/quality-guidelines.md) for the full editorial and launch checklist.

## Folder structure

```
programmatic-seo/
├── README.md
├── LICENSE
├── requirements.txt
├── generate_pages.py            # CSV -> quality gates -> HTML pages + sitemap + report
├── data/
│   └── locations.csv            # Sample dataset: services x cities (UAE, KSA, UK)
├── templates/
│   └── page_template.html       # Jinja2 page template
├── docs/
│   └── quality-guidelines.md    # How to keep programmatic pages useful
└── output/                      # Generated (git-ignored)
```

## How to use it

Requires Python 3.10+.

```bash
git clone https://github.com/haninbigleap-max/programmatic-seo.git
cd programmatic-seo
pip install -r requirements.txt

python generate_pages.py
```

Options:

```bash
python generate_pages.py \
  --base-url https://example.com \
  --data data/locations.csv \
  --template templates/page_template.html \
  --output output \
  --min-unique-words 60 \
  --max-similarity 0.6 \
  --noindex-thin
```

**Adapting it to your own data**

1. Replace `data/locations.csv` with your own rows. Keep the column names, or update `REQUIRED` and `UNIQUE_FIELDS` in `generate_pages.py`.
2. Write `local_intro`, `local_insight` and the FAQ answers for each row. This is where the value comes from.
3. Edit `templates/page_template.html` to match your site's layout and design system.
4. Run the generator, read `output/quality_report.csv`, fix the flagged rows and run it again.
5. Publish a small batch first, then monitor indexing and performance in Search Console before scaling up.

For Arabic pages (`ar-ae`, `ar-sa`), add rows with Arabic content. The template sets `dir="rtl"` automatically for `ar-*` locales.

## Example output

Console:

```
Rows: 9 | Published: 8 | Noindex: 0 | Skipped: 1
Output written to output/ (see quality_report.csv and sitemap.xml)
```

`output/quality_report.csv`:

| service | city | url | status | issues |
|---|---|---|---|---|
| Commercial Cleaning | Dubai | https://example.com/en-ae/commercial-cleaning/dubai/ | published | |
| Commercial Cleaning | Riyadh | https://example.com/en-sa/commercial-cleaning/riyadh/ | published | |
| Pest Control | Dubai | | skipped | missing areas_served; missing local_intro; missing local_insight; thin unique content (0 words < 60) |

Generated page head (`output/en-sa/commercial-cleaning/riyadh/index.html`):

```html
<html lang="en-sa" dir="ltr">
<head>
  <title>Commercial Cleaning in Riyadh | From SAR 1,400 | Example Co</title>
  <meta name="description" content="Commercial Cleaning in Riyadh from SAR 1,400. Within 24 hours. Covering Olaya and more.">
  <link rel="canonical" href="https://example.com/en-sa/commercial-cleaning/riyadh/">
  <script type="application/ld+json">{ "@context": "https://schema.org", "@graph": [ ...Service, BreadcrumbList, FAQPage... ] }</script>
</head>
```

## License

MIT
