import json  # parses the scenarios file
from pathlib import Path  # type of the optional path argument

from config.settings import SETTINGS  # default scenarios file location


def load_scenarios(path: Path | None = None) -> list[dict]:
    """Load the data-driven test scenarios (list of {name, query, max_price, limit})."""
    with open(path or SETTINGS.scenarios_file, encoding="utf-8") as fh:  # given path or the default file
        return json.load(fh)  # JSON array -> list of dicts
