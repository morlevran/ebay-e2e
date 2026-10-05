import logging  # logs a successful login

from config.settings import SETTINGS  # sign-in URL
from pages.base_page import BasePage  # shared page behaviour (goto, screenshot)

log = logging.getLogger(__name__)  # logger named after this module


class LoginPage(BasePage):
    USER_INPUT = "#userid"  # username / email field
    CONTINUE_BTN = "#signin-continue-btn"  # "Continue" after the username step
    PASS_INPUT = "#pass"  # password field
    SIGNIN_BTN = "#sgnBt"  # final "Sign in" button

    def login(self, username: str, password: str) -> None:
        self.goto(SETTINGS.signin_url)  # open the sign-in page
        self.page.fill(self.USER_INPUT, username)  # type the username
        self.page.click(self.CONTINUE_BTN)  # go to the password step
        self.page.fill(self.PASS_INPUT, password)  # type the password
        self.page.click(self.SIGNIN_BTN)  # submit
        self.page.wait_for_load_state("domcontentloaded")  # wait for the next page to load
        log.info("Logged in as %s", username)  # log the user (never the password)
