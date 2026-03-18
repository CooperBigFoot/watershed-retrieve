from typing import NamedTuple

from ._errors import CountryNotFoundError


class CountryInfo(NamedTuple):
    name: str
    file_stem: str
    gauge_prefix: str


def _country(name: str, gauge_prefix: str | None = None) -> CountryInfo:
    return CountryInfo(
        name=name,
        file_stem=name,
        gauge_prefix=gauge_prefix if gauge_prefix is not None else f"{name}_",
    )


_COUNTRIES: dict[str, CountryInfo] = {
    c.name: c
    for c in [
        _country("australia"),
        _country("brazil"),
        _country("canada"),
        _country("chile"),
        _country("czech"),
        _country("france"),
        _country("germany", gauge_prefix="germany_berlin_"),
        _country("japan"),
        _country("lithuania"),
        _country("norway"),
        _country("poland"),
        _country("portugal"),
        _country("slovenia"),
        _country("south_africa"),
        _country("spain"),
        _country("uk_ea"),
        _country("uk_nrfa"),
        _country("usa"),
    ]
}

_ALIASES: dict[str, str] = {
    "french": "france",
    "southafrican": "south_africa",
    "germany_berlin": "germany",
}


def resolve_country(raw: str) -> CountryInfo:
    key = raw.strip().lower()
    if key in _COUNTRIES:
        return _COUNTRIES[key]
    if key in _ALIASES:
        return _COUNTRIES[_ALIASES[key]]
    available = ", ".join(available_country_names())
    raise CountryNotFoundError(f"Country '{key}' not supported. Available: {available}")


def available_country_names() -> list[str]:
    return sorted(_COUNTRIES)
