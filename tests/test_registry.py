import pytest

from watershed_retrieve import CountryNotFoundError
from watershed_retrieve._registry import available_country_names, resolve_country


class TestResolveCountry:
    def test_exact_name(self) -> None:
        info = resolve_country("portugal")
        assert info.name == "portugal"
        assert info.file_stem == "portugal"

    def test_case_insensitive(self) -> None:
        info = resolve_country("PORTUGAL")
        assert info.name == "portugal"

    def test_strips_whitespace(self) -> None:
        info = resolve_country("  portugal  ")
        assert info.name == "portugal"

    def test_alias_french(self) -> None:
        info = resolve_country("french")
        assert info.name == "france"

    def test_alias_southafrican(self) -> None:
        info = resolve_country("southafrican")
        assert info.name == "south_africa"

    def test_alias_germany_berlin(self) -> None:
        info = resolve_country("germany_berlin")
        assert info.name == "germany"

    def test_unknown_country_raises(self) -> None:
        with pytest.raises(CountryNotFoundError, match="narnia"):
            resolve_country("narnia")

    def test_error_message_lists_available(self) -> None:
        with pytest.raises(CountryNotFoundError, match="australia"):
            resolve_country("atlantis")


class TestAvailableCountryNames:
    def test_returns_sorted_list(self) -> None:
        names = available_country_names()
        assert names == sorted(names)

    def test_has_18_entries(self) -> None:
        assert len(available_country_names()) == 18

    def test_all_lowercase(self) -> None:
        for name in available_country_names():
            assert name == name.lower()


class TestCountryInfo:
    def test_default_gauge_prefix(self) -> None:
        info = resolve_country("portugal")
        assert info.gauge_prefix == "portugal_"

    def test_custom_gauge_prefix_germany(self) -> None:
        info = resolve_country("germany")
        assert info.gauge_prefix == "germany_berlin_"

    def test_has_data_true_by_default(self) -> None:
        info = resolve_country("portugal")
        assert info.has_data is True

    def test_uk_ea_has_no_data(self) -> None:
        info = resolve_country("uk_ea")
        assert info.has_data is False

    def test_uk_nrfa_has_no_data(self) -> None:
        info = resolve_country("uk_nrfa")
        assert info.has_data is False
