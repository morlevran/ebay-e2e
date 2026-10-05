"""Central configuration. Everything can be overridden with environment variables."""
import os  # reads environment variables
from dataclasses import dataclass, field  # immutable settings object
from pathlib import Path  # file-system paths

ROOT = Path(__file__).resolve().parent.parent  # project root folder


@dataclass(frozen=True)  # frozen = settings cannot be changed at runtime
class Settings:
    base_url: str = os.getenv("EBAY_BASE_URL", "https://www.ebay.com")  # site under test
    cart_url: str = os.getenv("EBAY_CART_URL", "https://cart.ebay.com/")  # cart page
    signin_url: str = os.getenv("EBAY_SIGNIN_URL", "https://signin.ebay.com/")  # sign-in page
    # Optional credentials. When absent the flow runs as a guest (login stub).
    username: str = os.getenv("EBAY_USER", "")  # eBay username
    password: str = os.getenv("EBAY_PASS", "")  # eBay password
    default_timeout_ms: int = int(os.getenv("EBAY_TIMEOUT_MS", "15000"))  # default Playwright timeout
    max_result_pages: int = int(os.getenv("EBAY_MAX_PAGES", "5"))  # safety cap on result pages to scan
    random_seed: int | None = (  # fixed seed -> same random variants every run
        int(os.environ["EBAY_SEED"]) if os.getenv("EBAY_SEED") else None  # None = truly random
    )
    screenshots_dir: Path = field(default=ROOT / "artifacts" / "screenshots")  # where screenshots go
    scenarios_file: Path = field(default=ROOT / "data" / "scenarios.json")  # test data file


SETTINGS = Settings()  # single shared instance imported everywhere
SETTINGS.screenshots_dir.mkdir(parents=True, exist_ok=True)  # make sure the screenshots folder exists
