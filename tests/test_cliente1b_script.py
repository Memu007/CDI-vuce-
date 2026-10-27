"""CLIENTE-1b: el script que informa las fechas de inicio ya guardadas que no
sirven, sobre una base sqlite temporal con la tabla real. Datos inventados."""
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from proyecto_maria.database.models import Client
from scripts.datos.clientes_fecha_inic_activ import main

# (id, fecha guardada); el nombre es para ver que el informe no lo muestra
FILAS = [
    ("id-none", "None"),
    ("id-none-espacios", " None "),
    ("id-anio-cortado", "20150-01-0"),
    ("id-imposible", "2015-02-30"),
    ("id-texto", "mar-2015"),
    ("id-iso", "2015-03-01"),
    ("id-barras", "01/03/2015"),
    ("id-vacia", ""),
    ("id-nula", None),
]


@pytest.fixture
def base(tmp_path):
    ruta = tmp_path / "clientes.db"
    engine = create_engine(f"sqlite:///{ruta}")
    Client.__table__.create(engine)
    engine.dispose()
    con = sqlite3.connect(ruta)
    con.executemany(
        "INSERT INTO clients (id, name, fecha_inic_activ) VALUES (?, ?, ?)",
        [(cid, f"Cliente Inventado {cid}", fecha) for cid, fecha in FILAS])
    con.commit()
    con.close()
    return ruta


def _fechas(ruta):
    con = sqlite3.connect(ruta)
    try:
        return dict(con.execute("SELECT id, fecha_inic_activ FROM clients"))
    finally:
        con.close()


def test_sin_la_opcion_informa_y_no_cambia_nada(base, capsys):
    antes = _fechas(base)
    assert main(["--base", f"sqlite+aiosqlite:///{base}"]) == 0
    salida = capsys.readouterr().out
    assert _fechas(base) == antes
    assert "Con «None»: 2\n  id-none\n  id-none-espacios\n" in salida
    assert ("Con una fecha que no sirve: 3\n  id-anio-cortado\n  id-imposible\n  id-texto\n"
            in salida)
    for cid in ("id-iso", "id-barras", "id-vacia", "id-nula"):
        assert cid not in salida
    assert "Cliente Inventado" not in salida and "mar-2015" not in salida
    assert "No se cambió nada" in salida


def test_con_la_opcion_deja_vacias_solo_las_none(base, capsys):
    antes = _fechas(base)
    assert main(["--base", f"sqlite+aiosqlite:///{base}", "--arreglar-none"]) == 0
    salida = capsys.readouterr().out
    despues = _fechas(base)
    assert despues["id-none"] == "" and despues["id-none-espacios"] == ""
    for cid, fecha in antes.items():
        if cid not in ("id-none", "id-none-espacios"):
            assert despues[cid] == fecha, cid
    assert "Quedaron vacías: 2" in salida


