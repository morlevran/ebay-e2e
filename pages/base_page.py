import logging  # logs where screenshots are saved
import re  # sanitises screenshot names
import time  # timestamp prefix for screenshot files
from pathlib import Path  # return type of screenshot()

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout  # browser tab type + timeout error

from config.settings import SETTINGS  # timeouts and screenshots folder

log = logging.getLogger(__name__)  # logger named after this module


class BasePage:
    """Shared behaviour for every page object."""

    def __init__(self, page: Page):
        self.page = page  # the Playwright tab this page object drives
        self.page.set_default_timeout(SETTINGS.default_timeout_ms)  # default wait for every action

    def goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded")  # navigate and wait for the DOM
        self.dismiss_popups()  # close cookie banners that may cover the page

    def dismiss_popups(self) -> None:
        """Best-effort close of cookie / consent banners."""
        for selector in ("#gdpr-banner-accept", "button#onetrust-accept-btn-handler"):  # known "accept" buttons
            try:
                self.page.locator(selector).first.click(timeout=1500)  # click it if it shows up quickly
                return  # one banner closed - done
            except PlaywrightTimeout:  # banner not present
                continue  # try the next one
            except Exception:  # noqa: BLE001 - never fail a test on a banner
                continue

    def screenshot(self, name: str) -> Path:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name)[:80]  # file-system safe name, max 80 chars
        path = SETTINGS.screenshots_dir / f"{int(time.time() * 1000)}_{slug}.png"  # unique, time-ordered file name
        self.page.screenshot(path=str(path))  # take the screenshot
        log.info("Screenshot saved: %s", path)  # log its location
        try:  # attach to Allure when available
            import allure  # optional dependency

            allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)  # show in report
        except Exception:  # noqa: BLE001 - reporting must never break the test
            pass
        return path  # caller may use the path
