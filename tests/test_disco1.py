"""DISCO-1: el historial de NCM vive en la base, no en el disco.

Antes vivía en `ncm_historial_<usuario>.json` dentro de DATA_DIR, que en
Railway se borra en cada deploy. Ahora es la tabla `ncm_historial`, por
dueño, con el mismo comportamiento: misma clave (la descripción tal cual),
confirmar otra vez suma uno y actualiza la NCM, importar suma igual y cuenta
los duplicados igual. Los archivos que hubiera se cargan una sola vez al
arrancar. El caso en Postgres está en `scripts/testing/disco1_postgres.py`.
"""
import asyncio
import json
import logging
import os
import shutil
import uuid

import httpx
import pytest
from sqlalchemy import delete, select

from proyecto_maria import main
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import NcmHistorial, User
from proyecto_maria.main import app, get_current_user


def _usuario(base, prefijo="disco1"):
    u = dict(base)
    u["username"] = u["effective_owner"] = f"{prefijo}_{uuid.uuid4().hex[:8]}"
    return u


def _como(usuario):
    app.dependency_overrides[get_current_user] = lambda: usuario


async def _filas_async(owner):
    async with AsyncSessionLocal() as s:
        r = await s.execute(
            select(NcmHistorial.descripcion, NcmHistorial.ncm, NcmHistorial.count)
            .where(NcmHistorial.owner_username == owner)
            .order_by(NcmHistorial.id)
        )
        return [tuple(f) for f in r.all()]


def _filas(owner):
    return asyncio.run(_filas_async(owner))


async def _borrar(owners):
    async with AsyncSessionLocal() as s:
        await s.execute(delete(NcmHistorial).where(NcmHistorial.owner_username.in_(owners)))
        await s.execute(delete(User).where(User.username.in_(owners)))
        await s.commit()


@pytest.fixture()
def duenos(client, auth_override, monkeypatch, tmp_path):
    """Dueños propios (nunca test_user) y un DATA_DIR descartable; al terminar
    se borra lo que crearon."""
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "false")
    monkeypatch.setattr(main, "DATA_DIR", str(tmp_path / "data"))
    os.makedirs(main.DATA_DIR)
    creados = []

    def nuevo(prefijo="disco1"):
        u = _usuario(auth_override, prefijo)
        creados.append(u["username"])
        _crear_usuarios(u["username"])
        return u
    yield nuevo
    app.dependency_overrides[get_current_user] = lambda: auth_override
    asyncio.run(_borrar(creados))


def _confirmar(client, desc, ncm):
    r = client.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": ncm})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True, r.text


def _del_historial(client, desc):
    r = client.post("/api/ncm/sugerir", json={"descripcion": desc})
    assert r.status_code == 200, r.text
    return [{k: s.get(k) for k in ("ncm", "desc", "count")}
            for s in r.json()["sugerencias"] if s["source"] == "historial"]


def _importar(client, texto):
    return client.post("/api/ncm/import-historial",
                       files={"file": ("historial.csv", texto.encode("utf-8"), "text/csv")})


# --- guardar, sugerir e importar con el historial en la base -----------------

def test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm(client, duenos):
    a = duenos()
    _como(a)
    desc = "Bomba centrifuga sintetica"
    _confirmar(client, desc, "8413.70.10")
    assert _filas(a["username"]) == [(desc, "8413.70.10", 1)]

    _confirmar(client, desc, "8413.70.90")
    assert _filas(a["username"]) == [(desc, "8413.70.90", 2)], "confirmar otra vez suma uno y actualiza la NCM"

    sug = _del_historial(client, "bomba centrifuga sintetica")
    assert sug == [{"ncm": "8413.70.90", "desc": desc, "count": 2}], sug
    assert not any(n.startswith("ncm_historial") for n in os.listdir(main.DATA_DIR)), \
        "el historial ya no se escribe en DATA_DIR"


