import pytest  # test framework

from utils.price import is_price_range, parse_price  # functions under test

pytestmark = pytest.mark.unit  # offline unit tests (-m unit)


@pytest.mark.parametrize("text,expected", [  # input text -> expected number
    ("$1,234.56", 1234.56),  # US thousands separator
    ("ILS 220.00", 220.0),  # currency code prefix
    ("US $5.00", 5.0),  # eBay "US $" format
    ("1.234,56 €", 1234.56),  # European format
    ("$99", 99.0),  # no decimals
    ("no price", None),  # no number at all
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected  # parsed value matches


def test_parse_price_last():
    assert parse_price("Subtotal (3 items)\nUS $220.00", last=True) == 220.0  # takes the amount, not the "3"


def test_price_range_detection():
    assert is_price_range("$10.00 to $25.00")  # a range is detected
    assert not is_price_range("$10.00")  # a single price is not a range
