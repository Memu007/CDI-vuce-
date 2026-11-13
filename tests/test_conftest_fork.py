import os

from tests import conftest


def test_un_hijo_que_sale_no_borra_la_base_del_padre():
    ruta = os.environ["DATABASE_URL"].split("///", 1)[1]
    assert os.path.exists(ruta)
    pid = os.fork()
    if pid == 0:
        # Sólo el cierre del conftest: los demás atexit podrían borrar cosas del padre.
        try:
            conftest._borrar_db_de_prueba()
        finally:
            os._exit(0)
    os.waitpid(pid, 0)
    assert os.path.exists(ruta), "el hijo borró la base del padre"