def test_la_clave_es_la_descripcion_tal_cual(client, duenos):
    """Como en el archivo: «Tornillo» y «tornillo » son claves distintas
    (guardar-uso recorta los espacios de las puntas)."""
    a = duenos()
    _como(a)
    _confirmar(client, "Tornillo M6 sintetico", "7318.15.00")
    _confirmar(client, "TORNILLO M6 SINTETICO", "7318.15.00")
    _confirmar(client, "  Tornillo M6 sintetico  ", "7318.15.00")
    assert _filas(a["username"]) == [
        ("Tornillo M6 sintetico", "7318.15.00", 2),
        ("TORNILLO M6 SINTETICO", "7318.15.00", 1),
    ]


def test_sobrevive_a_que_se_borre_data_dir(client, duenos):
    a = duenos()
    _como(a)
    desc = "Valvula esferica sintetica"
    _confirmar(client, desc, "8481.80.95")
    shutil.rmtree(main.DATA_DIR)
    os.makedirs(main.DATA_DIR)
    sug = _del_historial(client, desc)
    assert [s["ncm"] for s in sug] == ["8481.80.95"], "el historial se perdió con DATA_DIR"


def test_importar_suma_igual_y_cuenta_duplicados_igual(client, duenos):
    a = duenos()
    _como(a)
    _confirmar(client, "Cable sintetico A", "8544.49.00")
    _confirmar(client, "Cable sintetico A", "8544.49.00")
    r = _importar(client, (
        "descripcion,ncm\n"
        "Cable sintetico A,8544.42.00\n"    # ya estaba: duplicado, nueva NCM, cuenta igual
        "Cable sintetico B,8544.11.00\n"    # nuevo
        "Cable sintetico B,8544.19.00\n"    # repetido en el archivo: duplicado
        "Cable sintetico C,8544\n"          # NCM corta: error
        ",8544.11.00\n"                     # sin descripción: se saltea
    ))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["importados"], cuerpo["duplicados"]) == (1, 2), cuerpo
    assert [e["fila"] for e in cuerpo["errores"]] == [5], cuerpo
    assert _filas(a["username"]) == [
        ("Cable sintetico A", "85444200", 2),
        ("Cable sintetico B", "85441900", 1),
    ]
    # Lo importado se sugiere igual que lo confirmado.
    assert [s["ncm"] for s in _del_historial(client, "cable sintetico b")] == ["85441900"]


def test_si_no_se_puede_guardar_lo_importado_da_500_y_no_queda_nada(client, duenos, monkeypatch, caplog):
    """La importación se guarda entera o nada: falla la segunda tanda de filas
    y la primera tampoco queda."""
    a = duenos()
    _como(a)
    monkeypatch.setattr(main, "_HISTORIAL_FILAS_POR_SENTENCIA", 1)
    original, llamadas = main._insert_ncm_historial, []

    def _falla_la_segunda():
        llamadas.append(1)
        if len(llamadas) == 2:
            raise RuntimeError("falla simulada al guardar el historial")
        return original()
    monkeypatch.setattr(main, "_insert_ncm_historial", _falla_la_segunda)
    from fastapi.testclient import TestClient
    r = TestClient(app, raise_server_exceptions=False).post(
        "/api/ncm/import-historial",
        files={"file": ("h.csv", b"descripcion,ncm\nGrifo sintetico,8481.80.99\nCanilla sintetica,8481.80.99\n",
                        "text/csv")})
    assert r.status_code == 500, r.text
    assert "No se pudo guardar: falla simulada" in caplog.text
    assert len(llamadas) == 2
    assert _filas(a["username"]) == [], "quedó guardada una parte de la importación"


# --- dos dueños --------------------------------------------------------------

def test_un_dueno_no_ve_ni_pisa_el_historial_de_otro(client, duenos):
    a, b = duenos(), duenos()
    desc = "Motor electrico sintetico"
    _como(a)
    _confirmar(client, desc, "8501.52.10")

    _como(b)
    assert _del_historial(client, desc) == [], "b ve el historial de a"
    _confirmar(client, desc, "8501.53.10")
    r = _importar(client, f"descripcion,ncm\n{desc},8501.40.11\n")
    assert r.status_code == 200 and r.json()["duplicados"] == 1, r.text

    assert _filas(a["username"]) == [(desc, "8501.52.10", 1)], "b pisó el historial de a"
    assert _filas(b["username"]) == [(desc, "85014011", 1)]
    _como(a)
    assert [s["ncm"] for s in _del_historial(client, desc)] == ["8501.52.10"]


