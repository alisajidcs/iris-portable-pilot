"""Fixture source adapter. Remote adapters can implement the same contract."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


def load_records(endpoint: str, fixture_dir: Path) -> list[dict[str, object]]:
    parsed = urlparse(endpoint)
    if parsed.scheme != "fixture":
        raise ValueError("Only fixture:// endpoints are supported by this pilot")
    name = parsed.netloc or parsed.path.lstrip("/")
    if not name or "/" in name or ".." in name:
        raise ValueError("Fixture endpoint must name a file in the fixture directory")
    with (fixture_dir / f"{name}.json").open(encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list):
        raise ValueError("Fixture must contain a JSON array")
    return records
