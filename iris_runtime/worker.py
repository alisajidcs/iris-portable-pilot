"""Load configured source records into the country-scoped PostGIS table."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

from iris_runtime.config import load_settings
from iris_runtime.source import load_records


def prepare_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    prepared: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each source record must be a JSON object")
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("Each source record needs a non-empty record_id")
        if record_id in seen:
            raise ValueError(f"Duplicate record_id in source: {record_id}")
        seen.add(record_id)
        geometry = record.get("geom")
        geom_json = None
        if geometry is not None:
            if not isinstance(geometry, dict) or geometry.get("type") not in {"Point", "Polygon", "MultiPolygon"}:
                raise ValueError(f"Record {record_id} has unsupported GeoJSON geometry")
            if geometry.get("coordinates") is None:
                raise ValueError(f"Record {record_id} geometry is missing coordinates")
            geom_json = json.dumps(geometry)
        prepared.append({"record_id": record_id, "payload": json.dumps(record), "geom": geom_json})
    return prepared


def run() -> int:
    settings = load_settings()
    fixture_dir = Path(os.environ.get("FIXTURE_DIR", "/app/fixtures"))
    records = load_records(settings.source_endpoint, fixture_dir)
    prepared = prepare_records(records)

    settings.output_path.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            for row in prepared:
                cur.execute(
                    """INSERT INTO pilot_feature (country_code, region_code, record_id, source_endpoint, payload, geom)
                       VALUES (%s, %s, %s, %s, %s::jsonb,
                               CASE WHEN %s::text IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s::text), 4326) END)
                       ON CONFLICT (country_code, region_code, record_id) DO UPDATE SET
                         source_endpoint = EXCLUDED.source_endpoint,
                         payload = EXCLUDED.payload,
                         geom = EXCLUDED.geom,
                         updated_at = now()""",
                    (settings.country_code, settings.region_code, row["record_id"], settings.source_endpoint,
                     row["payload"], row["geom"], row["geom"]),
                )
            cur.execute(
                "SELECT count(*) FROM pilot_feature WHERE country_code = %s AND region_code = %s",
                (settings.country_code, settings.region_code),
            )
            count = cur.fetchone()[0]
    output_file = settings.output_path / f"{settings.country_code}_{settings.region_code}_summary.json"
    output_file.write_text(json.dumps({"country_code": settings.country_code, "region_code": settings.region_code,
                                       "source_endpoint": settings.source_endpoint, "feature_count": count}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Loaded {len(prepared)} source records; {count} records persisted for {settings.country_code}/{settings.region_code}.")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