# --- dos confirmaciones a la vez ---------------------------------------------

def test_confirmaciones_a_la_vez_no_pierden_cuentas(client, duenos):
    a = duenos()
    _como(a)
    desc = "Rodamiento sintetico concurrente"
    n = 8

    async def _todas():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            return await asyncio.gather(*[
                c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": "8482.10.10"})
                for _ in range(n)
            ])
    respuestas = asyncio.run(_todas())
    assert all(r.status_code == 200 for r in respuestas), [r.text for r in respuestas]
    assert _filas(a["username"]) == [(desc, "8482.10.10", n)], "se perdió una confirmación"


# --- los archivos que había ---------------------------------------------------

def _crear_usuarios(*nombres):
    async def _crear():
        async with AsyncSessionLocal() as s:
            for n in nombres:
                s.add(User(username=n, password="x", name=n, plan="premium", billing_status="active"))
            await s.commit()
    asyncio.run(_crear())


def _archivo(owner_seguro, contenido):
    ruta = os.path.join(main.DATA_DIR, f"ncm_historial_{owner_seguro}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido if isinstance(contenido, str) else json.dumps(contenido, ensure_ascii=False))
    return ruta


def _cargar_archivos():
    asyncio.run(main._migrate_ncm_historial_archivos())


def test_los_archivos_viejos_se_cargan_una_sola_vez(client, duenos):
    a = duenos()
    ruta = _archivo(a["username"], {
        "Bomba sintetica vieja": {"ncm": "8413.70.10", "count": 3},
        "Filtro sintetico viejo": {"ncm": "8421.23.00", "count": 1},
    })
    _cargar_archivos()
    assert _filas(a["username"]) == [
        ("Bomba sintetica vieja", "8413.70.10", 3),
        ("Filtro sintetico viejo", "8421.23.00", 1),
    ]
    assert not os.path.exists(ruta), "el archivo cargado no se tiene que volver a leer"

    _como(a)
    _confirmar(client, "Bomba sintetica vieja", "8413.70.10")
    _cargar_archivos()
    assert _filas(a["username"])[0] == ("Bomba sintetica vieja", "8413.70.10", 4)

    # Aunque el archivo vuelva a aparecer (no se pudo renombrar, se restauró
    # una copia), cargarlo otra vez no duplica cuentas.
    _archivo(a["username"], {"Bomba sintetica vieja": {"ncm": "8413.70.10", "count": 3}})
    _cargar_archivos()
    assert _filas(a["username"])[0] == ("Bomba sintetica vieja", "8413.70.10", 4)


def test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas(client, duenos, caplog):
    a, b, c = duenos(), duenos(), duenos()
    roto = _archivo(a["username"], '{"Bomba": {"ncm": "8413')
    no_dict = _archivo(b["username"], '["no", "es", "un", "historial"]')
    _archivo(c["username"], {
        "Junta sintetica": {"ncm": "4016.93.00", "count": 2},
        "Sin ncm": {"count": 2},
        "No es entrada": "8413.70.10",
        "Cuenta rara": {"ncm": "4016.99.90", "count": "muchas"},
    })
    with caplog.at_level(logging.WARNING):
        _cargar_archivos()
    assert _filas(a["username"]) == [] and _filas(b["username"]) == []
    assert _filas(c["username"]) == [
        ("Junta sintetica", "4016.93.00", 2),
        ("Cuenta rara", "4016.99.90", 1),
    ]
    assert os.path.basename(roto) in caplog.text and os.path.basename(no_dict) in caplog.text, caplog.text
    # Las entradas salteadas se cuentan, sin copiar descripciones al log;
    # el archivo queda como `.migrado`.
    assert f"ncm_historial_{c['username']}.json: 2 entradas sin descripción o sin NCM" in caplog.text, caplog.text


def test_un_archivo_sin_dueno_claro_no_se_le_carga_a_nadie(client, duenos, caplog):
    """El nombre del archivo es el usuario con los signos cambiados por «_»:
    «x.y» y «x_y» compartían archivo. No se adivina de quién es."""
    base = duenos()["username"]
    punto, guion = f"{base}.p", f"{base}_p"
    _crear_usuarios(punto, guion)
    try:
        ambiguo = _archivo(f"{base}_p", {"Llave sintetica": {"ncm": "8481.80.99", "count": 1}})
        huerfano = _archivo(f"{base}_nadie", {"Llave sintetica": {"ncm": "8481.80.99", "count": 1}})
        with caplog.at_level(logging.WARNING):
            _cargar_archivos()
        assert _filas(punto) == [] and _filas(guion) == []
        assert os.path.exists(ambiguo) and os.path.exists(huerfano), "lo que no se cargó queda en su lugar"
        assert os.path.basename(ambiguo) in caplog.text and os.path.basename(huerfano) in caplog.text
    finally:
        asyncio.run(_borrar([punto, guion]))


def test_el_arranque_carga_los_archivos(monkeypatch):
    llamadas = []

    async def _espia():
        llamadas.append(1)
    monkeypatch.setattr(main, "_migrate_ncm_historial_archivos", _espia)
    from fastapi.testclient import TestClient
    with TestClient(app):
        pass
    assert llamadas == [1]


# --- devolución: topes, caracteres que la base no guarda, orden, `.migrado` ---

def _sin_excepciones():
    from fastapi.testclient import TestClient
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("desc,ncm,dice", [
    ("B" * 2001, "8413.70.10", "La descripción pasa de 2000 caracteres"),
    ("Bomba sintetica", "8" * 21, "La NCM pasa de 20 caracteres"),
    ("Bomba\x00sintetica", "8413.70.10", "La descripción tiene un carácter nulo"),
    ("Bomba sintetica", "8413.70.10\x00", "La NCM tiene un carácter nulo"),
    ("Bomba\ud800sintetica", "8413.70.10", "La descripción tiene un carácter que no es texto válido"),
])
def test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda(client, duenos, desc, ncm, dice):
    a = duenos()
    _como(a)
    r = _sin_excepciones().post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": ncm})
    assert r.status_code == 400, r.text
    assert dice in r.json()["detail"], r.text
    assert _filas(a["username"]) == []


@pytest.mark.parametrize("client_id,status", [
    ("cliente\x00sintetico", 400), ("cliente\ud800sintetico", 400), ("cliente-ajeno-sintetico", 404),
])
def test_confirmar_con_un_cliente_que_no_sirve_no_suma(client, duenos, client_id, status):
    """El error llega antes de escribir: reintentar no suma otra vez."""
    a = duenos()
    _como(a)
    _confirmar(client, "Bomba sintetica", "8413.70.10")
    r = _sin_excepciones().post("/api/ncm/guardar-uso", json={
        "descripcion": "Bomba sintetica", "ncm": "8413.70.10", "client_id": client_id})
    assert r.status_code == status, r.text
    assert _filas(a["username"]) == [("Bomba sintetica", "8413.70.10", 1)]


def test_confirmar_en_el_tope_entra(client, duenos):
    a = duenos()
    _como(a)
    # Un NCM de 20 caracteres no es un NCM (DESPACHO-1b): el más largo que entra.
    _confirmar(client, "B" * 2000, "8471.49.00.100D")
    assert _filas(a["username"]) == [("B" * 2000, "8471.49.00.100D", 1)]


@pytest.mark.parametrize("desc,ncm,dice", [
    ("B" * 2001, "8413.70.10", "Fila 3: la descripción pasa de 2000 caracteres"),
    ("Bomba sintetica", "8413.70.10.0000000000000", "Fila 3: la NCM pasa de 20 caracteres"),
    ("Bomba\x00sintetica", "8413.70.10", "Fila 3: la descripción tiene un carácter nulo"),
    ("Bomba\ud800sintetica", "8413.70.10", "Fila 3: la descripción tiene un carácter que no es texto válido"),
])
def test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada(
        client, duenos, monkeypatch, desc, ncm, dice):
    """Una fila mala frena el archivo entero y dice cuál es. El CSV corta en
    el NUL y el Excel no lo trae: la tabla se arma a mano."""
    import pandas as pd
    a = duenos()
    _como(a)
    tabla = pd.DataFrame({"descripcion": ["Polea sintetica", desc], "ncm": ["8483.50.10", ncm]})
    monkeypatch.setattr(main, "_leer_tabla", lambda content, filename: tabla)
    r = _sin_excepciones().post("/api/ncm/import-historial",
                                files={"file": ("h.csv", b"descripcion,ncm\nx,84835010\n", "text/csv")})
    assert r.status_code == 400, r.text
    assert dice in r.json()["detail"], r.text
    assert _filas(a["username"]) == [], "se guardó una parte del archivo"


def _en_orden_contrario_a_la_clave(prefijo, n=7):
    return sorted((f"{prefijo} {k}" for k in range(n)), key=main._clave_ncm_historial, reverse=True)


def test_importar_respeta_el_orden_del_archivo_para_sugerir(client, duenos, monkeypatch):
    """Lo importado se sugiere en el orden del archivo, también entre tandas;
    no en el de la clave."""
    a = duenos()
    _como(a)
    monkeypatch.setattr(main, "_HISTORIAL_FILAS_POR_SENTENCIA", 3)
    descs = _en_orden_contrario_a_la_clave("Arandela sintetica")
    r = _importar(client, "descripcion,ncm\n" + "".join(f"{d},7318.22.{n:02d}\n" for n, d in enumerate(descs)))
    assert r.status_code == 200 and r.json()["importados"] == 7, r.text
    assert [f[0] for f in _filas(a["username"])] == descs
    assert [s["desc"] for s in _del_historial(client, "arandela sintetica")] == descs[:5]


def test_un_archivo_viejo_se_carga_en_su_orden(client, duenos, monkeypatch):
    a = duenos()
    _como(a)
    monkeypatch.setattr(main, "_HISTORIAL_FILAS_POR_SENTENCIA", 3)
    descs = _en_orden_contrario_a_la_clave("Brida sintetica")
    _archivo(a["username"], {d: {"ncm": f"7307.21.{n:02d}", "count": 1} for n, d in enumerate(descs)})
    _cargar_archivos()
    assert [f[0] for f in _filas(a["username"])] == descs
    assert [s["desc"] for s in _del_historial(client, "brida sintetica")] == descs[:5]


def test_sugerir_recorre_el_historial_en_el_orden_en_que_se_agrego(client, duenos):
    """Las primeras cinco que coinciden, en el orden en que se confirmaron; no
    en el de la clave."""
    a = duenos()
    _como(a)
    descs = sorted((f"Tuerca sintetica {n}" for n in range(7)),
                   key=main._clave_ncm_historial, reverse=True)
    for n, d in enumerate(descs):
        _confirmar(client, d, f"7318.16.{n:02d}")
    sug = _del_historial(client, "tuerca sintetica")
    assert [s["desc"] for s in sug] == descs[:5]


def test_importar_muchas_filas_va_en_tandas(client, duenos, monkeypatch):
    """7000 filas son 35000 parámetros: en una sola sentencia pasan el tope de
    asyncpg (32767) y el de los SQLite compilados con el de fábrica (32766).
    El SQLite de la prueba puede tener otro tope: se mira cuántas filas lleva
    cada sentencia."""
    a = duenos()
    _como(a)
    original, por_sentencia = main._insert_ncm_historial, []

    class _Espia:
        def __init__(self):
            self._ins = original()

        def values(self, filas):
            por_sentencia.append(len(filas))
            return self._ins.values(filas)
    monkeypatch.setattr(main, "_insert_ncm_historial", _Espia)
    r = _importar(client, "descripcion,ncm\n" + "".join(f"Perno sintetico {n},7318.15.00\n" for n in range(7000)))
    assert r.status_code == 200 and r.json()["importados"] == 7000, r.text[:300]
    assert len(_filas(a["username"])) == 7000
    assert sum(por_sentencia) == 7000 and max(por_sentencia) * 5 <= 999, por_sentencia[:3]


def test_un_archivo_viejo_con_cuenta_cero_o_negativa_carga_cuenta_uno(client, duenos):
    a = duenos()
    _archivo(a["username"], {
        "Codo sintetico cero": {"ncm": "7307.19.00", "count": 0},
        "Codo sintetico negativo": {"ncm": "7307.19.00", "count": -2},
    })
    _cargar_archivos()
    assert _filas(a["username"]) == [
        ("Codo sintetico cero", "7307.19.00", 1),
        ("Codo sintetico negativo", "7307.19.00", 1),
    ]


def test_un_archivo_viejo_con_descripcion_en_blanco_no_la_carga(client, duenos, caplog):
    a = duenos()
    _archivo(a["username"], {
        "   ": {"ncm": "7307.19.00", "count": 1},
        "Codo sintetico": {"ncm": "7307.19.00", "count": 1},
    })
    with caplog.at_level(logging.WARNING):
        _cargar_archivos()
    assert _filas(a["username"]) == [("Codo sintetico", "7307.19.00", 1)]
    assert f"ncm_historial_{a['username']}.json: 1 entradas sin descripción o sin NCM" in caplog.text, caplog.text


def test_el_archivo_cargado_queda_como_migrado_con_su_contenido(client, duenos):
    a = duenos()
    contenido = {"Codo sintetico": {"ncm": "7307.19.00", "count": 2}}
    ruta = _archivo(a["username"], contenido)
    _cargar_archivos()
    with open(ruta + ".migrado", encoding="utf-8") as f:
        assert json.load(f) == contenido, "el archivo cargado no quedó como .migrado"


def test_un_migrado_anterior_no_se_pisa(client, duenos):
    a = duenos()
    ruta = _archivo(a["username"], {"Codo sintetico viejo": {"ncm": "7307.19.00", "count": 1}})
    _cargar_archivos()
    _archivo(a["username"], {"Codo sintetico nuevo": {"ncm": "7307.19.00", "count": 1}})
    _cargar_archivos()
    _archivo(a["username"], {"Codo sintetico otro": {"ncm": "7307.19.00", "count": 1}})
    _cargar_archivos()
    leidos = []
    for sufijo in (".migrado", ".migrado.1", ".migrado.2"):
        with open(ruta + sufijo, encoding="utf-8") as f:
            leidos.append(list(json.load(f)))
    assert leidos == [["Codo sintetico viejo"], ["Codo sintetico nuevo"], ["Codo sintetico otro"]], \
        "se pisó un .migrado anterior"
    assert not os.path.exists(ruta)


def test_un_archivo_viejo_con_caracteres_que_la_base_no_guarda_los_saltea(client, duenos, caplog):
    """Un NUL (Postgres no lo guarda), medio par UTF-16 (ninguna base) o algo
    más largo que el tope de confirmar: esa entrada no se carga, las demás sí
    (también las del tope justo) y el archivo queda como `.migrado`."""
    a = duenos()
    # Escapados en el JSON (\u0000, \ud800), como los deja json.dumps por defecto.
    ruta = _archivo(a["username"], json.dumps({
        "Codo\x00sintetico": {"ncm": "7307.19.00", "count": 1},
        "Codo sintetico con NUL en la NCM": {"ncm": "7307.19.00\x00", "count": 1},
        "Codo\ud800sintetico": {"ncm": "7307.19.00", "count": 1},
        "C" * 2001: {"ncm": "7307.19.00", "count": 1},
        "Codo sintetico con NCM larga": {"ncm": "8" * 21, "count": 1},
        "D" * 2000: {"ncm": "8" * 20, "count": 1},
        "Codo sintetico": {"ncm": "7307.19.00", "count": 1},
    }))
    with caplog.at_level(logging.WARNING):
        _cargar_archivos()
    assert _filas(a["username"]) == [("D" * 2000, "8" * 20, 1), ("Codo sintetico", "7307.19.00", 1)]
    assert (f"ncm_historial_{a['username']}.json: 5 entradas más largas que el tope, con un carácter nulo"
            in caplog.text), caplog.text
    assert os.path.exists(ruta + ".migrado") and not os.path.exists(ruta)
