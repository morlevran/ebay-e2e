import re  # regexes used to read totals from the page text

from config.settings import SETTINGS  # cart URL
from pages.base_page import BasePage  # shared page behaviour (goto, screenshot)
from utils.price import parse_price  # price text -> number


class CartPage(BasePage):
    SUBTOTAL_CANDIDATES = (  # known locations of the subtotal, tried in order
        "xpath=//*[@data-test-id='SUBTOTAL']",  # subtotal row
        "xpath=//*[@data-test-id='ITEM_TOTAL']",  # alternative markup
    )
    SUBTOTAL_TEXT_FALLBACK = re.compile(r"Subtotal[^\n]*\n?[^\n]*?([\d.,]+\d)", re.IGNORECASE)  # "Subtotal ... 123.45"
    ITEMS_TOTAL_RE = re.compile(r"Items?\s*\(\d+\)\D{0,15}(\d[\d.,]*\d)", re.I)  # "Items (3)  $123.45"

    def open(self) -> "CartPage":
        self.goto(SETTINGS.cart_url)  # navigate to the cart
        return self  # allow chaining

    def read_total(self) -> float:
        """Subtotal as displayed (includes shipping)."""
        for selector in self.SUBTOTAL_CANDIDATES:  # try each known locator
            loc = self.page.locator(selector).first  # first matching element
            if loc.count():  # it exists on the page
                value = parse_price(loc.inner_text(), last=True)  # last number in the row = the amount
                if value is not None:  # parsed successfully
                    return value
        match = self.SUBTOTAL_TEXT_FALLBACK.search(self.page.inner_text("body"))  # fallback: search page text
        if match:  # found "Subtotal ..." text
            value = parse_price(match.group(1))  # parse the captured amount
            if value is not None:
                return value
        raise AssertionError("Could not locate the cart subtotal on the page")  # fail the test clearly

    def read_items_total(self) -> float:
        """The 'Items (N)' line of the order summary (items only, no shipping)."""
        match = self.ITEMS_TOTAL_RE.search(self.page.inner_text("body"))  # search the page text
        if match:  # line found
            value = parse_price(match.group(1))  # parse the amount
            if value is not None:
                return value
        raise AssertionError("Could not locate the 'Items (N)' total in the cart")  # fail the test clearly
