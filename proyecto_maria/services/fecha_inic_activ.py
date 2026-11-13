"""La regla de la fecha de inicio de actividad del alta, en un solo lugar:
la usan el alta y la edición (`main.py`) y la importación
(`migration_service.py`)."""
from __future__ import annotations

import re
from datetime import date


def fecha_del_alta(texto: str) -> str | None:
    """AAAA-MM-DD o DD/MM/AAAA, con año de cuatro cifras, dígitos ASCII y una
    fecha que existe, como AAAA-MM-DD. Vacío da ""; lo demás, None."""
    texto = texto.strip()
    if not texto:
        return ""
    m = re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", texto)
    if m:
        anio, mes, dia = (int(g) for g in m.groups())
    else:
        m = re.fullmatch(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})", texto)
        if not m:
            return None
        dia, mes, anio = (int(g) for g in m.groups())
    try:
        return date(anio, mes, dia).isoformat()
    except ValueError:
        return None
