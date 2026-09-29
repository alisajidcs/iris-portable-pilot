"""Verify that the configured pilot data path completed successfully."""

from __future__ import annotations

import json

import psycopg

from iris_runtime.config import load_settings


def main() -> None:
    settings = load_settings()
    summary_path = settings.output_path / f"{settings.country_code}_{settings.region_code}_summary.json"
    if not summary_path.is_file():
        raise SystemExit(f"Missing worker summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT postgis_full_version()")
            postgis_version = cur.fetchone()[0]
            cur.execute(
                "SELECT count(*), count(*) FILTER (WHERE country_code IS NULL) FROM pilot_feature WHERE country_code = %s AND region_code = %s",
                (settings.country_code, settings.region_code),
            )
            count, null_country_count = cur.fetchone()
    if null_country_count:
        raise SystemExit("Smoke check failed: persisted records without country_code")
    if summary.get("feature_count") != count:
        raise SystemExit(f"Smoke check failed: summary reports {summary.get('feature_count')}, database has {count}")
    print(f"Smoke check passed for {settings.country_code}/{settings.region_code}: {count} records; {postgis_version}")


if __name__ == "__main__":
    main()
