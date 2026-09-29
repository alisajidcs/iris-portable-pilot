# IRIS Portable Pilot Runtime

A small Docker Compose pilot that loads explicit source fixtures into PostgreSQL 16 with PostGIS 3.4. Country, region, source endpoint, database credentials, and output path are supplied through an environment file. The worker is a one-shot job and can be rerun safely for the same country, region, and record identifiers.

## Requirements

- Docker Engine with the Compose v2 plugin
- A compatible Linux, macOS, or Windows host capable of running the pinned database image
- A host path with write access for the configured output directory

No production credentials or remote data source are needed. The pilot adapter currently supports `fixture://<name>` endpoints only.

## Run the smoke path

```sh
cp .env.dev.example .env
# Edit DB_PASSWORD to a local value before running.
make smoke
```

The `db` service reports healthy after PostgreSQL accepts connections and PostGIS is installed. The `migrate` service applies lexically ordered SQL files with `ON_ERROR_STOP`; the worker starts only after migrations complete successfully. The smoke command runs the worker and checks that the summary matches configuration and that the database contains exactly the fixture records, with expected geometry types, SRID, and missing-geometry behavior.

To use a second-host configuration, copy it to Compose's standard `.env` file:

```sh
cp .env.second-host.example .env
# Set a unique local password and adjust country, region, and host output path.
make smoke
```

The `.env` file is ignored by Git. Compose passes database credentials at runtime; the image contains no secrets. The sample passwords are placeholders and should be replaced before use. `OUTPUT_PATH` selects the worker's destination inside the container, and `HOST_OUTPUT_PATH` selects the host directory mounted there.

## Tests and useful commands

```sh
docker compose up -d db
docker compose run --build --rm worker
docker compose run --rm worker iris-smoke
python -m pip install -e '.[test]'
python -m pytest
```

The automated tests cover configuration validation, fixture path safety, source-record validation, and nullable geometry SQL. `make smoke` is the end-to-end check and requires Docker Compose.

The stack keeps the database in the named `postgres-data` volume. `docker compose down` stops services while preserving data. To intentionally reset this local pilot database, use `docker compose down --volumes`.

## Data and architecture

- `iris_runtime/config.py` validates the environment contract. Country codes are normalized to uppercase ISO alpha-2 form.
- `iris_runtime/source.py` provides a safe fixture adapter. A future country-aware remote adapter can implement the same record-list contract and be selected through `SOURCE_ENDPOINT`.
- `migrations/` contains ordered SQL migrations. `pilot_feature` uses the canonical `geom` column, an explicit EPSG:4326 geometry type, and a composite primary key containing country and region.
- Every persisted record has a non-null `country_code`. Identifiers and the primary key are scoped by country and region.
- Source attributes remain in JSONB. A provided GeoJSON geometry is converted to PostGIS geometry. A missing geometry remains `NULL`; the worker does not invent spatial attributes. The fixture labels its source date, CRS, units, completeness, and uncertainty explicitly.
- The worker writes a small count summary beneath `OUTPUT_PATH`.

## Deliberate pilot limits

The fixture is synthetic and demonstrates plumbing only. The adapter does not yet fetch remote sources, normalize country-specific schemas, transform CRSs, or infer area and distance units. Geometry coordinates are assumed to be GeoJSON longitude/latitude in EPSG:4326; production adapters should validate source CRS, completeness, source date, units, and uncertainty before persistence. A production deployment should also use managed secrets, least-privilege database roles, migration version tracking, and operational backup/retention policies.
