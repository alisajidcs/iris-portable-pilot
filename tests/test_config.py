import pytest

from iris_runtime.config import load_settings
from pathlib import Path


def valid_env(**overrides):
    env = {
        "COUNTRY_CODE": "de",
        "REGION_CODE": "nw",
        "SOURCE_ENDPOINT": "fixture://demo",
        "DB_NAME": "iris",
        "DB_USER": "iris-user",
        "DB_PASSWORD": "a@secret",
        "OUTPUT_PATH": "/tmp/iris-output",
    }
    env.update(overrides)
    return env


def test_country_and_region_are_configuration():
    settings = load_settings(valid_env(COUNTRY_CODE="NL", REGION_CODE="UT"))
    assert (settings.country_code, settings.region_code) == ("NL", "UT")


def test_database_url_quotes_credentials():
    settings = load_settings(valid_env())
    assert "iris-user:a%40secret@" in settings.database_url


def test_missing_configuration_is_reported():
    with pytest.raises(ValueError, match="SOURCE_ENDPOINT"):
        load_settings({})


def test_country_code_must_be_two_letters():
    with pytest.raises(ValueError, match="two-letter"):
        load_settings(valid_env(COUNTRY_CODE="DEU"))


@pytest.mark.parametrize("filename, country, region", [
    (".env.dev.example", "DE", "NW"),
    (".env.second-host.example", "NL", "UT"),
])
def test_documented_environment_examples_are_complete(filename, country, region):
    root = Path(__file__).parents[1]
    values = {}
    for line in (root / filename).read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value
    settings = load_settings(values)
    assert (settings.country_code, settings.region_code) == (country, region)
