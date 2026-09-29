"""Environment-backed runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


@dataclass(frozen=True)
class Settings:
    country_code: str
    region_code: str
    source_endpoint: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    output_path: Path

    @property
    def database_url(self) -> str:
        user = quote(self.db_user, safe="")
        password = quote(self.db_password, safe="")
        return f"postgresql://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    env = os.environ if environ is None else environ
    required = ("COUNTRY_CODE", "REGION_CODE", "SOURCE_ENDPOINT", "DB_NAME", "DB_USER", "DB_PASSWORD", "OUTPUT_PATH")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    country = env["COUNTRY_CODE"].strip().upper()
    region = env["REGION_CODE"].strip().upper()
    if len(country) != 2 or not country.isalpha():
        raise ValueError("COUNTRY_CODE must be a two-letter ISO country code")
    if not region or not region.replace("-", "").isalnum():
        raise ValueError("REGION_CODE must contain only letters, numbers, or hyphens")
    return Settings(
        country_code=country,
        region_code=region,
        source_endpoint=env["SOURCE_ENDPOINT"],
        db_host=env.get("DB_HOST", "db"),
        db_port=int(env.get("DB_PORT", "5432")),
        db_name=env["DB_NAME"],
        db_user=env["DB_USER"],
        db_password=env["DB_PASSWORD"],
        output_path=Path(env["OUTPUT_PATH"]),
    )
