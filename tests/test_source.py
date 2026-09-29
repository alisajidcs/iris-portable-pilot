import json

import pytest

from iris_runtime.source import load_records


def test_load_fixture(tmp_path):
    (tmp_path / "demo.json").write_text(json.dumps([{"record_id": "one"}]))
    assert load_records("fixture://demo", tmp_path) == [{"record_id": "one"}]


def test_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError, match="name a file"):
        load_records("fixture://../outside", tmp_path)


def test_rejects_remote_source_until_adapter_exists(tmp_path):
    with pytest.raises(ValueError, match="Only fixture"):
        load_records("https://example.test/data.json", tmp_path)
