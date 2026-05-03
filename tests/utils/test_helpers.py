"""
Funciones de ayuda y aserciones personalizadas para los tests.
"""

def assert_valid_api_response(data: dict, required_keys: list = None):
    """
    Valida la estructura básica de una respuesta de API exitosa.
    """
    assert isinstance(data, dict), "La respuesta no es un diccionario JSON."
    assert "success" in data, "La respuesta no contiene la clave 'success'."

    if data.get("success"):
        if required_keys:
            for key in required_keys:
                assert key in data, f"La clave requerida '{key}' no está en la respuesta."
    else:
        # Si no es exitosa, debería tener un 'detail' o 'error'
        assert "detail" in data or "error" in data, "La respuesta fallida no tiene 'detail' o 'error'."