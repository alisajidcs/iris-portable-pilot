"""Verify that the configured pilot data path completed successfully."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

from iris_runtime.config import load_settings
from iris_runtime.source import load_records


def main() -> None:
    settings = load_settings()
    summary_path = settings.output_path / f"{settings.country_code}_{settings.region_code}_summary.json"
    if not summary_path.is_file():
        raise SystemExit(f"Missing worker summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for key, expected in (("country_code", settings.country_code),
                          ("region_code", settings.region_code),
                          ("source_endpoint", settings.source_endpoint)):
        if summary.get(key) != expected:
            raise SystemExit(f"Smoke check failed: summary {key} is {summary.get(key)!r}, expected {expected!r}")
    fixture_dir = Path(os.environ.get("FIXTURE_DIR", "/app/fixtures"))
    expected_records = load_records(settings.source_endpoint, fixture_dir)
    expected_ids = sorted(record["record_id"] for record in expected_records)
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT PostGIS_Full_Version(), version()")
            postgis_full_version, postgres_full_version = cur.fetchone()
            cur.execute(
                """SELECT record_id, country_code, ST_SRID(geom), ST_GeometryType(geom)
                   FROM pilot_feature WHERE country_code = %s AND region_code = %s
                   ORDER BY record_id""",
                (settings.country_code, settings.region_code),
            )
            rows = cur.fetchall()
    actual_ids = [row[0] for row in rows]
    if actual_ids != expected_ids:
        raise SystemExit(f"Smoke check failed: database record IDs {actual_ids!r}, fixture has {expected_ids!r}")
    expected_by_id = {record["record_id"]: record for record in expected_records}
    for record_id, country_code, srid, geometry_type in rows:
        if country_code != settings.country_code:
            raise SystemExit(f"Smoke check failed: record {record_id} has country_code {country_code!r}")
        fixture_geometry = expected_by_id[record_id].get("geom")
        if fixture_geometry is None:
            if srid is not None or geometry_type is not None:
                raise SystemExit(f"Smoke check failed: record {record_id} should have NULL geometry")
        elif srid != 4326 or geometry_type != f"ST_{fixture_geometry['type']}":
            raise SystemExit(f"Smoke check failed: record {record_id} geometry is {geometry_type} SRID {srid}, expected ST_{fixture_geometry['type']} SRID 4326")
    count = len(rows)
    if summary.get("feature_count") != count:
        raise SystemExit(f"Smoke check failed: summary reports {summary.get('feature_count')}, database has {count}")
    postgis_version = postgis_full_version.split()[0].split("=", 1)[-1]
    postgres_version = postgres_full_version.split()[1]
    print("Smoke check passed")
    print(f"  Region:   {settings.country_code}/{settings.region_code}")
    print(f"  Records:  {count} fixture records verified")
    print(f"  Database: PostgreSQL {postgres_version} with PostGIS {postgis_version}")


if __name__ == "__main__":
    main()
