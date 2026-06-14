import pytest


def test_export_csv_requires_auth(client):
    r = client.get("/api/clientes/abc/export.csv")
    assert r.status_code == 401
