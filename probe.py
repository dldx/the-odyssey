"""Probe: click Buy and capture the form submission (URL + POST data)."""
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

    # Inspect the jQuery click handler source
    handler_src = page.evaluate("""() => {
        const buyBtn = document.querySelector(".item-link:not(.soldout) .btn-primary");
        if (!buyBtn || !window.jQuery) return null;
        const events = jQuery._data(buyBtn, 'events');
        if (!events || !events.click) return null;
        return events.click.map(h => h.handler.toString());
    }""")
    print("=== JQUERY CLICK HANDLER SOURCE ===")
    if handler_src:
        for src in handler_src:
            print(src)
    else:
        print("(no jQuery click handler found)")

    # Also check inline onclick
    onclick_src = page.evaluate("""() => {
        const buyBtn = document.querySelector(".item-link:not(.soldout) .btn-primary");
        return buyBtn ? buyBtn.getAttribute('onclick') : null;
    }""")
    print("\n=== INLINE ONCLICK ===")
    print(onclick_src or "(none)")

    ctx.close()
    browser.close()
