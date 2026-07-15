"""Save seat plans for all non-morning available Odyssey screenings at BFI IMAX.

For each page of the availability widget:
  1. Record every screening's date/time/page/sold_out status.
  2. For each available screening that is NOT in the morning (hour >= 12):
     - Click its Buy button (navigates to mapSelect.asp).
     - Screenshot div.screen-image (the seat plan).
     - Navigate back to the listing page to continue.

Outputs:
  - seat-maps/YYYY-MM-DD_HH-MM.png  (one per non-morning available screening)
  - all-screenings.json             (every screening with date/time/page/status/screenshot)
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright

CDP_ENDPOINT = "http://localhost:9222"
ARTICLE_URL = (
    "https://whatson.bfi.org.uk/imax/Online/default.asp"
    "?BOparam::WScontent::loadArticle::permalink=odyssey-the-film-imax-70mm-2026"
    "&BOparam::WScontent::loadArticle::context_id="
)
RESULTS_SELECTOR = ".detailed-search-results .result-box-item"
NEXT_LINK_SELECTOR = "#av-next-link a"
SEAT_MAP_DIR = Path("seat-maps")


def parse_dt(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%A %d %B %Y %H:%M")
    except ValueError:
        return None


def is_morning(start_str: str) -> bool:
    dt = parse_dt(start_str)
    return dt is not None and dt.hour < 12


def _wait_past_cloudflare(page, target_selector: str, timeout_ms: int = 30000) -> bool:
    for _ in range(60):
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


def _find_buy_btn_index(page, start_str: str) -> int:
    """Find the result-box-item index for a screening with the given start time."""
    return page.evaluate(
        """(startStr) => {
            const items = document.querySelectorAll('.result-box-item');
            for (let i = 0; i < items.length; i++) {
                const d = items[i].querySelector('.start-date');
                const l = items[i].querySelector('.item-link');
                if (d && d.textContent.trim() === startStr
                    && l && !l.classList.contains('soldout')) {
                    return i;
                }
            }
            return -1;
        }""",
        start_str,
    )


def _repaginate(page, target_page: int) -> bool:
    """Re-navigate from the article page to the given page number."""
    print("  [!] Re-paginating from article page...", end=" ", flush=True)
    page.goto(ARTICLE_URL, wait_until="domcontentloaded")
    if not _wait_past_cloudflare(page, RESULTS_SELECTOR):
        return False
    for pg in range(2, target_page + 1):
        next_link = page.locator(NEXT_LINK_SELECTOR)
        if next_link.count() == 0:
            break
        href = next_link.first.get_attribute("href")
        if not href:
            break
        page.goto(urljoin(page.url, href), wait_until="domcontentloaded")
        _wait_past_cloudflare(page, RESULTS_SELECTOR)
    return True


def main() -> int:
    SEAT_MAP_DIR.mkdir(exist_ok=True)
    records: list[dict] = []
    screenshots = 0

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
        ctx = browser.new_context(viewport={"width": 1280, "height": 1600})
        page = ctx.new_page()

        page.goto(ARTICLE_URL, wait_until="domcontentloaded")
        if not _wait_past_cloudflare(page, RESULTS_SELECTOR):
            print("[!] Could not load article page", file=sys.stderr)
            return 1

        page_no = 1
        while True:
            boxes = page.locator(RESULTS_SELECTOR)
            count = boxes.count()

            # --- Collect info for all screenings on this page ---
            targets: list[tuple[int, str]] = []
            for i in range(count):
                box = boxes.nth(i)
                link_box = box.locator(".item-link").first
                classes = link_box.get_attribute("class") or ""
                sold_out = "soldout" in classes or link_box.locator(".unavailable-message").count() > 0
                start = box.locator(".start-date").first.inner_text().strip()
                venue = box.locator(".item-venue").first.inner_text().strip()

                records.append({
                    "page": page_no,
                    "start": start,
                    "venue": venue,
                    "sold_out": sold_out,
                    "screenshot": None,
                })

                if not sold_out:
                    targets.append((i, start))

            avail_on_page = sum(1 for i in range(count)
                                 if "soldout" not in (boxes.nth(i).locator(".item-link").first.get_attribute("class") or ""))
            print(f"[page {page_no:>2}] {count} screenings, {len(targets)} to screenshot")

            # --- Click Buy + screenshot for each non-morning available screening ---
            for _, start in targets:
                listing_url = page.url
                dt = parse_dt(start)
                fname = dt.strftime("%Y-%m-%d_%H-%M") + ".png" if dt else f"p{page_no}_{start}.png"

                print(f"  -> {start} ...", end=" ", flush=True)

                # Re-find the Buy button (page state may have changed after returning)
                idx = _find_buy_btn_index(page, start)
                if idx < 0:
                    print("SKIP (not found)")
                    continue

                buy_btn = page.locator(RESULTS_SELECTOR).nth(idx).locator("a.btn.btn-primary").first

                # Click and wait for navigation to seat map page
                try:
                    with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                        buy_btn.click()
                except PWTimeout:
                    print("FAIL (navigation timeout)")
                    continue

                # Wait for the seat map to render
                page.wait_for_timeout(3000)

                # Screenshot div.screen-image
                seat_map = page.locator("div.screen-image").first
                if seat_map.count() > 0:
                    seat_map.screenshot(path=str(SEAT_MAP_DIR / fname))
                else:
                    page.screenshot(path=str(SEAT_MAP_DIR / fname), full_page=True)
                    print("(full page) ", end="")

                screenshots += 1
                # Update the matching record with screenshot filename
                for r in reversed(records):
                    if r["start"] == start and r["page"] == page_no:
                        r["screenshot"] = fname
                        break
                print("OK")

                # Return to the listing page
                page.goto(listing_url, wait_until="domcontentloaded")
                if not _wait_past_cloudflare(page, RESULTS_SELECTOR):
                    # sToken likely expired — re-navigate from article page
                    if not _repaginate(page, page_no):
                        print("  [!] Could not reload listing page; stopping", file=sys.stderr)
                        break

                time.sleep(0.5)

            # --- Next page ---
            next_link = page.locator(NEXT_LINK_SELECTOR)
            if next_link.count() == 0:
                break
            href = next_link.first.get_attribute("href")
            if not href:
                break
            page.goto(urljoin(page.url, href), wait_until="domcontentloaded")
            if not _wait_past_cloudflare(page, RESULTS_SELECTOR):
                print(f"[!] Could not load page {page_no + 1}", file=sys.stderr)
                break
            page_no += 1

        ctx.close()
        browser.close()

    # --- Save all records ---
    with open("all-screenings.json", "w") as f:
        json.dump(records, f, indent=2)

    # --- Summary ---
    total = len(records)
    sold = sum(1 for r in records if r["sold_out"])
    avail = total - sold
    non_morning_avail = sum(1 for r in records if not r["sold_out"] and not is_morning(r["start"]))

    print(f"\n{'=' * 60}")
    print(f"Total screenings recorded: {total}")
    print(f"Sold out: {sold}   Available: {avail}")
    print(f"Non-morning available: {non_morning_avail}")
    print(f"Seat maps saved: {screenshots}")
    print(f"Records:  all-screenings.json")
    print(f"Maps dir: {SEAT_MAP_DIR}/")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
