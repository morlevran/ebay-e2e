"""The four required functions, orchestrating the page objects."""
import logging  # standard logging - every step is written to the test log
import random  # random generator used to pick item variants

from playwright.sync_api import Page  # type of the browser tab we drive

from config.settings import SETTINGS  # central config (credentials, seed, timeouts)
from pages.cart_page import CartPage  # page object for the shopping cart
from pages.home_page import HomePage  # page object for the eBay homepage (search box)
from pages.item_page import ItemNotPurchasable, ItemPage  # item page + "cannot add" error
from pages.login_page import LoginPage  # page object for the sign-in form

log = logging.getLogger(__name__)  # logger named after this module


class ShoppingFlow:
    """High-level business flow. Tests call only these methods, never page objects."""

    def __init__(self, page: Page):
        self.page = page  # the "search tab" - stays open for the whole flow
        self.rng = random.Random(SETTINGS.random_seed)  # seeded RNG -> reproducible runs if EBAY_SEED is set
        self.added_urls: list[str] = []  # items that were really added to the cart
        self.failed_urls: list[str] = []  # items that could not be added (skipped)

    # 1. authentication ---------------------------------------------------
    def login(self) -> None:
        if SETTINGS.username and SETTINGS.password:  # credentials provided via env vars?
            LoginPage(self.page).login(SETTINGS.username, SETTINGS.password)  # real sign-in
        else:
            log.info("EBAY_USER/EBAY_PASS not set - continuing as guest (login stub)")  # guest mode

    # 2. search with price condition -------------------------------------
    def search_items_by_name_under_price(self, query: str, max_price: float, limit: int = 5) -> list[str]:
        """Return up to `limit` item URLs whose price is <= max_price (empty list is valid)."""
        results = HomePage(self.page).open().search(query)  # open homepage and search for `query`
        results.apply_max_price(max_price)  # apply eBay's max-price filter to narrow the results
        return results.collect_items_under_price(max_price, limit)  # collect via XPath, paging if needed

    # 3. add to cart -----------------------------------------------------
    def add_items_to_cart(self, urls: list[str]) -> None:
        """Adds every item it can. Items that cannot be added (e.g. unavailable, variant
        that cannot be chosen) are logged, screenshotted and skipped; see added_urls."""
        for url in urls:  # loop over every URL returned by the search
            item_id = url.rsplit("/", 1)[-1]  # eBay item id = last URL segment (used in file names)
            tab = self.page.context.new_page()  # item opens in its own tab
            try:
                item = ItemPage(tab).open(url)  # navigate the new tab to the item page
                try:
                    item.add_to_cart(self.rng)  # pick random variants (if any) and click "Add to cart"
                except ItemNotPurchasable as exc:  # item could not be added
                    log.warning("Skipping item: %s", exc)  # log the reason
                    item.screenshot(f"add_failed_{item_id}")  # evidence of the failure
                    self.failed_urls.append(url)  # remember it as failed
                    continue  # move on to the next item (finally still runs)
                item.screenshot(f"added_{item_id}")  # screenshot for every item that was added
                self.added_urls.append(url)  # remember it as added
                log.info("Added to cart: %s", url)  # log entry for every added item
            finally:
                tab.close()  # close the item tab ...
                self.page.bring_to_front()  # ... and return to the search tab

    # 4. assert cart total -----------------------------------------------
    def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int,
                                      include_shipping: bool = False) -> None:
        """Assert the cart total <= budget_per_item * items_count."""
        cart = CartPage(self.page).open()  # open the cart page
        items_total = cart.read_items_total()  # "Items (N)" line - items only, no shipping
        subtotal = cart.read_total()  # "Subtotal" line - includes shipping
        total = subtotal if include_shipping else items_total  # which value to compare
        threshold = budget_per_item * items_count  # maximum allowed total
        cart.screenshot("cart_page")  # screenshot of the cart as evidence
        log.info("Items total=%.2f | Subtotal (incl. shipping)=%.2f | threshold=%.2f | compared=%s",
                 items_total, subtotal, threshold, "subtotal" if include_shipping else "items")  # log both values
        assert total <= threshold, f"Cart total {total} exceeds threshold {threshold}"  # the actual check
