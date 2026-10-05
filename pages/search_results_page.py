import logging  # logging of paging / errors
from urllib.parse import urlencode  # builds a safe query string for the results URL

from playwright.sync_api import TimeoutError as PlaywrightTimeout  # raised when a wait times out

from config.settings import SETTINGS  # base URL and max number of result pages
from pages.base_page import BasePage  # shared page behaviour (goto, screenshot)
from utils.price import is_price_range, parse_price  # price text -> number helpers

log = logging.getLogger(__name__)  # logger named after this module


class SearchResultsPage(BasePage):
    # XPath locators (kept in one place so they are easy to adjust if eBay changes markup).
    # eBay injects a hidden placeholder card linking to /itm/123456 - it is excluded here.
    CARDS = ("xpath=//li[(contains(@class,'s-item') or contains(@class,'s-card')) "  # a result card (old/new markup)
             "and .//a[contains(@href,'/itm/') and not(contains(@href,'/itm/123456'))]]")  # that links to a real item
    PRICE_REL = ("xpath=.//*[contains(@class,'s-item__price') "  # price element inside a card (old markup)
                 "or contains(@class,'s-card__price')]")  # price element inside a card (new markup)
    LINK_REL = ("xpath=.//a[contains(@href,'/itm/') "  # item link inside a card
                "and not(contains(@href,'/itm/123456'))]")  # excluding the placeholder link
    NEXT_PAGE = "xpath=//a[contains(@class,'pagination__next') and @href]"  # "Next" paging button

    ERROR_TEXT = "Something went wrong on our end"  # text of eBay's error page

    def __init__(self, page, query: str | None = None):
        super().__init__(page)  # BasePage setup (default timeout)
        self.query = query  # remember the search term to build URLs later

    # ---- loading ------------------------------------------------------
    def results_url(self, max_price: float | None = None) -> str:
        """Direct, deterministic URL of the results page (optionally with eBay's max-price filter)."""
        params = {"_nkw": self.query, "_sacat": "0"}  # _nkw = keywords, _sacat=0 = all categories
        if max_price is not None:  # a price filter was requested
            params["_udhi"] = f"{max_price:g}"  # _udhi = eBay's "max price" filter parameter
        return f"{SETTINGS.base_url}/sch/i.html?{urlencode(params)}"  # full search URL

    def _is_error_page(self) -> bool:
        return self.page.get_by_text(self.ERROR_TEXT).count() > 0  # True if eBay's error text is shown

    def wait_until_loaded(self) -> bool:
        """True when we are on a results page (cards visible, or a genuine empty result).
        False when eBay showed its error page or bounced us away from /sch/."""
        if "/sch/" not in self.page.url or self._is_error_page():  # not a results page / error page
            return False
        try:
            self.page.locator(self.CARDS).first.wait_for(state="visible", timeout=15000)  # wait for a result card
            return True  # results are visible
        except PlaywrightTimeout:  # no card appeared in time
            if "/sch/" not in self.page.url or self._is_error_page():  # redirected or error meanwhile
                return False
            log.warning("No result cards for %s | title=%r", self.page.url, self.page.title())  # log empty page
            self.screenshot("no_result_cards")  # evidence of the empty page
            return True  # on a results page but empty: treated as "0 results"

    def load(self, url: str, retries: int = 3) -> None:
        """Open a results URL, retrying when eBay shows an error page or redirects to the homepage."""
        for attempt in range(1, retries + 1):  # attempts 1..retries
            self.goto(url)  # navigate
            if self.wait_until_loaded():  # results page reached
                return
            log.warning("Results page not available (attempt %d/%d) url=%s title=%r",
                        attempt, retries, self.page.url, self.page.title())  # log failed attempt
            self.page.wait_for_timeout(3000 * attempt)  # growing back-off: 3s, 6s, 9s
        self.screenshot("results_unavailable")  # all attempts failed - keep evidence
        raise RuntimeError("eBay did not return a results page; try again in a few minutes")  # fail clearly

    # ---- price filter -------------------------------------------------
    def apply_max_price(self, max_price: float) -> None:
        """Use eBay's own price filter (the _udhi URL param behind the Price filter)."""
        self.load(self.results_url(max_price))  # reload the results with the max-price filter applied

    # ---- extraction ---------------------------------------------------
    def _collect_current_page(self, max_price: float, seen: list[str], limit: int) -> None:
        """Append to `seen` the URLs of cards on the current page priced <= max_price."""
        cards = self.page.locator(self.CARDS)  # all result cards on this page (XPath)
        for i in range(cards.count()):  # iterate cards in display order
            if len(seen) >= limit:  # already have enough items
                return
            card = cards.nth(i)  # the i-th card
            try:
                price_text = card.locator(self.PRICE_REL).first.inner_text(timeout=2000)  # e.g. "$12.99"
                href = card.locator(self.LINK_REL).first.get_attribute("href", timeout=2000)  # item link
            except PlaywrightTimeout:
                continue  # sponsored / placeholder card without price or link
            if not href or is_price_range(price_text):  # no link, or "$10 to $25" (ambiguous) -> skip
                continue
            price = parse_price(price_text)  # text -> float
            if price is None or price > max_price:  # unparsable or above the limit -> skip
                continue
            url = href.split("?")[0]  # drop tracking query params -> clean item URL
            if url not in seen:  # avoid duplicates (same item can appear twice)
                seen.append(url)  # keep it

    def _go_next_page(self) -> bool:
        """Go to the next results page; False if there is no "Next" button."""
        nxt = self.page.locator(self.NEXT_PAGE)  # the "Next" paging link
        if nxt.count() == 0:  # no paging / last page
            return False
        self.load(nxt.first.get_attribute("href"))  # open the next page (with retries)
        return True

    def collect_items_under_price(self, max_price: float, limit: int = 5) -> list[str]:
        """Collect up to `limit` item URLs priced <= max_price, paging when needed."""
        urls: list[str] = []  # collected URLs
        for page_no in range(1, SETTINGS.max_result_pages + 1):  # safety cap on pages (EBAY_MAX_PAGES)
            self._collect_current_page(max_price, urls, limit)  # collect from the current page
            log.info("Page %d: %d/%d items collected", page_no, len(urls), limit)  # progress log
            if len(urls) >= limit or not self._go_next_page():  # enough items, or no more pages
                break
        return urls[:limit]  # may be fewer than `limit`, or empty - both are valid
