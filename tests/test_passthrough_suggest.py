"""Unit-test fixture catalog is not used on runtime paths."""

from tests.fixtures.mock_vendor_catalog import MOCK_VENDOR_CATALOG


def test_mock_catalog_is_fixture_only():
    assert len(MOCK_VENDOR_CATALOG) >= 1
    assert MOCK_VENDOR_CATALOG[0]["restaurant_name"] == "A2B"
