"""CLIENTE-1b: el script que informa las fechas de inicio ya guardadas que no
sirven, sobre una base sqlite temporal con la tabla real. Datos inventados."""
import sqlite3

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


def test_la_base_es_obligatoria(monkeypatch, capsys):
    """No se toma de DATABASE_URL: así no se corre contra una base sin nombrarla."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./no-usar.db")
    with pytest.raises(SystemExit):
        main([])


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
