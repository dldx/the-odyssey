"""Save seat plans for all available Odyssey screenings at Science Museum IMAX.

Unlike BFI IMAX (which requires screenshot + OpenCV detection), the Science
 Museum uses a tnew SYOS (Select Your Own Seat) system that renders seats as
 SVG elements with structured data directly in the DOM:

    <g role="button" data-tn-seat-id="8699133"
       class="tn-syos-seat-map__seat"
       aria-label="A1, £12.20 to £18.00"
       style="color: rgb(0, 72, 153);">
      <use x="576" y="864" width="72" height="72"
           xlink:href="#tn-syos-seat-map-icon-circle-r"/>
    </g>

Available seats have class ``tn-syos-seat-map__seat`` and a ``circle-r``
icon.  Booked seats have ``tn-syos-seat-map__seat--unavailable`` and a
``square`` icon.

For each available screening this script:
  1. Navigates to the event detail page.
  2. Waits for the SYOS seat map SVG to render.
  3. Extracts all seats (id, row, number, x, y, available, price).
  4. Screenshots the seat map for visual reference.
  5. Saves structured data to ``analyzed-seats-sm.json``.

Outputs:
  - seat-maps-sm/YYYY-MM-DD_HH-MM.png   (seat map screenshots)
  - all-screenings-sm.json              (every screening with status)
  - analyzed-seats-sm.json              (structured seat data per screening)
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright

CDP_ENDPOINT = "http://localhost:9222"
SCREENINGS_FILE = Path("screenings-sm.json")
SEAT_MAP_DIR = Path("seat-maps-sm")
SEAT_MAP_SELECTOR = ".tn-syos-seat-map"
SEAT_SELECTOR = "[data-tn-seat-id]"
EVENT_DETAIL_SELECTOR = ".tn-event-detail"


def _parse_dt(date_str: str, time_str: str) -> datetime | None:
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _wait_for_seat_map(page, timeout_ms: int = 30_000) -> bool:
    """Wait for the SYOS seat map to render with seat elements."""
    try:
        page.wait_for_selector(SEAT_MAP_SELECTOR, timeout=timeout_ms)
        page.wait_for_selector(SEAT_SELECTOR, timeout=timeout_ms)
        return True
    except PWTimeout:
        return False


def extract_seats(page) -> list[dict]:
    """Extract all seat data from the SVG DOM."""
    return page.evaluate(
        """() => {
            const seats = document.querySelectorAll('[data-tn-seat-id]');
            const results = [];
            for (const seat of seats) {
                const seatId = seat.getAttribute('data-tn-seat-id');
                const cls = seat.getAttribute('class') || '';
                const available = !cls.includes('--unavailable');
                const label = seat.getAttribute('aria-label') || '';

                // Parse label: "A1, £12.20 to £18.00" or "A10, Booked Seats"
                const labelMatch = label.match(/^([A-Z])(\\d+)/);
                const row = labelMatch ? labelMatch[1] : '';
                const number = labelMatch ? parseInt(labelMatch[2]) : 0;

                // Parse price from label
                const priceMatch = label.match(/£([\\d.]+)/g);
                const prices = priceMatch ? priceMatch.map(p => p.replace('£', '')) : [];

                // Get position from <use> child
                const useEl = seat.querySelector('use');
                const x = useEl ? parseInt(useEl.getAttribute('x')) || 0 : 0;
                const y = useEl ? parseInt(useEl.getAttribute('y')) || 0 : 0;

                // Get icon type
                const href = useEl ? useEl.getAttribute('xlink:href') || '' : '';
                const iconType = href.replace('#tn-syos-seat-map-icon-', '');

                // Get section/row from aria-describedby
                const describedBy = seat.getAttribute('aria-describedby') || '';
                const sectionMatch = describedBy.match(/section-list-heading-id-(\\d+)/);
                const sectionId = sectionMatch ? sectionMatch[1] : '';

                results.push({
                    seat_id: seatId,
                    row, number,
                    x, y,
                    available,
                    prices,
                    icon_type: iconType,
                    section_id: sectionId,
                    label,
                });
            }
            return results;
        }"""
    )


def save_seat_plan_for_screening(page, screening: dict) -> dict | None:
    """Navigate to a screening's event page and extract seat data."""
    href = screening["href"]
    date_str = screening["date"]
    time_str = screening["time"]

    dt = _parse_dt(date_str, time_str)
    fname = dt.strftime("%Y-%m-%d_%H-%M") + ".png" if dt else f"{date_str}_{time_str}.png"

    print(f"  -> {date_str} {time_str} ...", end=" ", flush=True)

    try:
        page.goto(href, wait_until="networkidle", timeout=60_000)
    except PWTimeout:
        print("FAIL (navigation timeout)")
        return None

    page.wait_for_timeout(3000)

    # Check if sold out (no seat map)
    unavailable_text = page.locator(".tn-event-detail__unavailable-text")
    if unavailable_text.count() and "sold out" in unavailable_text.first.inner_text().lower():
        print("SOLD OUT")
        return None

    # Wait for seat map
    if not _wait_for_seat_map(page):
        # Try clicking the IMAX section button if present
        section_btn = page.locator(".tn-syos-screen-button")
        if section_btn.count():
            print("(clicking section) ", end="")
            try:
                section_btn.first.click()
                page.wait_for_timeout(3000)
            except PWTimeout:
                pass

        if not _wait_for_seat_map(page):
            print("FAIL (no seat map)")
            # Save debug HTML
            Path(f"debug-sm-{fname.replace('.png', '.html')}").write_text(page.content())
            return None

    # Extract structured seat data
    seats = extract_seats(page)
    if not seats:
        print("FAIL (no seats extracted)")
        return None

    available_count = sum(1 for s in seats if s["available"])
    total_count = len(seats)
    print(f"OK ({available_count}/{total_count} available)")

    # Screenshot the seat map
    seat_map_el = page.locator(SEAT_MAP_SELECTOR).first
    if seat_map_el.count():
        seat_map_el.screenshot(path=str(SEAT_MAP_DIR / fname))
    else:
        page.screenshot(path=str(SEAT_MAP_DIR / fname), full_page=True)

    # Group seats by row
    by_row: dict[str, list] = {}
    for s in seats:
        row = s["row"]
        if row not in by_row:
            by_row[row] = []
        by_row[row].append(s)

    return {
        "datetime": f"{date_str} {time_str}",
        "date": date_str,
        "time": time_str,
        "performance_id": screening["performance_id"],
        "production_season_id": screening["production_season_id"],
        "href": href,
        "total_seats": total_count,
        "available_seats": available_count,
        "sold_out": screening["sold_out"],
        "screenshot": fname,
        "by_row": {
            row: {
                "total": len(seats_in_row),
                "available": sum(1 for s in seats_in_row if s["available"]),
                "seats": [
                    {
                        "seat_id": s["seat_id"],
                        "number": s["number"],
                        "x": s["x"],
                        "y": s["y"],
                        "available": s["available"],
                        "price": s["prices"],
                        "icon": s["icon_type"],
                    }
                    for s in sorted(seats_in_row, key=lambda s: s["number"])
                ],
            }
            for row, seats_in_row in sorted(by_row.items())
        },
        "all_seats": seats,
    }


