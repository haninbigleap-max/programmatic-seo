#!/usr/bin/env python3
"""
generate_pages.py - Build service x city landing pages from a CSV and a Jinja2 template.

Pipeline:
  1. Read data/locations.csv
  2. Run quality gates on each row (required fields, minimum unique content)
  3. Render templates/page_template.html for each row that passes
  4. Check generated pages for near-duplicate content
  5. Write HTML files, a sitemap.xml and a quality report to output/

Rows that fail the quality gates are NOT published (or, with --noindex-thin,
they are rendered with a noindex tag and left out of the sitemap).

Usage:
    python generate_pages.py
    python generate_pages.py --base-url https://example.com --output output --min-unique-words 60
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from datetime import date
from itertools import combinations
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parent
REQUIRED = ["service", "service_slug", "city", "city_slug", "country", "locale", "currency",
            "price_from", "response_time", "areas_served", "local_intro", "local_insight"]
# Columns that hold content written specifically for this row. Templated
# boilerplate doesn't count towards uniqueness; these fields do.
UNIQUE_FIELDS = ["local_intro", "local_insight", "faq_1_a", "faq_2_a"]
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def word_set(text: str) -> set[str]:
    """Lower-cased word set used for similarity checks."""
    return set(re.findall(r"\w+", text.lower()))


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def quality_issues(row: dict[str, str], min_words: int) -> list[str]:
    """Return a list of reasons this row should not be published as-is."""
    issues = [f"missing {col}" for col in REQUIRED if not row.get(col, "").strip()]
    for col in ("service_slug", "city_slug"):
        if row.get(col) and not SLUG_RE.match(row[col]):
            issues.append(f"invalid {col} '{row[col]}'")
    if row.get("price_from") and not row["price_from"].isdigit():
        issues.append("price_from is not a whole number")
    unique_words = sum(len(row.get(c, "").split()) for c in UNIQUE_FIELDS)
    if unique_words < min_words:
        issues.append(f"thin unique content ({unique_words} words < {min_words})")
    return issues


def build_page(row: dict[str, str], base_url: str, all_rows: list[dict[str, str]]) -> dict:
    """Compute page-level values (URL, title, meta, FAQs, related links)."""
    url = f"{base_url}/{row['locale']}/{row['service_slug']}/{row['city_slug']}/"
    lang = row["locale"]
    faqs = [{"q": row[f"faq_{i}_q"], "a": row[f"faq_{i}_a"]}
            for i in (1, 2) if row.get(f"faq_{i}_q") and row.get(f"faq_{i}_a")]

    # Related links: same service in other cities of the same locale, and
    # other services in the same city. Builds a sensible internal link mesh.
    related = []
    for other in all_rows:
        if other is row or other.get("_skip"):
            continue
        same_service = other["service_slug"] == row["service_slug"] and other["locale"] == row["locale"]
        same_city = other["city_slug"] == row["city_slug"] and other["locale"] == row["locale"]
        if same_service or same_city:
            related.append({
                "url": f"{base_url}/{other['locale']}/{other['service_slug']}/{other['city_slug']}/",
                "label": f"{other['service']} in {other['city']}",
            })

    title = f"{row['service']} in {row['city']} | From {row['currency']} {int(row['price_from']):,} | Example Co"
    if len(title) > 60:  # Drop the price before truncating the brand.
        title = f"{row['service']} in {row['city']} | Example Co"
    meta = (f"{row['service']} in {row['city']} from {row['currency']} {int(row['price_from']):,}. "
            f"{row['response_time']}. Covering {row['areas_served'].split(',')[0].strip()} and more.")

    return {
        "url": url,
        "base_url": base_url,
        "lang": lang,
        "dir": "rtl" if lang.startswith("ar") else "ltr",
        "title": title,
        "meta_description": meta[:155],
        "h1": f"{row['service']} in {row['city']}",
        "areas": [a.strip() for a in row["areas_served"].split(",") if a.strip()],
        "faqs": faqs,
        "related": related[:6],
        "noindex": bool(row.get("_noindex")),
    }


def build_schema(row: dict[str, str], page: dict) -> str:
    """Build JSON-LD in Python (not in the template) so it is always valid JSON."""
    base = page["base_url"]
    graph: list[dict] = [
        {
            "@type": "Service",
            "@id": f"{page['url']}#service",
            "name": page["h1"],
            "serviceType": row["service"],
            "provider": {"@id": f"{base}/#organization"},
            "areaServed": {"@type": "City", "name": row["city"],
                           "containedInPlace": {"@type": "Country", "name": row["country"]}},
            "offers": {"@type": "Offer", "priceCurrency": row["currency"],
                       "price": row["price_from"], "url": page["url"]},
            "url": page["url"],
            "inLanguage": page["lang"],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{base}/"},
                {"@type": "ListItem", "position": 2, "name": row["service"],
                 "item": f"{base}/{row['locale']}/{row['service_slug']}/"},
                {"@type": "ListItem", "position": 3, "name": row["city"], "item": page["url"]},
            ],
        },
    ]
    if page["faqs"]:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in page["faqs"]],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False)


def write_sitemap(urls: list[str], path: Path) -> None:
    today = date.today().isoformat()
    entries = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                    f"{entries}\n</urlset>\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate programmatic SEO pages from CSV + Jinja2.")
    parser.add_argument("--data", default=str(ROOT / "data" / "locations.csv"))
    parser.add_argument("--template", default=str(ROOT / "templates" / "page_template.html"))
    parser.add_argument("--output", default=str(ROOT / "output"))
    parser.add_argument("--base-url", default="https://example.com")
    parser.add_argument("--min-unique-words", type=int, default=60,
                        help="Minimum words of row-specific content required to publish a page")
    parser.add_argument("--max-similarity", type=float, default=0.6,
                        help="Flag page pairs whose unique content overlaps more than this (0-1)")
    parser.add_argument("--noindex-thin", action="store_true",
                        help="Render thin rows with noindex instead of skipping them")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    with open(args.data, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("No rows in data file.", file=sys.stderr)
        return 1

    # --- 1. Quality gates -------------------------------------------------
    report: list[dict[str, str]] = []
    seen_urls: set[tuple[str, str, str]] = set()
    for row in rows:
        issues = quality_issues(row, args.min_unique_words)
        key = (row.get("locale", ""), row.get("service_slug", ""), row.get("city_slug", ""))
        if key in seen_urls:
            issues.append("duplicate service/city/locale combination")
        seen_urls.add(key)
        hard_fail = any(not i.startswith("thin") for i in issues)
        if issues and (hard_fail or not args.noindex_thin):
            row["_skip"] = "1"
        elif issues:
            row["_noindex"] = "1"
        row["_issues"] = "; ".join(issues)

    # --- 2. Render ----------------------------------------------------------
    template_path = Path(args.template)
    env = Environment(loader=FileSystemLoader(template_path.parent), autoescape=True,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_path.name)

    out_dir = Path(args.output)
    if out_dir.exists():
        shutil.rmtree(out_dir)  # Always rebuild from scratch so removed rows disappear.
    out_dir.mkdir(parents=True)

    published: list[tuple[dict[str, str], dict]] = []
    for row in rows:
        if row.get("_skip"):
            report.append({"url": "", "status": "skipped", "issues": row["_issues"],
                           "service": row.get("service", ""), "city": row.get("city", "")})
            continue
        page = build_page(row, base_url, rows)
        html = template.render(row=row, page=page, schema_json=build_schema(row, page))
        target = out_dir / row["locale"] / row["service_slug"] / row["city_slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        published.append((row, page))
        report.append({"url": page["url"], "status": "noindex" if page["noindex"] else "published",
                       "issues": row["_issues"], "service": row["service"], "city": row["city"]})

    # --- 3. Near-duplicate check on row-specific content -------------------------
    for (r1, p1), (r2, p2) in combinations(published, 2):
        sim = jaccard(word_set(" ".join(r1[c] for c in UNIQUE_FIELDS)),
                      word_set(" ".join(r2[c] for c in UNIQUE_FIELDS)))
        if sim > args.max_similarity:
            for entry in report:
                if entry["url"] in (p1["url"], p2["url"]):
                    other = p2["url"] if entry["url"] == p1["url"] else p1["url"]
                    entry["issues"] = "; ".join(filter(None, [entry["issues"],
                                                f"{sim:.0%} similar to {other}"]))

    # --- 4. Sitemap and report --------------------------------------------
    indexable = [p["url"] for _, p in published if not p["noindex"]]
    write_sitemap(indexable, out_dir / "sitemap.xml")
    with open(out_dir / "quality_report.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["service", "city", "url", "status", "issues"])
        writer.writeheader()
        writer.writerows(report)

    skipped = sum(1 for r in report if r["status"] == "skipped")
    print(f"Rows: {len(rows)} | Published: {len(indexable)} | "
          f"Noindex: {len(published) - len(indexable)} | Skipped: {skipped}")
    print(f"Output written to {out_dir}/ (see quality_report.csv and sitemap.xml)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
