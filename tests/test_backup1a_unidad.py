"""BACKUP-1a, lo que no necesita Postgres (corre también en la CI): los
errores no muestran la clave de ninguna de las dos direcciones, una copia no
pisa un archivo, el envío no deja una copia distinta y una huella que no se
entiende no llega a la base de prueba."""
import asyncio
import hashlib
import json
import secrets
from urllib.parse import quote

import pytest

from scripts.datos import copia_base

HOST = "127.0.0.1"


def _clave() -> str:
    return secrets.token_hex(4) + " :@%/;ñ"


def _formas(clave: str) -> list:
    return [clave, quote(clave, safe=""), quote(clave), quote(clave, safe=" +").replace(" ", "+")]


@pytest.mark.parametrize("variable", copia_base.VARIABLES)
@pytest.mark.parametrize("como", ["escapada", "sin_escapar", "en_la_consulta"])
def test_tapar_no_deja_la_clave_y_deja_el_host(monkeypatch, variable, como):
    clave = _clave()
    url = {
        "escapada": f"postgresql://cdi:{quote(clave, safe='')}@{HOST}:5432/postgres",
        "sin_escapar": f"postgresql://cdi:{clave}@{HOST}:5432/postgres",
        "en_la_consulta": f"postgresql://cdi@{HOST}:5432/postgres?password={quote(clave, safe='')}",
    }[como]
    for v in copia_base.VARIABLES:
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv(variable, url)

    for forma in _formas(clave):
        texto = f"no conecta a {HOST}:5432 con «{forma}» (ConnectionRefusedError)"
        tapado = copia_base.tapar(texto)
        assert forma not in tapado, f"queda la clave escrita como {forma!r}"
        assert HOST in tapado and "ConnectionRefusedError" in tapado, tapado


def test_tapar_sin_direcciones_no_cambia_el_texto(monkeypatch):
    for v in copia_base.VARIABLES:
        monkeypatch.delenv(v, raising=False)
    assert copia_base.tapar("pg_restore: error 127.0.0.1") == "pg_restore: error 127.0.0.1"


# ── Archivos ─────────────────────────────────────────────────────────────────

def test_fijar_no_pisa_un_archivo_que_aparecio(tmp_path):
    """El chequeo de antes de copiar o enviar no alcanza si otro proceso deja
    un archivo con ese nombre mientras tanto."""
    temporal, ruta = tmp_path / "copia.parcial", tmp_path / "copia.dump"
    temporal.write_bytes(b"nueva")
    ruta.write_bytes(b"anterior")
    with pytest.raises(copia_base.Falla, match="ya existe"):
        copia_base._fijar(str(temporal), str(ruta))
    assert ruta.read_bytes() == b"anterior"
    assert not temporal.exists()


def _copia_verificada(carpeta):
    archivo = carpeta / "copia.dump"
    archivo.write_bytes(b"PGDMP" + secrets.token_bytes(64))
    huella = {"formato": copia_base.FORMATO, "codificacion": "UTF8",
              "tablas": {"public.x": {"filas": 3, "sha256": "0"}}}
    (carpeta / "copia.dump.huella.json").write_text(json.dumps(huella))
    suma = hashlib.sha256(archivo.read_bytes()).hexdigest()
    (carpeta / "copia.dump.sha256").write_text(f"{suma}  copia.dump\n")
    return archivo


def test_enviar_no_deja_una_copia_que_llego_distinta(monkeypatch, tmp_path):
    archivo = _copia_verificada(tmp_path)
    destino = tmp_path / "destino"
    destino.mkdir()
    monkeypatch.setenv("COPIA_DESTINO", str(destino))
    monkeypatch.setattr(copia_base.shutil, "copyfile",
                        lambda origen, final: open(final, "wb").write(b"a medias"))
    with pytest.raises(copia_base.Falla, match="la copia llegó distinta"):
        asyncio.run(copia_base.enviar(str(archivo)))
    assert list(destino.iterdir()) == []


def test_enviar_no_lleva_una_copia_sin_su_huella(monkeypatch, tmp_path):
    archivo = _copia_verificada(tmp_path)
    (tmp_path / "copia.dump.huella.json").unlink()
    destino = tmp_path / "destino"
    destino.mkdir()
    monkeypatch.setenv("COPIA_DESTINO", str(destino))
    with pytest.raises(copia_base.Falla, match="falta la huella"):
        asyncio.run(copia_base.enviar(str(archivo)))
    assert list(destino.iterdir()) == []


@pytest.mark.parametrize("huella", [
    {"codificacion": "UTF8' LOCALE 'C' TEMPLATE template1 --"},
    {"formato": "otro"},
    {"tablas": {"public.x": {"filas": "3", "sha256": "0"}}},
])
def test_una_huella_que_no_se_entiende_no_llega_a_la_base(monkeypatch, tmp_path, huella):
    """Sin COPIA_PRUEBA_URL: si la huella pasara, el error sería otro."""
    archivo = _copia_verificada(tmp_path)
    ruta = tmp_path / "copia.dump.huella.json"
    ruta.write_text(json.dumps({**json.loads(ruta.read_text()), **huella}))
    for v in copia_base.VARIABLES:
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(copia_base.Falla, match="no se entiende"):
        asyncio.run(copia_base.verificar(str(archivo)))
    assert not (tmp_path / "copia.dump.sha256").exists()


@pytest.mark.parametrize("tablas", [{}, {"public.x": {"filas": 0, "sha256": "0"}}])
def test_una_huella_sin_filas_no_llega_a_la_base(monkeypatch, tmp_path, tablas):
    archivo = _copia_verificada(tmp_path)
    ruta = tmp_path / "copia.dump.huella.json"
    ruta.write_text(json.dumps({**json.loads(ruta.read_text()), "tablas": tablas}))
    for v in copia_base.VARIABLES:
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(copia_base.Falla, match=f"la copia está vacía: {len(tablas)} tablas, 0 filas"):
        asyncio.run(copia_base.verificar(str(archivo)))


class _Admin:
    """Una conexión cuyo DROP termina cuando la prueba lo suelta."""
    def __init__(self):
        self.empezo, self.soltar, self.hecho = asyncio.Event(), asyncio.Event(), []

    async def execute(self, sql):
        self.empezo.set()
        await self.soltar.wait()
        self.hecho.append(sql)

    async def close(self):
        self.hecho.append("close")

    def is_closed(self):
        return "close" in self.hecho or "terminate" in self.hecho

    def terminate(self):
        self.hecho.append("terminate")


def test_un_corte_durante_el_borrado_no_lo_deja_a_medias():
    async def principal():
        admin = _Admin()
        tarea = asyncio.ensure_future(copia_base._borrar_restauracion(admin, "cdi_restauracion_x"))
        await admin.empezo.wait()
        tarea.cancel()
        await asyncio.sleep(0)  # el corte le llega mientras borra
        admin.soltar.set()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        return admin.hecho
    assert asyncio.run(principal()) == ['DROP DATABASE IF EXISTS "cdi_restauracion_x" WITH (FORCE)', "close"]


def test_un_borrado_colgado_tiene_tope(monkeypatch):
    monkeypatch.setattr(copia_base, "TOPE_BORRADO_S", 0.2)
    admin = _Admin()
    with pytest.raises(copia_base.Falla, match="no se pudo borrar cdi_restauracion_x en 0.2 s"):
        asyncio.run(copia_base._borrar_restauracion(admin, "cdi_restauracion_x"))
    assert admin.hecho == ["terminate"]