def test_la_base_es_obligatoria(base, monkeypatch, capsys):
    """No se toma de DATABASE_URL: así no se corre contra una base sin nombrarla.
    DATABASE_URL apunta a una base que existe, para que no frene por otra cosa."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{base}")
    with pytest.raises(SystemExit) as salida:
        main(["--arreglar-none"])
    assert salida.value.code == 2
    assert "--base" in capsys.readouterr().err
    assert _fechas(base)["id-none"] == "None"


def test_con_la_opcion_vacia_cada_none_que_informa(tmp_path, capsys):
    """La que se informa como «None» se vacía, con el espacio que sea: el
    informe y el arreglo usan el mismo criterio."""
    ruta = tmp_path / "clientes.db"
    engine = create_engine(f"sqlite:///{ruta}")
    Client.__table__.create(engine)
    engine.dispose()
    con = sqlite3.connect(ruta)
    con.executemany("INSERT INTO clients (id, name, fecha_inic_activ) VALUES (?, ?, ?)",
                    [("id-tab", "Cliente Inventado", "None\t"), ("id-salto", "Cliente Inventado", "\nNone")])
    con.commit()
    con.close()
    assert main(["--base", f"sqlite+aiosqlite:///{ruta}", "--arreglar-none"]) == 0
    salida = capsys.readouterr().out
    assert "Con «None»: 2" in salida
    assert _fechas(ruta) == {"id-tab": "", "id-salto": ""}
    assert "Quedaron vacías: 2" in salida


def test_acepta_la_url_sqlite_sin_driver(base, capsys):
    assert main(["--base", f"sqlite:///{base}"]) == 0
    assert "Con «None»: 2" in capsys.readouterr().out


def test_una_base_sqlite_que_no_existe_no_se_crea(tmp_path, capsys):
    """Una ruta mal escrita no deja una base vacía ni un traceback."""
    ruta = tmp_path / "no-existe.db"
    with pytest.raises(SystemExit) as salida:
        main(["--base", f"sqlite:///{ruta}"])
    assert salida.value.code == 2
    assert not ruta.exists()
    assert "no existe" in capsys.readouterr().err


# CLIENTE-1c: con un --base mal escrito o una base que no responde, el error
# no muestra la clave ni un traceback. Se corre como proceso, como lo corre
# una persona: así se ve también lo que imprimiría Python al caerse.
SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "datos" / "clientes_fecha_inic_activ.py"


def _correr(base):
    r = subprocess.run([sys.executable, str(SCRIPT), "--base", base],
                       capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


@pytest.mark.parametrize("base", [
    "postgresql//usuario:CLAVESECRETA@127.0.0.1/base",       # sin los dos puntos
    "usuario:CLAVESECRETA@127.0.0.1/base",                   # sin el esquema
    "postgresql://usuario:CLAVESECRETA@127.0.0.1:abc/base",  # puerto que no es número
], ids=["sin-dos-puntos", "sin-esquema", "puerto-texto"])
def test_un_base_mal_escrito_no_muestra_la_clave(base):
    rc, salida = _correr(base)
    assert rc == 2, salida
    assert "CLAVESECRETA" not in salida, salida
    assert "Traceback" not in salida, salida
    assert "--base" in salida, salida


def test_una_base_que_no_responde_no_muestra_la_clave():
    # El puerto 9 no escucha: la conexión se rechaza.
    rc, salida = _correr("postgresql://usuario:CLAVESECRETA@127.0.0.1:9/base")
    assert rc == 2, salida
    assert "CLAVESECRETA" not in salida, salida
    assert "Traceback" not in salida, salida
    assert "127.0.0.1:9" in salida, salida   # dice a cuál quiso entrar


@pytest.mark.parametrize("base", [
    "postgresql://usuario:CLAVE@SECRETA@127.0.0.1:9/base",       # «@» sin escapar en la clave
    "postgresql://usuario@127.0.0.1:9/base?password=CLAVESECRETA",  # la clave en la consulta
    "postgresql://usuario;CLAVESECRETA@127.0.0.1:9/base",        # «;» en vez de «:»
], ids=["arroba", "en-la-consulta", "punto-y-coma"])
def test_una_base_mal_armada_que_no_responde_no_muestra_la_clave(base):
    """SQLAlchemy no reconoce estas claves como clave: el error no puede
    repetir la URL tal como la entiende."""
    rc, salida = _correr(base)
    assert rc == 2, salida
    for pedazo in ("CLAVE", "SECRETA"):
        assert pedazo not in salida, salida
    assert "Traceback" not in salida, salida
    assert "127.0.0.1:9" in salida, salida


def test_una_clave_corta_no_tapa_el_nombre_de_la_base():
    rc, salida = _correr("postgresql://usuario:1@127.0.0.1:9/base")
    assert rc == 2, salida
    assert "127.0.0.1:9" in salida, salida


@pytest.mark.parametrize("clave", ["CLAVESECRETA", "Clave/Con Raros+1"], ids=["simple", "escapada"])
def test_si_el_error_de_la_base_nombra_la_clave_no_se_muestra(monkeypatch, capsys, clave):
    """Ningún driver de los que probamos pone la clave en su error, pero alguno
    podría repetir la URL: se tapa como venga, tal cual o escapada."""
    from urllib.parse import quote, quote_plus

    import scripts.datos.clientes_fecha_inic_activ as script

    async def _cae(url, arreglar_none):
        raise RuntimeError(f"no conecta: {clave} | {quote(clave, safe='')} | {quote_plus(clave)}")
    monkeypatch.setattr(script, "revisar", _cae)
    base = f"postgresql://usuario:{quote(clave, safe='')}@127.0.0.1:9/base"
    assert main(["--base", base]) == 2
    err = capsys.readouterr().err
    assert "no conecta" in err
    for forma in (clave, quote(clave, safe=""), quote_plus(clave)):
        assert forma not in err, err


@pytest.mark.parametrize("base", [
    "postgresql://usuario:CLAVE@SECRETA@127.0.0.1:9/base",
    "postgresql://usuario@127.0.0.1:9/base?password=CLAVESECRETA",
    "postgresql://usuario;CLAVESECRETA@127.0.0.1:9/base",
], ids=["arroba", "en-la-consulta", "punto-y-coma"])
def test_si_el_error_repite_una_base_mal_armada_no_se_ve_la_clave(monkeypatch, capsys, base):
    """El error repite la URL como se escribió y como la entiende SQLAlchemy
    (con «@» de más, el host le queda «SECRETA@127.0.0.1»)."""
    from sqlalchemy.engine import make_url

    import scripts.datos.clientes_fecha_inic_activ as script

    entendida = make_url(base)

    async def _cae(url, arreglar_none):
        raise RuntimeError(f"no conecta: {base} | {entendida.render_as_string(hide_password=False)}"
                           f" | host {entendida.host}")
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", base]) == 2
    err = capsys.readouterr().err
    assert "no conecta" in err
    for pedazo in ("CLAVE", "SECRETA"):
        assert pedazo not in err, err


def test_una_clave_corta_no_tapa_el_host_en_el_error(monkeypatch, capsys):
    import scripts.datos.clientes_fecha_inic_activ as script

    async def _cae(url, arreglar_none):
        raise RuntimeError("no conecta a 127.0.0.1")
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", "postgresql://usuario:1@127.0.0.1:9/base"]) == 2
    assert "no conecta a 127.0.0.1" in capsys.readouterr().err


# Vuelta de CLIENTE-1c (H1): el lugar y la clave salen de lo mismo que
# conecta (`make_url`), no de `urlsplit`. Con «/», «?», «#», «[» o un carácter
# de ancho completo en la clave, el error mostraba la clave o se caía con un
# traceback.
CLAVES_RARAS = ["CLA/VESECRETA", "CLA?VESECRETA", "CLA#VESECRETA", "CLA[VESECRETA",
                "CLA]VESECRETA", "CLA／VESECRETA", "CLA＠VESECRETA", "CLA？VESECRETA",
                "CLA＃VESECRETA", "CLA%2FVESECRETA", "CLA;VESECRETA", "CLA VESECRETA"]


@pytest.mark.parametrize("clave", CLAVES_RARAS)
def test_una_clave_con_un_separador_no_se_ve_en_el_error(clave):
    rc, salida = _correr(f"postgresql://usuario:{clave}@127.0.0.1:9/base")
    assert rc == 2, salida
    for pedazo in ("CLA", "VESECRETA"):
        assert pedazo not in salida, salida
    assert "Traceback" not in salida, salida
    assert "No se pudo revisar la base 127.0.0.1:9/base:" in salida, salida


@pytest.mark.parametrize("clave", CLAVES_RARAS + ["CLA@VESECRETA", "CLA@VE/SE@CRETA"])
def test_si_el_error_repite_la_url_una_clave_con_separador_no_se_ve(monkeypatch, capsys, clave):
    from sqlalchemy.engine import make_url

    import scripts.datos.clientes_fecha_inic_activ as script

    base = f"postgresql://usuario:{clave}@127.0.0.1:9/base"
    entendida = make_url(base)

    async def _cae(url, arreglar_none):
        raise RuntimeError(f"no conecta: {base} | {entendida.render_as_string(hide_password=False)}"
                           f" | host {entendida.host} | base {entendida.database} | clave {entendida.password}")
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", base]) == 2
    err = capsys.readouterr().err
    assert "no conecta" in err, err
    for pedazo in ("CLA", "VE", "SE", "CRETA"):
        assert pedazo not in err, err


def test_una_clave_que_hace_ilegible_la_url_tampoco_se_ve():
    """«:» después de un «@» de la clave: SQLAlchemy no la entiende y el
    script corta antes de conectar, sin mostrarla."""
    rc, salida = _correr("postgresql://usuario:CLA@VESE:CRETA@127.0.0.1:9/base")
    assert rc == 2, salida
    assert "--base" in salida, salida
    for pedazo in ("CLA", "VESE", "CRETA", "Traceback"):
        assert pedazo not in salida, salida


def test_lo_que_conecta_es_lo_que_se_lee(monkeypatch, capsys):
    """El motor recibe la misma URL que se usó para tapar la clave."""
    import scripts.datos.clientes_fecha_inic_activ as script

    vistas = []

    def _motor(url, *a, **k):
        vistas.append(url)
        raise RuntimeError("no conecta")
    monkeypatch.setattr(script, "create_async_engine", _motor)
    assert main(["--base", "postgresql://usuario:CLA/VESECRETA@127.0.0.1:9/base"]) == 2
    assert [(u.password, u.host, u.port, u.database) for u in vistas] == [
        ("CLA/VESECRETA", "127.0.0.1", 9, "base")]


# H2: lo que se tapa no rompe el resto del mensaje.
@pytest.mark.parametrize("usuario", ["u", "o", "Error", "Connection", "ed"])
def test_un_usuario_corto_no_rompe_el_mensaje(monkeypatch, capsys, usuario):
    import scripts.datos.clientes_fecha_inic_activ as script

    async def _cae(url, arreglar_none):
        raise ConnectionRefusedError(111, "Connect call failed ('127.0.0.1', 9)")
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", f"postgresql://{usuario}:CLAVESECRETA@127.0.0.1:9/base"]) == 2
    err = capsys.readouterr().err
    assert ("No se pudo revisar la base 127.0.0.1:9/base: ConnectionRefusedError: "
            "[Errno 111] Connect call failed ('127.0.0.1', 9)") in err, err


def test_el_usuario_suelto_en_el_error_se_tapa(monkeypatch, capsys):
    import scripts.datos.clientes_fecha_inic_activ as script

    async def _cae(url, arreglar_none):
        raise RuntimeError('password authentication failed for user "ulises"')
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", "postgresql://ulises:CLAVESECRETA@127.0.0.1:9/base"]) == 2
    err = capsys.readouterr().err
    assert 'failed for user "***"' in err, err


def test_una_clave_que_empieza_como_el_host_se_tapa_entera(monkeypatch, capsys):
    """El host queda visible, pero no protege lo que es parte de la clave."""
    import scripts.datos.clientes_fecha_inic_activ as script

    async def _cae(url, arreglar_none):
        raise RuntimeError(f"no conecta con clave {url.password} a {url.host}")
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", "postgresql://usuario:127.0.0.1CLAVE@127.0.0.1:9/base"]) == 2
    err = capsys.readouterr().err
    assert "CLAVE" not in err, err
    assert "no conecta con clave *** a 127.0.0.1" in err, err


def test_si_tapar_falla_no_hay_traceback_ni_clave(monkeypatch, capsys):
    import scripts.datos.clientes_fecha_inic_activ as script

    async def _cae(url, arreglar_none):
        raise RuntimeError(f"no conecta con clave {url.password}")

    def _rompe(*a, **k):
        raise ValueError("tapar se rompió")
    monkeypatch.setattr(script, "revisar", _cae)
    monkeypatch.setattr(script, "_tapar", _rompe)
    assert main(["--base", "postgresql://usuario:CLAVESECRETA@127.0.0.1:9/base"]) == 2
    err = capsys.readouterr().err
    assert "CLAVESECRETA" not in err and "Traceback" not in err, err
    assert "No se pudo revisar la base (sin detalle): RuntimeError" in err, err


# EXCEL-3f, H1-bis: SQLAlchemy escribe la clave con `quote(clave, safe=" +")`
# y esa forma no se tapaba si la clave mezclaba un espacio con otro carácter
# escapado. Se tapa cualquier forma escapada: con cualquier carácter tal cual o
# como %XX (en mayúscula o minúscula), «+» por el espacio, o escrita por Python
# o JSON (con las dos comillas, Python escribe «\'»).
def _formas_de(clave):
    from urllib.parse import quote, quote_plus

    return {
        "sqlalchemy": quote(clave, safe=" +"),
        "quote": quote(clave),
        "quote-vacio": quote(clave, safe=""),
        "quote_plus": quote_plus(clave),
        "minusculas": re.sub(r"%[0-9A-F]{2}", lambda m: m.group(0).lower(), quote(clave, safe="")),
        "repr": repr(clave),
        "ascii": ascii(clave),
        "json": json.dumps(clave),
    }


@pytest.mark.parametrize("clave", [
    "QZXW KJVB|NMPL", "QZXW KJVB%NMPL", "QZXW KJVB\"NMPL", "QZXW KJVB/NMPL",
    "QZXW+KJVB NMPL", "QZXW KJVB\\NMPL", "QZXW KJVBñNMPL", "QZXW\tKJVB NMPL",
    "QZXW 'KJVB\"NMPL",
], ids=["barra", "porcentaje", "comilla", "barra-comun", "mas", "contrabarra", "enie", "tab",
        "las-dos-comillas"])
@pytest.mark.parametrize("forma", list(_formas_de("x")))
def test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error(
        monkeypatch, capsys, clave, forma):
    from urllib.parse import quote

    from sqlalchemy.engine import make_url

    import scripts.datos.clientes_fecha_inic_activ as script

    base = f"postgresql://usuario:{quote(clave, safe='')}@db.local:9/base"
    assert make_url(base).password == clave

    async def _cae(url, arreglar_none):
        raise RuntimeError(f"no conecta: [{_formas_de(clave)[forma]}]")
    monkeypatch.setattr(script, "revisar", _cae)
    assert main(["--base", base]) == 2
    err = capsys.readouterr().err
    assert "No se pudo revisar la base db.local:9/base: RuntimeError: no conecta: [" in err, err
    for pedazo in ("QZXW", "KJVB", "NMPL"):
        assert pedazo not in err, err


def test_el_error_con_la_url_de_sqlalchemy_no_muestra_ninguna_clave_al_azar(monkeypatch, capsys):
    """Como el fuzz de la PM: claves al azar con separadores, espacios y letras
    de otros alfabetos, y el error repite la URL como la escribe SQLAlchemy y
    las otras formas. Ningún pedazo de la clave queda a la vista."""
    import random
    from urllib.parse import quote

    from sqlalchemy.engine import make_url

    import scripts.datos.clientes_fecha_inic_activ as script

    azar = random.Random(20261027)
    raros = " |%+/@:?#;[]\\\"'<>{}^`~!$&*()=,\tñé€／＠"
    letras = "ABCDEFGHJKLMNPQRSTVWXZ"
    fugas = []
    for _ in range(400):
        pedazos = ["".join(azar.choices(letras, k=4)) for _ in range(3)]
        clave = pedazos[0]
        for p in pedazos[1:]:
            clave += "".join(azar.choices(raros, k=azar.randint(1, 3))) + p
        base = f"postgresql://usuario:{quote(clave, safe='')}@db.local:9/base"
        entendida = make_url(base)
        assert entendida.password == clave

        async def _cae(url, arreglar_none, entendida=entendida, clave=clave):
            raise RuntimeError(f"no conecta: {entendida.render_as_string(hide_password=False)} | "
                               + " | ".join(_formas_de(clave).values()))
        monkeypatch.setattr(script, "revisar", _cae)
        assert main(["--base", base]) == 2
        err = capsys.readouterr().err
        if any(p in err for p in pedazos) or "db.local:9/base" not in err:
            fugas.append((clave, err))
    assert not fugas, f"{len(fugas)} de 400: {fugas[:3]}"


@pytest.mark.parametrize("visible", ["QZXW%20KJVB%7CNMPL", "QZXW KJVB%7cNMPL", "QZXW+KJVB|NMPL"],
                         ids=["quote", "minusculas", "mas"])
def test_un_pedazo_del_host_que_es_la_clave_escrita_de_otra_forma_se_tapa(visible):
    """Lo que se deja ver es el host, nunca la clave escapada aunque llegue
    como pedazo del host."""
    from scripts.datos.clientes_fecha_inic_activ import _tapar

    assert _tapar(f"host {visible} y db", {"QZXW KJVB|NMPL"}, {visible, "db"}) == "host *** y db"
