"""Dónde espera la subida normal de test_excel2 con ocho libros pesados delante.

No es parte de la suite (no empieza con test_): se corre a mano, solo.

    python -m pytest -q -s --no-cov -p no:cacheprovider tests/medir_excel2.py

- test_etapas: cuánto cuesta cada paso de validar y leer un libro, en solitario.
- test_linea_de_tiempo: el mismo escenario que
  test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal,
  con una línea por evento: segundos desde el arranque, qué pasó, de quién y
  en qué hilo. No afirma nada; sólo mide.
- test_hilos_contra_procesos: el paso más caro, cuatro veces a la vez, en
  hilos y en procesos.
"""
import asyncio
import io
import os
import tempfile
import threading
import time
import zipfile

from proyecto_maria import main
from proyecto_maria.security import file_security as fs
from tests.test_excel2 import FILAS, _libro_con, _libro_normal


def _libros():
    filas = 6000
    for _ in range(3):
        armado = _libro_con(filas_primera=filas)
        with zipfile.ZipFile(io.BytesIO(armado)) as z:
            tamano = z.getinfo("xl/worksheets/sheet1.xml").file_size
        if 9.5 * 2**20 < tamano < 10 * 2**20:
            break
        filas = int(filas * (9.8 * 2**20) / tamano)
    return armado, _libro_normal({"Factura": FILAS})


def _cronometro():
    inicio = time.perf_counter()
    return lambda: round(time.perf_counter() - inicio, 2)


def test_etapas():
    armado, normal = _libros()
    for nombre, libro in (("pesada", armado), ("normal", normal)):
        t = {}
        reloj = _cronometro(); fs._excel_descomprimido_bytes(libro); t["indice"] = reloj()
        with zipfile.ZipFile(io.BytesIO(libro)) as z:
            reloj = _cronometro(); fs._sin_dtd(z); t["sin_dtd"] = reloj()
            reloj = _cronometro(); hojas = fs.hojas_del_xlsx(z); fs.partes_del_xlsx(z); t["partes"] = reloj()
            reloj = _cronometro(); xml = z.read(hojas[0][1]); t["leer_hoja"] = reloj()
            reloj = _cronometro(); fs._ultima_columna(xml); t["ultima_columna"] = reloj()
        reloj = _cronometro(); fs._abrir_excel(libro, ".xlsx"); t["TOTAL_validar"] = reloj()
        print(nombre, t)
    fd, ruta = tempfile.mkstemp(suffix=".xlsx")
    os.write(fd, armado)
    os.close(fd)
    try:
        reloj = _cronometro()
        try:
            main._leer_excel_ruta(ruta, "openpyxl", ())
        except Exception as e:  # la pesada pasa de 5000 filas: da 400
            print("  (leer:", str(e)[:70], ")")
        print("pesada leer_excel_ruta", reloj())
        reloj = _cronometro(); main._otras_hojas_con_datos(ruta, "openpyxl"); print("pesada otras_hojas", reloj())
    finally:
        os.unlink(ruta)


def test_linea_de_tiempo(monkeypatch):
    import httpx

    armado, normal = _libros()
    reloj = _cronometro()
    log = []
    candado = threading.Lock()

    def marca(que, quien):
        with candado:
            log.append((reloj(), que, quien, threading.current_thread().name))

    def medido(nombre_func, func, quien):
        def envuelta(*a, **k):
            q = quien(*a)
            marca(f"{nombre_func}:empieza", q)
            try:
                return func(*a, **k)
            finally:
                marca(f"{nombre_func}:termina", q)
        return envuelta

    monkeypatch.setattr(fs, "_abrir_excel", medido(
        "validar", fs._abrir_excel, lambda c, *_: "normal" if c == normal else "pesada"))
    monkeypatch.setattr(main, "_leer_excel_ruta", medido("leer", main._leer_excel_ruta, lambda *_: "?"))
    monkeypatch.setattr(main, "_otras_hojas_con_datos", medido("otras", main._otras_hojas_con_datos, lambda *_: "?"))

    async def _todo():
        entradas = 0
        listas = asyncio.Event()
        validar = fs.validate_file_upload

        async def observar(file, *a, **k):
            nonlocal entradas
            marca("entra_al_validador", file.filename)
            if file.filename == "pesada.xlsx":
                entradas += 1
                if entradas == 8:
                    listas.set()
            return await validar(file, *a, **k)
        monkeypatch.setattr(fs, "validate_file_upload", observar)

        transporte = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test", timeout=600) as c:
            async def subir(contenido, nombre, quien):
                r = await c.post("/upload_excel_v2/", files={"file": (nombre, contenido)})
                marca(f"respuesta {r.status_code}", quien)
            pesadas = [asyncio.create_task(subir(armado, "pesada.xlsx", f"pesada (pedido {i})")) for i in range(8)]
            await asyncio.wait_for(listas.wait(), 10)
            marca("sube", "normal")
            await subir(normal, "normal.xlsx", "normal")
            await asyncio.gather(*pesadas)

    asyncio.run(_todo())
    # Un hilo vencido sigue trabajando: se lo espera para que la línea lo muestre.
    for pool in (fs._POOL_VALIDAR_EXCEL, main._POOL_LECTURA_EXCEL):
        if pool is not None:
            pool.submit(lambda: None).result()
            pool.shutdown(wait=True)
    fs._POOL_VALIDAR_EXCEL = None
    main._POOL_LECTURA_EXCEL = None
    for fila in log:
        print(*fila, sep="\t")


def test_hilos_contra_procesos():
    """El costo dominante (_ultima_columna) cuatro veces a la vez: en hilos
    comparten el GIL; en procesos usan un núcleo cada uno."""
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

    armado, _ = _libros()
    with zipfile.ZipFile(io.BytesIO(armado)) as z:
        xml = z.read(fs.hojas_del_xlsx(z)[0][1])
    reloj = _cronometro(); fs._ultima_columna(xml); uno = reloj()
    with ThreadPoolExecutor(4) as p:
        reloj = _cronometro(); list(p.map(fs._ultima_columna, [xml] * 4)); hilos = reloj()
    with ProcessPoolExecutor(4) as p:
        list(p.map(len, [b""] * 4))  # que los procesos ya estén levantados
        reloj = _cronometro(); list(p.map(fs._ultima_columna, [xml] * 4)); procesos = reloj()
    print(f"núcleos: {os.cpu_count()}; una: {uno} s; cuatro en hilos: {hilos} s; cuatro en procesos: {procesos} s")
