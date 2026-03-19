import pytest

import watershed_retrieve as wr
from tests.conftest import KNOWN_PORTUGAL_GAUGE, PORTUGAL_GAUGE_COUNT
from watershed_retrieve import CountryNotFoundError

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _setup_data_dir(configure_data_dir: None) -> None:
    pass


class TestAvailableGauges:
    def test_returns_a_list_for_portugal(self) -> None:
        assert isinstance(wr.available_gauges("portugal"), list)

    def test_has_expected_count(self) -> None:
        assert len(wr.available_gauges("portugal")) == PORTUGAL_GAUGE_COUNT

    def test_is_sorted(self) -> None:
        gauges = wr.available_gauges("portugal")
        assert gauges == sorted(gauges)

    def test_contains_known_gauge(self) -> None:
        assert KNOWN_PORTUGAL_GAUGE in wr.available_gauges("portugal")

    def test_invalid_country_raises_country_not_found_error(self) -> None:
        with pytest.raises(CountryNotFoundError):
            wr.available_gauges("narnia")
