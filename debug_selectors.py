from playwright.sync_api import sync_playwright

URL = "https://www.ebay.com/sch/i.html?_nkw=backpack&_udhi=50"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(8000)
    print("title:", page.title())
    for name, sel in {
        "li.s-item": "li.s-item",
        "li.s-card": "li.s-card",
        "li with /itm/ link": "xpath=//li[.//a[contains(@href,'/itm/')]]",
        "any /itm/ link": "xpath=//a[contains(@href,'/itm/')]",
    }.items():
        print(name, "->", page.locator(sel).count())
    open("debug.html", "w", encoding="utf-8").write(page.content())
    page.screenshot(path="debug.png")
    browser.close()