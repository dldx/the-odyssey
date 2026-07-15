"""Scrape BFI IMAX screening availability for The Odyssey.

The article page embeds a "SearchWebWidget2" availability widget whose DOM
looks like:

    <div class="detailed-search-results results-box">
      <div class="odd result-box-item">
        <div class="item-name">
          <a href="default.asp?...article_id=...&...context_id=...">The Odyssey</a>
        </div>
        <div class="item-start-date"><span class="start-date">Friday 17 July 2026 00:01</span></div>
        <div class="item-venue">BFI IMAX</div>
        <div class="item-link result-box-item-details last-column soldout">
          <span class="unavailable-message">Sold out!</span>
        </div>
      </div>
      ...
    </div>

Sold-out rows carry a `soldout` class on `.item-link` and show an
`.unavailable-message`. Available rows instead contain a submit button / link
that posts the shared `sToken` to `seatSelect.asp` for that screening's
`context_id`.

Results are paginated (30 pages for a year-long run); the `#av-next-link`
anchor advances one page at a time, preserving the session `sToken`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

ARTICLE_URL = (
    "https://whatson.bfi.org.uk/imax/Online/default.asp"
    "?BOparam::WScontent::loadArticle::permalink=odyssey-the-film-imax-70mm-2026"
    "&BOparam::WScontent::loadArticle::context_id="
)
CDP_ENDPOINT = "http://localhost:9222"
ODYSSEY_ARTICLE_ID = "A0A2A7B6-689F-40DA-A1E4-22F7A5B3E99A"
RESULTS_SELECTOR = ".detailed-search-results .result-box-item"
NEXT_LINK_SELECTOR = "#av-next-link a"


@dataclass
class Screening:
    page: int
    start: str
    venue: str
    sold_out: bool
    article_id: str | None = None
    context_id: str | None = None
    article_href: str | None = None
    book_href: str | None = None
    book_html: str | None = None

    @property
    def when(self) -> datetime | None:
        try:
            return datetime.strptime(self.start, "%A %d %B %Y %H:%M")
        except ValueError:
            return None


def _qs_value(href: str, key: str) -> str | None:
    qs = parse_qs(urlparse(href).query, keep_blank_values=True)
    vals = qs.get(key)
    return vals[0] if vals else None


def _wait_past_cloudflare(page: Page, target_selector: str, timeout_ms: int = 30000) -> bool:
    """Wait through a Cloudflare interstitial ("Just a moment...") then for `target_selector`.

    Returns True when `target_selector` appears, False on timeout.
    """
    deadline_steps = 60
    for _ in range(deadline_steps):
        title = page.title()
        if "just a moment" in title.lower():
            try:
                page.wait_for_function(
                    "() => !/just a moment/i.test(document.title)",
                    timeout=timeout_ms,
                )
            except PWTimeout:
                return False
        try:
            page.wait_for_selector(target_selector, timeout=timeout_ms)
            return True
        except PWTimeout:
            if "just a moment" in page.title().lower():
                continue
            return False
    return False


def parse_page(page: Page, page_no: int) -> list[Screening]:
    items: list[Screening] = []
    boxes = page.locator(RESULTS_SELECTOR)
    count = boxes.count()
    for i in range(count):
        box = boxes.nth(i)

        name_link = box.locator(".item-name a")
        article_href = name_link.get_attribute("href") if name_link.count() else None
        article_id = _qs_value(article_href, "BOparam::WScontent::loadArticle::article_id") if article_href else None
        context_id = _qs_value(article_href, "BOparam::WScontent::loadArticle::context_id") if article_href else None

        start = box.locator(".start-date").first.inner_text().strip()
        venue = box.locator(".item-venue").first.inner_text().strip()

        link_box = box.locator(".item-link").first
        link_classes = link_box.get_attribute("class") or ""
        sold_out = "soldout" in link_classes or link_box.locator(".unavailable-message").count() > 0

        book_href = None
        book_html = None
        if not sold_out:
            inner_link = link_box.locator("a")
            if inner_link.count():
                book_href = inner_link.first.get_attribute("href")
            book_html = link_box.inner_html().strip()

        items.append(
            Screening(
                page=page_no,
                start=start,
                venue=venue,
                sold_out=sold_out,
                article_id=article_id,
                context_id=context_id,
                article_href=article_href,
                book_href=book_href,
                book_html=book_html,
            )
        )
    return items


def scrape(headed: bool = False, max_pages: int = 100, cdp: str | None = None) -> list[Screening]:
    all_items: list[Screening] = []
    with sync_playwright() as p:
        if cdp:
            browser = p.chromium.connect_over_cdp(cdp)
            owned_browser = False
            context = browser.new_context()
        else:
            browser = p.chromium.launch(headless=not headed)
            owned_browser = True
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-GB",
                timezone_id="Europe/London",
            )
        page = context.new_page()
        page.goto(ARTICLE_URL, wait_until="domcontentloaded")
        if not _wait_past_cloudflare(page, RESULTS_SELECTOR, timeout_ms=30000):
            html = page.content()
            Path("debug-article.html").write_text(html)
            print(f"[!] Widget did not appear. Saved HTML to debug-article.html ({len(html)} bytes)", file=sys.stderr)
            browser.close()
            return all_items

        page_no = 1
        while True:
            items = parse_page(page, page_no)
            all_items.extend(items)
            avail = sum(1 for it in items if not it.sold_out)
            print(f"[page {page_no:>2}] {len(items)} screenings, {avail} available")
            if page_no >= max_pages:
                break
            next_link = page.locator(NEXT_LINK_SELECTOR)
            if next_link.count() == 0:
                break
            href = next_link.first.get_attribute("href")
            if not href:
                break
            next_url = urljoin(page.url, href)
            page.goto(next_url, wait_until="domcontentloaded")
            if not _wait_past_cloudflare(page, RESULTS_SELECTOR, timeout_ms=30000):
                Path(f"debug-page{page_no + 1}.html").write_text(page.content())
                print(
                    f"[!] page {page_no + 1} blocked/unavailable after challenge; "
                    f"saved debug-page{page_no + 1}.html",
                    file=sys.stderr,
                )
                break
            page_no += 1

        context.close()
        if owned_browser:
            browser.close()
        else:
            browser.close()
    return all_items


def report(items: list[Screening]) -> None:
    total = len(items)
    sold = sum(1 for it in items if it.sold_out)
    avail = total - sold
    print("\n" + "=" * 60)
    print(f"The Odyssey @ BFI IMAX  -  {total} screenings found")
    print(f"Sold out: {sold}   Available: {avail}")
    print("=" * 60)

    available = [it for it in items if not it.sold_out]
    if available:
        print("\nAVAILABLE SEATS:\n")
        for it in available:
            dt = it.when
            day = dt.strftime("%a %d %b %Y %H:%M") if dt else it.start
            print(f"  {day}  ({it.venue})  page {it.page}")
            if it.book_href:
                print(f"      book: {it.book_href}")
            if it.book_html:
                print(f"      link html: {it.book_html[:120]}")
    else:
        print("\nNo available seats found across any page.")

    upcoming = [it for it in items if it.when and it.when >= datetime.now()]
    if upcoming:
        print("\nFirst few upcoming screenings (status):")
        for it in upcoming[:10]:
            status = "SOLD OUT" if it.sold_out else "AVAILABLE"
            print(f"  {it.when.strftime('%a %d %b %Y %H:%M')}  {status}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Find BFI IMAX seats for The Odyssey")
    ap.add_argument("--headed", action="store_true", help="launch a visible browser (ignored with --cdp)")
    ap.add_argument("--max-pages", type=int, default=100, help="cap on pages to scan")
    ap.add_argument(
        "--cdp",
        default=CDP_ENDPOINT,
        help="CDP endpoint of an existing Chrome to attach to (default: %(default)s; "
        "pass an empty string to launch a fresh browser instead)",
    )
    ap.add_argument("--out", default="screenings.json", help="JSON output path")
    args = ap.parse_args()

    items = scrape(headed=args.headed, max_pages=args.max_pages, cdp=args.cdp or None)
    if not items:
        return 1

    Path(args.out).write_text(json.dumps([asdict(it) for it in items], indent=2))
    print(f"\nSaved {len(items)} screenings to {args.out}")
    report(items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
