import pytest  # fixtures

from flows.shopping import ShoppingFlow  # the business flow handed to tests


@pytest.fixture(scope="session")  # overrides pytest-playwright's fixture once per run
def browser_context_args(browser_context_args):
    # Keep the defaults, force a desktop-sized window and English UI.
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}, "locale": "en-US"}


@pytest.fixture  # new flow (fresh tab and state) for every test
def shop(page) -> ShoppingFlow:
    return ShoppingFlow(page)  # `page` is provided by pytest-playwright