def main() -> int:
    if not SCREENINGS_FILE.exists():
        print(f"[!] {SCREENINGS_FILE} not found. Run scrape_sm.py first.", file=sys.stderr)
        return 1

    with open(SCREENINGS_FILE) as f:
        screenings = json.load(f)

    SEAT_MAP_DIR.mkdir(exist_ok=True)

    # Filter to available screenings only
    available = [s for s in screenings if not s["sold_out"]]
    print(f"[*] {len(screenings)} screenings total, {len(available)} available")

    if not available:
        print("[!] No available screenings to process.")
        return 0

    results: dict[str, dict] = {}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context(
            viewport={"width": 1280, "height": 1600}
        )
        page = ctx.new_page()

        for i, screening in enumerate(available):
            print(f"[{i + 1:>2}/{len(available)}]", end="")
            result = save_seat_plan_for_screening(page, screening)
            if result:
                key = result["datetime"].replace(" ", "_").replace(":", "-")
                results[key] = result
            time.sleep(1)

        page.close()

    # Save structured data
    output = {
        "venue": "Science Museum IMAX",
        "total_screenings": len(screenings),
        "available_screenings": len(available),
        "screenings_processed": len(results),
        "screenings": results,
    }

    with open("analyzed-seats-sm.json", "w") as f:
        json.dump(output, f, indent=2)

    # Save full screening list with processing status
    for s in screenings:
        s["processed"] = any(
            r["performance_id"] == s["performance_id"] for r in results.values()
        )
    with open("all-screenings-sm.json", "w") as f:
        json.dump(screenings, f, indent=2)

    # Summary
    total_avail = sum(r["available_seats"] for r in results.values())
    print(f"\n{'=' * 60}")
    print(f"Science Museum IMAX - Seat Plan Extraction Complete")
    print(f"Screenings processed: {len(results)}")
    print(f"Total available seats: {total_avail}")
    print(f"Screenshots:  {SEAT_MAP_DIR}/")
    print(f"Seat data:    analyzed-seats-sm.json")
    print(f"Screenings:   all-screenings-sm.json")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
