from watershed_retrieve._api import _normalize_gauge_id, _strip_prefix, _to_composite
from watershed_retrieve._registry import CountryInfo
from watershed_retrieve._types import CompositeGaugeId, GaugeId

PORTUGAL = CountryInfo(name="portugal", file_stem="portugal", gauge_prefix="portugal_")
GERMANY = CountryInfo(name="germany", file_stem="germany", gauge_prefix="germany_berlin_")


class TestNormalizeGaugeId:
    def test_noop_for_clean_id(self) -> None:
        assert _normalize_gauge_id("04K-04A") == "04K-04A"

    def test_slash_replaced_with_dash(self) -> None:
        assert _normalize_gauge_id("04K/04A") == "04K-04A"

    def test_strips_whitespace(self) -> None:
        assert _normalize_gauge_id("  04K-04A  ") == "04K-04A"

    def test_slash_and_whitespace(self) -> None:
        assert _normalize_gauge_id(" 04K/04A ") == "04K-04A"


class TestToComposite:
    def test_portugal_prefix(self) -> None:
        result = _to_composite(PORTUGAL, GaugeId("04K-04A"))
        assert result == "portugal_04K-04A"

    def test_germany_custom_prefix(self) -> None:
        result = _to_composite(GERMANY, GaugeId("GAUGE001"))
        assert result == "germany_berlin_GAUGE001"

    def test_returns_composite_gauge_id_type(self) -> None:
        result = _to_composite(PORTUGAL, GaugeId("G001"))
        assert isinstance(result, str)


class TestStripPrefix:
    def test_strips_portugal_prefix(self) -> None:
        result = _strip_prefix(PORTUGAL, CompositeGaugeId("portugal_04K-04A"))
        assert result == "04K-04A"

    def test_strips_germany_prefix(self) -> None:
        result = _strip_prefix(GERMANY, CompositeGaugeId("germany_berlin_GAUGE001"))
        assert result == "GAUGE001"

    def test_no_prefix_match_returns_original(self) -> None:
        result = _strip_prefix(PORTUGAL, CompositeGaugeId("france_X001"))
        assert result == "france_X001"
