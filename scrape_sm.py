"""Scrape Science Museum IMAX screening availability for The Odyssey.

The Science Museum uses a tnew-based ticketing system with a Queue-it
interstitial.  The calendar page renders events as list items inside day
cells:

    <li class="tn-events-calendar__day-event-list-item"
        data-tn-performance-id="468567"
        data-tn-product-type-id="3">
      <a href="https://my.sciencemuseum.org.uk/423861/468567"
         class="tn-events-calendar__event btn btn-primary">
        <span class="tn-events-calendar__event-name">The Odyssey (15)</span>
        <span class="tn-events-calendar__event-time">10:30</span>
        <span class="tn-events-calendar__event-status">Sold out</span>
      </a>
    </li>

Day cells carry an SR-only label like
``#tn-events-day-cell-2026-07-17`` giving the full date.

The calendar shows one month at a time; the "next" button
``.tn-btn-datepicker__btn-period-prev-next--btn-next`` advances.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

CDP_ENDPOINT = "http://localhost:9222"
CALENDAR_URL = (
    "https://my.sciencemuseum.org.uk/events"
    "?view=calendar&kid=794&startdate=01-07-2026"
)
EVENT_ITEM_SELECTOR = ".tn-events-calendar__day-event-list-item"
NEXT_BTN_SELECTOR = ".tn-btn-datepicker__btn-period-prev-next--btn-next"
MONTH_VIEW_SELECTOR = "#tn-events-calendar-view-month"


@dataclass
class Screening:
    date: str  # ISO date "2026-07-17"
    time: str  # "10:30"
    name: str
    sold_out: bool
    performance_id: str
    production_season_id: str
    href: str

    @property
    def when(self) -> datetime | None:
        try:
            return datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    @property
    def key(self) -> str:
        dt = self.when
        return dt.strftime("%Y-%m-%d_%H-%M") if dt else f"{self.date}_{self.time}"


def _wait_for_calendar(page: Page, timeout_ms: int = 30_000) -> bool:
    """Wait for the month calendar view to render events."""
    try:
        page.wait_for_selector(MONTH_VIEW_SELECTOR, timeout=timeout_ms)
        page.wait_for_selector(EVENT_ITEM_SELECTOR, timeout=timeout_ms)
        return True
    except PWTimeout:
        return False


def parse_calendar(page: Page) -> list[Screening]:
    """Extract all screenings visible on the current calendar month view."""
    results = page.evaluate(
        """() => {
            const dayCells = document.querySelectorAll('[id^="tn-events-day-cell-"]');
            const screenings = [];
            for (const cell of dayCells) {
                const id = cell.id;  // tn-events-day-cell-2026-07-17
                const dateMatch = id.match(/(\\d{4}-\\d{2}-\\d{2})$/);
                if (!dateMatch) continue;
                const date = dateMatch[1];

                const dayCell = cell.closest('.tn-events-calendar__day-cell');
                if (!dayCell) continue;

                const items = dayCell.querySelectorAll('.tn-events-calendar__day-event-list-item');
                for (const item of items) {
                    const link = item.querySelector('a.tn-events-calendar__event');
                    if (!link) continue;

                    const name = item.querySelector('.tn-events-calendar__event-name')?.textContent?.trim() || '';
                    const timeEl = item.querySelector('.tn-events-calendar__event-time');
                    let time = timeEl ? timeEl.textContent.trim() : '';
                    time = time.replace(/,/, '').trim();

                    const statusEl = item.querySelector('.tn-events-calendar__event-status');
                    const status = statusEl ? statusEl.textContent.trim() : '';
                    const soldOut = status.toLowerCase().includes('sold');

                    const perfId = item.getAttribute('data-tn-performance-id') || '';
                    const href = link.getAttribute('href') || '';

                    // Extract production season id from href: /423861/468567
                    const hrefMatch = href.match(/\\/(\\d+)\\/(\\d+)/);
                    const prodSeasonId = hrefMatch ? hrefMatch[1] : '';

                    screenings.push({
                        date, time, name, soldOut,
                        performanceId: perfId,
                        productionSeasonId: prodSeasonId,
                        href,
                    });
                }
            }
            return screenings;
        }"""
    )

    screenings: list[Screening] = []
    for r in results:
        screenings.append(
            Screening(
                date=r["date"],
                time=r["time"],
                name=r["name"],
                sold_out=r["soldOut"],
                performance_id=r["performanceId"],
                production_season_id=r["productionSeasonId"],
                href=r["href"],
            )
        )
    return screenings


def scrape(
    max_months: int = 12,
    cdp: str | None = None,
    headed: bool = False,
) -> list[Screening]:
    all_items: list[Screening] = []
    with sync_playwright() as p:
        if cdp:
            browser = p.chromium.connect_over_cdp(cdp)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            browser = p.chromium.launch(headless=not headed)
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-GB",
                timezone_id="Europe/London",
            )
        page = ctx.new_page()

        print(f"[*] Navigating to {CALENDAR_URL}")
        page.goto(CALENDAR_URL, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(3000)

        if not _wait_for_calendar(page):
            print("[!] Calendar did not render. Saving debug HTML.", file=sys.stderr)
            Path("debug-sm-calendar.html").write_text(page.content())
            page.close()
            return all_items

        for month_idx in range(max_months):
            if not _wait_for_calendar(page):
                break

            items = parse_calendar(page)
            avail = sum(1 for it in items if not it.sold_out)
            month_label = items[0].date[:7] if items else f"month {month_idx + 1}"
            print(f"[month {month_idx + 1:>2}] {month_label}: {len(items)} screenings, {avail} available")

            # Add only new screenings not already seen
            seen_ids = {it.performance_id for it in all_items}
            new_items = [it for it in items if it.performance_id not in seen_ids]
            all_items.extend(new_items)
            print(f"  ({len(new_items)} new, {len(items) - len(new_items)} duplicates skipped)")

            # Click "next" to advance to the next month
            next_btn = page.locator(NEXT_BTN_SELECTOR).last
            if not next_btn.count() or next_btn.is_disabled():
                print("[*] No more months to scan.")
                break

            next_btn.click()
            page.wait_for_timeout(3000)
            if not _wait_for_calendar(page):
                print(f"[!] Failed to load next month. Stopping.", file=sys.stderr)
                break

        page.close()

    # Deduplicate by performance_id
    seen: set[str] = set()
    unique: list[Screening] = []
    for it in all_items:
        if it.performance_id not in seen:
            seen.add(it.performance_id)
            unique.append(it)

    return unique


def report(items: list[Screening]) -> None:
    total = len(items)
    sold = sum(1 for it in items if it.sold_out)
    avail = total - sold
    print("\n" + "=" * 60)
    print(f"The Odyssey @ Science Museum IMAX  -  {total} screenings found")
    print(f"Sold out: {sold}   Available: {avail}")
    print("=" * 60)

    available = [it for it in items if not it.sold_out]
    if available:
        print("\nAVAILABLE SCREENINGS:\n")
        for it in available:
            dt = it.when
            day = dt.strftime("%a %d %b %Y %H:%M") if dt else f"{it.date} {it.time}"
            print(f"  {day}  (perf {it.performance_id})")
            print(f"      {it.href}")
    else:
        print("\nNo available screenings found.")

    upcoming = [it for it in items if it.when and it.when >= datetime.now()]
    if upcoming:
        print("\nUpcoming screenings:")
        for it in upcoming[:15]:
            status = "SOLD OUT" if it.sold_out else "AVAILABLE"
            print(f"  {it.when.strftime('%a %d %b %Y %H:%M')}  {status}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Find Science Museum IMAX seats for The Odyssey"
    )
    ap.add_argument("--headed", action="store_true", help="launch a visible browser")
    ap.add_argument("--max-months", type=int, default=12, help="max months to scan")
    ap.add_argument(
        "--cdp",
        default=CDP_ENDPOINT,
        help="CDP endpoint (default: %(default)s; pass empty string for fresh browser)",
    )
    ap.add_argument("--out", default="screenings-sm.json", help="JSON output path")
    args = ap.parse_args()

    items = scrape(max_months=args.max_months, cdp=args.cdp or None, headed=args.headed)
    if not items:
        return 1

    Path(args.out).write_text(json.dumps([asdict(it) for it in items], indent=2))
    print(f"\nSaved {len(items)} screenings to {args.out}")
    report(items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
