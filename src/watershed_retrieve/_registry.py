from typing import NamedTuple

from ._errors import CountryNotFoundError, InvalidArgumentError


class CountryInfo(NamedTuple):
    name: str
    file_stem: str
    gauge_prefix: str
    has_data: bool = True


def _country(name: str, gauge_prefix: str | None = None, has_data: bool = True) -> CountryInfo:
    return CountryInfo(
        name=name,
        file_stem=name,
        gauge_prefix=gauge_prefix if gauge_prefix is not None else f"{name}_",
        has_data=has_data,
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
        _country("uk_ea", has_data=False),
        _country("uk_nrfa", has_data=False),
        _country("usa"),
    ]
}

_ALIASES: dict[str, str] = {
    "french": "france",
    "southafrican": "south_africa",
    "southafrica": "south_africa",
    "germany_berlin": "germany",
    "czech_republic": "czech",
    "czechrepublic": "czech",
}


def resolve_country(raw: str) -> CountryInfo:
    if not isinstance(raw, str):
        raise InvalidArgumentError(f"country must be a str, got {type(raw).__name__!r}")
    key = raw.strip().lower().replace(" ", "_")
    if key in _COUNTRIES:
        return _COUNTRIES[key]
    if key in _ALIASES:
        return _COUNTRIES[_ALIASES[key]]
    available = ", ".join(available_country_names())
    raise CountryNotFoundError(f"Country '{raw.strip()}' not supported. Available: {available}")


def available_country_names() -> list[str]:
    return sorted(_COUNTRIES)
