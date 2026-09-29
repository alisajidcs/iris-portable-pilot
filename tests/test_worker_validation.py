import pytest
from pathlib import Path
from iris_runtime.worker import prepare_records


def test_duplicate_source_identifier_rejected():
    with pytest.raises(ValueError, match="Duplicate record_id"):
        prepare_records([{"record_id": "same"}, {"record_id": "same"}])


def test_missing_geometry_is_not_invented():
    prepared = prepare_records([{"record_id": "no-geometry"}])
    assert prepared[0]["geom"] is None


def test_malformed_geometry_is_rejected():
    with pytest.raises(ValueError, match="missing coordinates"):
        prepare_records([{"record_id": "bad", "geom": {"type": "Point"}}])


def test_worker_sql_types_nullable_geometry_parameters():
    sql = (Path(__file__).parents[1] / "iris_runtime" / "worker.py").read_text()
    assert "CASE WHEN %s::text IS NULL" in sql
    assert "ST_GeomFromGeoJSON(%s::text)" in sql
