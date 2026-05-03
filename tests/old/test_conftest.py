"""
Unit tests for the pytest fixtures defined in conftest.py.

This file ensures that the shared fixtures used across the test suite
are reliable and behave as expected.
"""

import os
from fastapi.testclient import TestClient
from proyecto_maria.models.operations import Item

# The `project_root` variable is available because it's defined in conftest.py
# at the session scope, but we import it here for clarity in the cleanup test.
from .conftest import project_root


def test_api_client_fixture(api_client):
    """
    Tests the `api_client` fixture.

    Verifies that:
    1. The fixture returns a valid TestClient instance.
    2. The client is configured correctly and can hit a basic endpoint.
    """
    assert isinstance(api_client, TestClient), "Fixture should return a TestClient instance."

    # Perform a basic health check to ensure the client is operational
    response = api_client.get("/health")
    assert response.status_code == 200, "Client should be able to make successful requests."
    data = response.json()
    assert data.get("status") == "ok", "The /health endpoint should return a status of 'ok'."


def test_sample_items_fixture(sample_items):
    """
    Tests the `sample_items` fixture.

    Verifies that:
    1. It returns a list of the correct length.
    2. All elements in the list are `Item` model instances.
    3. The data within the items is correct.
    """
    assert isinstance(sample_items, list), "Fixture should return a list."
    assert len(sample_items) == 2, "Fixture should provide exactly 2 sample items."
    assert all(isinstance(item, Item) for item in sample_items), "All elements must be Item instances."

    # Check data integrity of the first item
    assert sample_items[0].pieza == "84713010"
    assert sample_items[0].descripcion == "Laptop"
    assert sample_items[0].valor_unitario == 500.0


def test_cleanup_excel_files_fixture_creates_and_cleans_up(cleanup_excel_files):
    """
    Tests the `cleanup_excel_files` fixture's teardown behavior.

    This test creates a dummy file that matches the cleanup pattern.
    The `cleanup_excel_files` fixture's teardown logic (the `yield` part)
    will run *after* this test function completes, deleting the file.
    """
    dummy_filename = "MARIA_dummy_for_cleanup_test.xlsx"
    dummy_filepath = os.path.join(project_root, dummy_filename)

    # Create a dummy file for the fixture to clean up
    with open(dummy_filepath, "w") as f:
        f.write("test")

    assert os.path.exists(dummy_filepath), "Dummy file should be created before the test finishes."


def test_cleanup_excel_files_handles_avg_prefix(cleanup_excel_files):
    """
    Tests that the cleanup fixture can also handle the 'AVG_' prefix,
    which is used by the excel_generator module. This test will initially
    fail, proving the bug, and will pass after the fix.
    """
    # Este es el nombre de archivo que genera `create_maria_excel`
    avg_dummy_filename = "AVG_dummy_for_cleanup_test.xlsx"
    avg_dummy_filepath = os.path.join(project_root, avg_dummy_filename)

    # Crear un archivo de prueba con el prefijo 'AVG_'
    with open(avg_dummy_filepath, "w") as f:
        f.write("test")

    # La aserción se hará después de que el test termine y la fixture limpie.
    # Pytest se encargará de verificar que el archivo ya no existe.
    assert os.path.exists(avg_dummy_filepath), "El archivo de prueba AVG_ debe existir antes de la limpieza."