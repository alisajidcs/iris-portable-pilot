CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS pilot_feature (
    country_code CHAR(2) NOT NULL,
    region_code TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_endpoint TEXT NOT NULL,
    payload JSONB NOT NULL,
    geom geometry(Geometry, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (country_code, region_code, record_id)
);

CREATE INDEX IF NOT EXISTS pilot_feature_geom_gix ON pilot_feature USING GIST (geom);
CREATE INDEX IF NOT EXISTS pilot_feature_region_idx ON pilot_feature (country_code, region_code);
