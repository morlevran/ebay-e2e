import logging  # logs fallbacks when the UI search fails

from playwright.sync_api import TimeoutError as PlaywrightTimeout  # raised when a wait times out

from config.settings import SETTINGS  # base URL
from pages.base_page import BasePage  # shared page behaviour (goto, screenshot)
from pages.search_results_page import SearchResultsPage  # page returned after searching

log = logging.getLogger(__name__)  # logger named after this module


class HomePage(BasePage):
    SEARCH_INPUT = "input[name='_nkw']"  # the main search box

    def open(self) -> "HomePage":
        self.goto(SETTINGS.base_url)  # navigate to www.ebay.com
        return self  # allow chaining: HomePage(page).open().search(...)

    def search(self, query: str) -> SearchResultsPage:
        """Search through the UI; if eBay shows an error page / bounces us back to the
        homepage, fall back to the direct results URL (with retries)."""
        results = SearchResultsPage(self.page, query)  # results page object for this query
        box = self.page.locator(self.SEARCH_INPUT).first  # the search input
        try:
            box.wait_for(state="visible", timeout=10000)  # wait until the box is shown
            box.fill(query)  # type the search term
            with self.page.expect_navigation(url="**/sch/**", wait_until="domcontentloaded",
                                             timeout=15000):  # expect navigation to a /sch/ results URL
                box.press("Enter")  # submit the search
            if results.wait_until_loaded():  # results page loaded correctly
                return results
            log.warning("UI search did not land on results (url=%s)", self.page.url)  # error page / redirect
        except PlaywrightTimeout:  # box not found or navigation did not happen
            log.warning("UI search failed on %s | title=%r", self.page.url, self.page.title())  # log it
            self.screenshot("ui_search_failed")  # evidence
        results.load(results.results_url())  # fallback: open the results URL directly (with retries)
        return results
