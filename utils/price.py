"""Price parsing helpers (pure functions, unit-testable offline)."""
import re  # regular expressions

_NUMBER = re.compile(r"\d[\d.,]*")  # a number, possibly with thousands/decimal separators
_RANGE = re.compile(r"\bto\b|[–—]", re.IGNORECASE)  # "10 to 25" or "10 – 25" = a price range


def _normalize(token: str) -> float:
    """Convert '1,234.56' / '1.234,56' / '220,00' to a float."""
    token = token.rstrip(".,")  # drop a trailing separator ("220." -> "220")
    if "," in token and "." in token:  # both separators present
        if token.rfind(",") > token.rfind("."):  # 1.234,56 (European: comma is decimal)
            token = token.replace(".", "").replace(",", ".")
        else:  # 1,234.56 (US: dot is decimal)
            token = token.replace(",", "")
    elif "," in token:  # only commas
        head, _, tail = token.rpartition(",")  # split at the last comma
        token = f"{head.replace(',', '')}.{tail}" if len(tail) == 2 else token.replace(",", "")  # "12,50" vs "1,234"
    return float(token)  # final numeric value


def parse_price(text: str, last: bool = False) -> float | None:
    """Return the first (or last) number in `text` as float, or None if there is none."""
    matches = _NUMBER.findall(text or "")  # all numbers in the text
    if not matches:  # no number at all
        return None
    try:
        return _normalize(matches[-1] if last else matches[0])  # pick first or last and convert
    except ValueError:  # malformed number
        return None


def is_price_range(text: str) -> bool:
    """eBay shows '$10.00 to $25.00' for multi-variation listings - ambiguous, so we skip them."""
    return bool(_RANGE.search(text or ""))  # True if the text looks like a range
