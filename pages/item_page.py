import logging  # logs which variant was chosen
import random  # type of the RNG passed in by the flow
import re  # regex to skip "- Select -" placeholder options

from playwright.sync_api import TimeoutError as PlaywrightTimeout  # raised when a click/wait times out

from pages.base_page import BasePage  # shared page behaviour (goto, screenshot)

log = logging.getLogger(__name__)  # logger named after this module


class ItemNotPurchasable(RuntimeError):
    """Raised when an item cannot be added to the cart (the flow catches it and skips the item)."""


class ItemPage(BasePage):
    VARIANT_SELECTS = "xpath=//select[contains(@id,'msku') or contains(@class,'msku')]"  # native <select> variant menus
    # Best-effort support for eBay's custom (non-<select>) variant dropdowns.
    CUSTOM_LISTBOX_BUTTONS = ("xpath=//*[contains(@class,'msku')]"  # inside the variants area ...
                              "//button[@aria-haspopup='listbox' and not(@disabled)]")  # ... an enabled dropdown button
    LISTBOX_OPTIONS = "xpath=//*[@role='listbox']//*[@role='option' and not(@aria-disabled='true')]"  # enabled options
    ADD_TO_CART = ("xpath=//*[@id='atcBtn_btn_1' or ((self::a or self::button) "  # the known button id, or ...
                   "and normalize-space(.)='Add to cart')]")  # ... any link/button labelled "Add to cart"
    CONFIRMATION = ("text=/Added to cart|added to your cart|Go to cart|See in cart|"  # texts eBay shows
                    "View cart|Continue shopping/i")  # after a successful add
    VALIDATION_ERROR = "text=/Please select|Select a|Please choose/i"  # shown when a variant is missing

    def open(self, url: str) -> "ItemPage":
        self.goto(url)  # navigate to the item page
        return self  # allow chaining: ItemPage(tab).open(url).add_to_cart(...)

    def select_random_variants(self, rng: random.Random) -> None:
        """Pick a random available option in every variant dropdown (size / colour / ...)."""
        selects = self.page.locator(self.VARIANT_SELECTS)  # every native variant <select>
        for i in range(selects.count()):  # handle each dropdown
            select = selects.nth(i)  # the i-th dropdown
            options = select.locator("option")  # its <option> elements
            valid = []  # values that can be chosen
            for j in range(options.count()):  # check every option
                opt = options.nth(j)  # the j-th option
                value = opt.get_attribute("value")  # its value
                if value in (None, "", "-1") or opt.is_disabled():  # placeholder or out of stock
                    continue  # skip it
                valid.append(value)  # selectable option
            if valid:  # at least one option available
                choice = rng.choice(valid)  # pick one at random
                select.select_option(choice)  # select it in the page
                log.info("Variant %d -> %s", i, choice)  # log the choice
        self._select_custom_listboxes(rng)  # then handle the non-<select> dropdowns

    def _select_custom_listboxes(self, rng: random.Random) -> None:
        buttons = self.page.locator(self.CUSTOM_LISTBOX_BUTTONS)  # custom dropdown buttons
        for i in range(buttons.count()):  # handle each one
            try:
                buttons.nth(i).click(timeout=3000)  # open the dropdown
                options = self.page.locator(self.LISTBOX_OPTIONS)  # options of the open list
                valid = []  # selectable options
                for j in range(options.count()):  # check every option
                    opt = options.nth(j)  # the j-th option
                    if opt.is_visible() and not re.match(r"\s*-?\s*select", opt.inner_text(), re.I):  # real option
                        valid.append(opt)  # keep it
                if valid:  # something to choose
                    rng.choice(valid).click(timeout=3000)  # click a random option
                    log.info("Custom variant %d selected", i)  # log it
                else:
                    self.page.keyboard.press("Escape")  # nothing to choose - close the dropdown
            except PlaywrightTimeout:  # dropdown did not open / option not clickable
                continue  # best effort - move on

    def _confirmed(self) -> bool:
        return ("cart" in self.page.url.lower()  # redirected to the cart, or ...
                or self.page.locator(self.CONFIRMATION).count() > 0)  # ... a confirmation text is shown

    def add_to_cart(self, rng: random.Random) -> None:
        self.select_random_variants(rng)  # choose variants first (if the item has any)
        button = self.page.locator(self.ADD_TO_CART).first  # the "Add to cart" button
        if button.count() == 0:  # no button (sold out, auction only, ...)
            raise ItemNotPurchasable(f"No 'Add to cart' button on {self.page.url}")
        button.click()  # click "Add to cart"
        for _ in range(20):  # up to ~10 seconds
            if self._confirmed():  # success
                return
            self.page.wait_for_timeout(500)  # wait 0.5s and check again
        reason = ("a variant must be selected"  # eBay asks for a variant ...
                  if self.page.locator(self.VALIDATION_ERROR).count() else "no confirmation shown")  # ... or unknown
        raise ItemNotPurchasable(f"Add to cart not confirmed ({reason}) for {self.page.url}")  # caller skips the item
