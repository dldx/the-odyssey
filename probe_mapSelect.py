"""Probe: fetch and save the HTML of mapSelect.asp to see its internal structure."""
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
    ctx = browser.new_context()
    page = ctx.new_page()

    page.goto(ARTICLE_URL, wait_until="domcontentloaded")
    page.wait_for_selector(".detailed-search-results .result-box-item", timeout=20000)

    # Navigate to page 11
    for target_page in range(2, 12):
        next_link = page.locator("#av-next-link a")
        if next_link.count() == 0:
            break
        href = next_link.first.get_attribute("href")
        page.goto(urljoin(page.url, href), wait_until="domcontentloaded")
        page.wait_for_selector(".detailed-search-results .result-box-item", timeout=20000)

    # Click first available Buy button
    buy_btn = page.locator(".item-link:not(.soldout) .btn-primary").first
    buy_btn.click()
    page.wait_for_timeout(3000)

    # Save full page HTML
    html = page.content()
    with open("debug-mapSelect.html", "w") as f:
        f.write(html)
    print(f"Saved {len(html)} characters of mapSelect.asp to debug-mapSelect.html")

    ctx.close()
    browser.close()
