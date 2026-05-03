
def process_pdf(file_path_or_bytes):
    """
    Punto de entrada principal para procesar PDFs.
    Acepta ruta al archivo o bytes.
    """
    import os
    
    data = None
    if isinstance(file_path_or_bytes, str):
        with open(file_path_or_bytes, 'rb') as f:
            data = f.read()
    else:
        data = file_path_or_bytes

    # Intentar extracción con Gemini Vision (la más robusta)
    # Si falla, tiene sus propios fallbacks internos
    return _extract_with_gemini_vision(data)

