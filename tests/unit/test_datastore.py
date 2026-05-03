import pytest

from proyecto_maria.core import datastore


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch):
    datastore._reset_backend_cache_for_tests()
    monkeypatch.delenv("DATASTORE_BACKEND", raising=False)
    monkeypatch.delenv("DATASTORE_DISABLE_DB", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    yield
    datastore._reset_backend_cache_for_tests()


def test_forced_memory_backend(monkeypatch):
    monkeypatch.setenv("DATASTORE_BACKEND", "memory")
    ds = datastore.DataStore()
    assert ds.using_postgres is False


def test_disable_db_flag(monkeypatch):
    monkeypatch.setenv("DATASTORE_DISABLE_DB", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://should/not/use")
    ds = datastore.DataStore()
    assert ds.using_postgres is False


def test_postgres_failure_cached(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fail")

    call_count = {"value": 0}

    class BoomBackend:
        def __init__(self, db_url, user_id):
            call_count["value"] += 1
            raise RuntimeError("boom")

    monkeypatch.setattr(datastore, "PostgreSQLBackend", BoomBackend)

    ds = datastore.DataStore()
    assert ds.using_postgres is False
    assert call_count["value"] == 1

    ds2 = datastore.DataStore()
    assert ds2.using_postgres is False
    assert call_count["value"] == 1, "should not retry postgres init after cached failure"


def test_forced_postgres_raises(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fail")
    monkeypatch.setenv("DATASTORE_BACKEND", "postgres")

    class BoomBackend:
        def __init__(self, db_url, user_id):
            raise RuntimeError("boom")

    monkeypatch.setattr(datastore, "PostgreSQLBackend", BoomBackend)

    with pytest.raises(RuntimeError):
        datastore.DataStore()

