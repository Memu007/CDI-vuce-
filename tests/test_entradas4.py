"""Todo campo `Form` de texto de la app pasa por `_guardable_en_pg`: Postgres
rechaza un NUL y la ruta daría 500. Lo que hace la ruta con el NUL contra
Postgres lo mide `scripts/testing/entradas4_postgres.py`.
"""
import enum
import typing

from fastapi.params import Form
from fastapi.routing import APIRoute, iter_route_contexts
from pydantic import BaseModel

import proyecto_maria.main as m


def _textos(tipo, guardado=False):
    """Por cada texto dentro del tipo, si pasa por `_guardable_en_pg`."""
    if typing.get_origin(tipo) is typing.Annotated:
        base, *meta = typing.get_args(tipo)
        yield from _textos(base, guardado or any(getattr(x, "func", None) is m._guardable_en_pg for x in meta))
    elif isinstance(tipo, type) and issubclass(tipo, BaseModel):
        for f in tipo.model_fields.values():
            yield from _textos(f.annotation, guardado or any(getattr(x, "func", None) is m._guardable_en_pg
                                                             for x in f.metadata))
    elif isinstance(tipo, type) and issubclass(tipo, str):
        # Un Enum de texto sólo acepta sus valores: un NUL da 422.
        if not issubclass(tipo, enum.Enum):
            yield guardado
    else:
        for t in typing.get_args(tipo):
            yield from _textos(t, guardado)


def _dependencias(d):
    yield d
    for sub in d.dependencies:
        yield from _dependencias(sub)


def campos_form_de_texto(rutas):
    """(ruta, campo, guardado) de cada `Form` de texto, también de routers, `Depends` y montajes."""
    for contexto in iter_route_contexts(rutas):
        ruta = contexto.route
        if not isinstance(ruta, APIRoute):
            yield from campos_form_de_texto(getattr(ruta, "routes", []))
            continue
        for d in _dependencias(ruta.dependant):
            for campo in d.body_params:
                textos = list(_textos(campo.field_info.annotation))
                if isinstance(campo.field_info, Form) and textos:
                    yield contexto.path, campo.alias, all(textos)


def test_form_de_texto_pasa_por_guardable_en_pg():
    campos = list(campos_form_de_texto(m.app.routes))
    assert campos, "no encontró ningún campo Form de texto: la búsqueda está rota"
    sin_guarda = [(ruta, campo) for ruta, campo, guardado in campos if not guardado]
    assert not sin_guarda, f"campos Form de texto sin _guardable_en_pg: {sin_guarda}"
