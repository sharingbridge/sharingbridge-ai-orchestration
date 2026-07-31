"""Unit-test-only: fixture catalog exists and is not used by runtime suggest path."""

from app.services.suggest_vendors import build_passthrough_suggest_vendors_response
from tests.fixtures.mock_vendor_catalog import MOCK_VENDOR_CATALOG


def test_mock_catalog_is_fixture_only():
    assert len(MOCK_VENDOR_CATALOG) >= 1
    assert MOCK_VENDOR_CATALOG[0]["restaurant_name"] == "A2B"


def test_passthrough_echoes_query_not_catalog():
    result = build_passthrough_suggest_vendors_response(
        {"query_text": "my local tiffin place", "manual_area": "Chennai"}
    )
    assert result["source"] == "passthrough"
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["restaurant_name"] == "my local tiffin place"
    names = {row["restaurant_name"] for row in MOCK_VENDOR_CATALOG}
    assert result["suggestions"][0]["restaurant_name"] not in names


def test_passthrough_empty_query():
    result = build_passthrough_suggest_vendors_response({"query_text": "  "})
    assert result["source"] == "passthrough"
    assert result["suggestions"] == []
