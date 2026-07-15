"""Click the first available Buy button and screenshot the seat plan page."""
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

CDP = "http://localhost:9222"
ARTICLE_URL = (
    "https://whatson.bfi.org.uk/imax/Online/default.asp"
    "?BOparam::WScontent::loadArticle::permalink=odyssey-the-film-imax-70mm-2026"
    "&BOparam::WScontent::loadArticle::context_id="
)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.new_context(viewport={"width": 1280, "height": 1600})
    page = ctx.new_page()

    page.goto(ARTICLE_URL, wait_until="domcontentloaded")
    page.wait_for_selector(".detailed-search-results .result-box-item", timeout=20000)

    # Navigate to page 11 (first page with availability)
    for target_page in range(2, 12):
        next_link = page.locator("#av-next-link a")
        if next_link.count() == 0:
            break
        href = next_link.first.get_attribute("href")
        page.goto(urljoin(page.url, href), wait_until="domcontentloaded")
        page.wait_for_selector(".detailed-search-results .result-box-item", timeout=20000)
    print(f"On page 11, URL: {page.url}")

    # Find first available Buy button
    buy_btn = page.locator(".item-link:not(.soldout) .btn-primary").first
    print(f"Buy button found: {buy_btn.count() > 0}")
    label = buy_btn.get_attribute("aria-label")
    print(f"Clicking: {label}")

    # Click and wait for navigation (form POST to seatSelect.asp)
    with page.expect_navigation(wait_until="domcontentloaded", timeout=30000) as nav_info:
        buy_btn.click()
    resp = nav_info.value
    print(f"Navigated to: {page.url}")
    print(f"Response status: {resp.status if resp else 'unknown'}")

    # Wait for the seat plan to render
    page.wait_for_timeout(3000)

    # Screenshot only the seat map element
    seat_map = page.locator("div.screen-image").first
    if seat_map.count() == 0:
        print("[!] div.screen-image not found; saving full page instead")
        page.screenshot(path="seat-plan.png", full_page=True)
    else:
        seat_map.screenshot(path="seat-map.png")
        print("Screenshot of div.screen-image saved to seat-map.png")

    title = page.title()
    print(f"Page title: {title}")

    ctx.close()
    browser.close()
