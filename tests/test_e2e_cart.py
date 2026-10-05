import pytest  # test framework

from utils.data_loader import load_scenarios  # reads data/scenarios.json

pytestmark = pytest.mark.e2e  # mark every test here as end-to-end (-m e2e)


@pytest.mark.parametrize("scenario", load_scenarios(), ids=lambda s: s["name"])  # one test per JSON scenario
def test_cart_total_within_budget(shop, scenario):
    shop.login()  # 1. log in (or continue as guest)
    urls = shop.search_items_by_name_under_price(  # 2. search and collect item URLs under the price
        scenario["query"], scenario["max_price"], scenario.get("limit", 5)  # limit defaults to 5
    )
    if not urls:  # nothing matched - valid result, nothing to test further
        pytest.skip(f"No items found under {scenario['max_price']} for '{scenario['query']}'")

    shop.add_items_to_cart(urls)  # 3. add every found item to the cart
    if not shop.added_urls:  # nothing could be added - the scenario cannot be verified
        pytest.fail("None of the found items could be added to the cart")

    # 4. The budget is checked against the number of items that really are in the cart.
    shop.assert_cart_total_not_exceeds(scenario["max_price"], len(shop.added_urls))
