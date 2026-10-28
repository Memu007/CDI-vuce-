"""EXCEL-2b (D4 a): el carril liviano.

Un libro chico valida y se lee en hilos propios y no espera detrás de las
subidas pesadas. Qué es «chico» se mide una sola vez, desde los bytes subidos:
un .xlsx, por lo que su índice declara descomprimido sin contar las imágenes
(reconocidas por su firma, no por su nombre); un .xls, por su tamaño. El libro
no puede burlar esa medida: ante cualquier duda va al carril pesado.
"""
import io
import struct
import threading
import zipfile
import zlib

import pytest

from proyecto_maria import main
from proyecto_maria.security import file_security as fs
from tests.test_excel2 import _libro_con, _subir
from tests.test_maria1b_devolucion import FILAS, _libro_normal

PNG = b"\x89PNG\r\n\x1a\n"


def _normal():
    return _libro_normal({"Factura": FILAS})


def _xml_de_3_mib():
    """Un libro con 3 MiB de XML en la primera hoja: más que el umbral de 2."""
    libro = _libro_con(filas_primera=2100)
    with zipfile.ZipFile(io.BytesIO(libro)) as z:
        assert z.getinfo("xl/worksheets/sheet1.xml").file_size > 3 * 2**20
    return libro


def _con_entradas(libro, *extra):
    origen = zipfile.ZipFile(io.BytesIO(libro))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for info in origen.infolist():
            z.writestr(info.filename, origen.read(info))
        for nombre, datos in extra:
            z.writestr(nombre, datos)
    return buf.getvalue()


def _hoja_de(libro):
    with zipfile.ZipFile(io.BytesIO(libro)) as z:
        return z.read("xl/worksheets/sheet1.xml")


# ------------------------------------------------------------ la medida

def test_un_libro_normal_va_al_carril_liviano():
    assert fs._excel_liviano(_normal(), ".xlsx") is True


def test_un_libro_con_mas_xml_que_el_umbral_va_al_pesado():
    assert fs._excel_liviano(_xml_de_3_mib(), ".xlsx") is False


def test_una_hoja_con_nombre_de_imagen_cuenta_como_xml():
    """3 MiB de XML guardados como xl/media/image1.png: el nombre no lo
    descuenta, porque no empieza con la firma de una imagen."""
    libro = _con_entradas(_normal(), ("xl/media/image1.png", _hoja_de(_xml_de_3_mib())))
    assert fs._excel_liviano(libro, ".xlsx") is False


def test_una_imagen_de_verdad_no_cuenta():
    """Un logo de 3 MiB no manda una factura chica al carril pesado."""
    libro = _con_entradas(_normal(), ("xl/media/image1.png", PNG + bytes(3 * 2**20)))
    assert fs._excel_liviano(libro, ".xlsx") is True


def test_mas_de_10_mib_de_imagen_no_se_descuentan():
    """Una imagen se vuelve a comprimir al leer (_xlsx_solo_primera_hoja):
    descontar más de 10 MiB dejaría trabajo pesado en el carril liviano."""
    libro = _con_entradas(_normal(), ("xl/media/image1.png", PNG + bytes(12 * 2**20)))
    assert len(libro) < 10 * 2**20
    assert fs._excel_liviano(libro, ".xlsx") is False


def test_no_se_leen_mas_de_20_cabezas_de_imagen():
    """Cada cabeza de imagen se descomprime en el hilo del servidor: con 40
    imágenes, a las 20 lecturas se corta y el libro va al pesado aunque
    descontándolas todas entraría."""
    normal = _normal()
    imagenes = [(f"xl/media/image{i}.png", PNG + bytes(110 * 1024)) for i in range(40)]
    libro = _con_entradas(normal, *imagenes)
    with zipfile.ZipFile(io.BytesIO(libro)) as z:
        xml = sum(i.file_size for i in z.infolist() if not i.filename.startswith("xl/media/"))
    tam = len(imagenes[0][1])
    assert xml + 20 * tam > 2 * 2**20  # con 20 descontadas, no entra
    assert xml + 2 * tam <= 2 * 2**20  # descontando casi todas, entraría
    assert fs._excel_liviano(libro, ".xlsx") is False


def test_una_imagen_guardada_sin_comprimir_tampoco_cuenta():
    libro = _con_entradas(_normal())
    buf = io.BytesIO(libro)
    with zipfile.ZipFile(buf, "a") as z:
        z.writestr("xl/media/image1.png", PNG + bytes(3 * 2**20), compress_type=zipfile.ZIP_STORED)
    assert fs._excel_liviano(buf.getvalue(), ".xlsx") is True


def _bloques_vacios(k):
    """k entradas DEFLATE hechas sólo de bloques vacíos, 9,5 MiB en total:
    no dan un byte hasta el final, así que sacarles la cabeza con zipfile
    obliga a descomprimirlas enteras. Cada una declara 2,5 MiB."""
    vacio = bytes([2, 8, 32, 128, 0])  # cuatro bloques fijos vacíos, 10 bits cada uno
    crudo = vacio * (int(9.5 * 2**20) // k // len(vacio))
    assert zlib.decompressobj(-15).decompress(crudo) == b""  # ni un byte de cabeza
    buf = io.BytesIO(_con_entradas(_normal()))
    with zipfile.ZipFile(buf, "a") as z:
        for i in range(k):
            z.writestr(f"xl/media/x{i}.bin", crudo, compress_type=zipfile.ZIP_STORED)
    b = bytearray(buf.getvalue())
    i = b.find(b"PK\x01\x02")
    while i >= 0:
        largo = struct.unpack_from("<H", b, i + 28)[0]
        if bytes(b[i + 46:i + 46 + largo]).startswith(b"xl/media/x"):
            local = struct.unpack_from("<I", b, i + 42)[0]
            for metodo, tamano in ((i + 10, i + 24), (local + 8, local + 22)):
                struct.pack_into("<H", b, metodo, zipfile.ZIP_DEFLATED)
                struct.pack_into("<I", b, tamano, int(2.5 * 2**20))
        i = b.find(b"PK\x01\x02", i + 4)
    return bytes(b)


def test_las_cabezas_de_imagen_no_descomprimen_la_entrada_entera(monkeypatch):
    """La medida corre en el hilo del servidor: por cada candidata se mira
    una porción acotada de lo comprimido, no la entrada entera."""
    libro = _bloques_vacios(20)
    assert len(libro) < 10 * 2**20
    with zipfile.ZipFile(io.BytesIO(libro)) as z:
        info = z.getinfo("xl/media/x0.bin")
        assert info.compress_type == zipfile.ZIP_DEFLATED and info.compress_size > 400_000
    entrada = []
    real_obj, real_dec = zlib.decompressobj, zlib.decompress

    class Contado:
        def __init__(self, *a, **k):
            self._d = real_obj(*a, **k)

        def decompress(self, datos, *a, **k):
            entrada.append(len(datos))
            return self._d.decompress(datos, *a, **k)

        def __getattr__(self, nombre):
            return getattr(self._d, nombre)

    def contado(datos, *a, **k):
        entrada.append(len(datos))
        return real_dec(datos, *a, **k)
    monkeypatch.setattr(zlib, "decompressobj", Contado)
    monkeypatch.setattr(zlib, "decompress", contado)
    assert fs._excel_liviano(libro, ".xlsx") is False
    assert sum(entrada) <= 2**20, f"se descomprimieron {sum(entrada)} bytes en el hilo del servidor"


def _indice_largo():
    """Un libro chico con 2000 entradas vacías: su índice pasa de 128 KiB."""
    libro = _con_entradas(_normal(), *[(f"xl/x/{i:060d}.txt", b"") for i in range(2000)])
    fin = libro.rfind(b"PK\x05\x06")
    assert int.from_bytes(libro[fin + 12:fin + 16], "little") > 128 * 1024
    return libro


def test_un_indice_largo_va_al_pesado_sin_leerlo(monkeypatch):
    """La medida corre en el hilo del servidor: un índice largo no se lee ahí."""
    libro = _indice_largo()
    leidos = []
    # Abrir el ZipFile ya lee el índice entero: se espía eso, no infolist().
    original = zipfile.ZipFile._RealGetContents
    monkeypatch.setattr(zipfile.ZipFile, "_RealGetContents",
                        lambda self: leidos.append(1) or original(self))
    assert fs._excel_liviano(libro, ".xlsx") is False
    assert leidos == [], "el índice largo se leyó en el hilo del servidor"


def test_un_zip64_que_declara_un_indice_corto_va_al_pesado():
    """El fin de índice clásico dice 100 bytes y el de zip64, el índice real:
    zipfile usa el de zip64, así que el tope no se mide sobre el clásico."""
    libro = _indice_largo()
    fin = libro.rfind(b"PK\x05\x06")
    _, _, _, en_disco, total, tamano, inicio, _ = struct.unpack("<4sHHHHIIH", libro[fin:fin + 22])
    eocd64 = struct.pack("<4sQHHIIQQQQ", b"PK\x06\x06", 44, 45, 45, 0, 0, total, total, tamano, inicio)
    localizador = struct.pack("<4sIQI", b"PK\x06\x07", 0, fin, 1)
    clasico = struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, en_disco, total, 100, inicio, 0)
    forjado = libro[:fin] + eocd64 + localizador + clasico
    assert len(zipfile.ZipFile(io.BytesIO(forjado)).infolist()) == total  # zipfile lo abre
    assert fs._excel_liviano(forjado, ".xlsx") is False


def test_lo_que_no_es_un_zip_va_al_pesado():
    assert fs._excel_liviano(b"no es un zip", ".xlsx") is False


def test_un_xls_se_mide_por_su_tamano():
    assert fs._excel_liviano(b"x" * 2**20, ".xls") is True
    assert fs._excel_liviano(b"x" * (3 * 2**20), ".xls") is False


def test_el_umbral_sale_de_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("EXCEL_LIVIANO_MB", "5")
    assert fs._excel_liviano(_xml_de_3_mib(), ".xlsx") is True
    monkeypatch.setenv("EXCEL_LIVIANO_MB", "0.001")
    assert fs._excel_liviano(_normal(), ".xlsx") is False


def _mentir(libro, nombre, declarado):
    """El índice, central y local, dice que `nombre` ocupa `declarado` bytes,
    con el CRC de esos primeros bytes."""
    real = zipfile.ZipFile(io.BytesIO(libro)).read(nombre)
    crc = zlib.crc32(real[:declarado])
    b = bytearray(libro)
    i = b.find(b"PK\x01\x02")
    while i >= 0:
        largo = struct.unpack_from("<H", b, i + 28)[0]
        if bytes(b[i + 46:i + 46 + largo]) == nombre.encode():
            struct.pack_into("<I", b, i + 16, crc)
            struct.pack_into("<I", b, i + 24, declarado)
            local = struct.unpack_from("<I", b, i + 42)[0]
            struct.pack_into("<I", b, local + 14, crc)
            struct.pack_into("<I", b, local + 22, declarado)
        i = b.find(b"PK\x01\x02", i + 4)
    return bytes(b)


def test_un_libro_que_dice_ser_chico_no_entrega_mas_de_lo_que_dice():
    """3 MiB de hoja con un índice que declara 50 000 bytes: la medida le cree
    al índice, pero nadie lee más que eso, porque zipfile corta en el tamaño
    declarado. En el carril liviano no entra el trabajo de los 3 MiB."""
    libro = _mentir(_xml_de_3_mib(), "xl/worksheets/sheet1.xml", 50_000)
    assert fs._excel_liviano(libro, ".xlsx") is True
    with zipfile.ZipFile(io.BytesIO(libro)) as z:
        assert len(z.read("xl/worksheets/sheet1.xml")) == 50_000
        with z.open("xl/worksheets/sheet1.xml") as f:
            assert len(f.read()) == 50_000


# ------------------------------------------------- de punta a punta: los hilos

@pytest.fixture
def hilos(monkeypatch):
    """En qué hilo valida y en cuál lee cada subida."""
    vistos = []

    def espiar(lista, que, funcion):
        def envuelta(*a, **k):
            lista.append((que, threading.current_thread().name))
            return funcion(*a, **k)
        return envuelta
    monkeypatch.setattr(fs, "_abrir_excel", espiar(vistos, "validar", fs._abrir_excel))
    monkeypatch.setattr(main, "_leer_excel_ruta", espiar(vistos, "leer", main._leer_excel_ruta))
    return vistos


def test_la_subida_chica_valida_y_lee_en_los_hilos_livianos(hilos):
    r = _subir(_normal())
    assert r.status_code == 200, r.text[:300]
    assert [q for q, _ in hilos] == ["validar", "leer"], hilos
    assert hilos[0][1].startswith("validar-excel-liviano"), hilos
    assert hilos[1][1].startswith("lectura-excel-liviano"), hilos


def test_la_subida_grande_valida_y_lee_en_los_hilos_pesados(hilos):
    _subir(_xml_de_3_mib())
    assert [q for q, _ in hilos] == ["validar", "leer"], hilos
    assert hilos[0][1].startswith("validar-excel_"), hilos
    assert hilos[1][1].startswith("lectura-excel_"), hilos


def test_el_libro_que_dice_ser_chico_se_rechaza_rapido_en_el_carril_liviano(hilos):
    """De punta a punta: lo que entra al carril liviano son los 50 000 bytes
    declarados, no los 3 MiB; el XML cortado da 400 y no se lee."""
    libro = _mentir(_xml_de_3_mib(), "xl/worksheets/sheet1.xml", 50_000)
    r = _subir(libro)
    assert r.status_code == 400, r.text[:300]
    assert "column 49999" in r.text, r.text[:300]
    assert hilos == [("validar", hilos[0][1])] and hilos[0][1].startswith("validar-excel-liviano"), hilos


@pytest.fixture
def hilos_de_lectura(monkeypatch):
    """En qué hilo corre cada paso de la lectura: la hoja, las otras hojas y
    los ítems (devolución de EXCEL-2b, punto 2)."""
    vistos = {}

    def espiar(que, funcion):
        def envuelta(*a, **k):
            vistos.setdefault(que, threading.current_thread().name)
            return funcion(*a, **k)
        return envuelta
    for que in ("_leer_excel_ruta", "_otras_hojas_con_datos", "extract_items_from_excel"):
        monkeypatch.setattr(main, que, espiar(que, getattr(main, que)))
    return vistos


PASOS = ["_leer_excel_ruta", "_otras_hojas_con_datos", "extract_items_from_excel"]


def test_la_subida_chica_lee_las_otras_hojas_y_los_items_en_los_hilos_livianos(hilos_de_lectura):
    r = _subir(_normal())
    assert r.status_code == 200, r.text[:300]
    assert sorted(hilos_de_lectura) == sorted(PASOS), hilos_de_lectura
    for paso in PASOS:
        assert hilos_de_lectura[paso].startswith("lectura-excel-liviano_"), (paso, hilos_de_lectura)


def test_la_subida_grande_lee_las_otras_hojas_y_los_items_en_los_hilos_pesados(hilos_de_lectura, monkeypatch):
    # El mismo libro, medido grande: llega hasta los ítems por el carril pesado.
    monkeypatch.setenv("EXCEL_LIVIANO_MB", "0.001")
    r = _subir(_normal())
    assert r.status_code == 200, r.text[:300]
    assert sorted(hilos_de_lectura) == sorted(PASOS), hilos_de_lectura
    for paso in PASOS:
        assert hilos_de_lectura[paso].startswith("lectura-excel_"), (paso, hilos_de_lectura)


def test_un_indice_que_no_se_puede_leer_va_al_pesado():
    """Pasa el control del fin de índice, pero zipfile no lo puede leer: ante
    la duda, carril pesado (punto 4 de la devolución)."""
    libro = bytearray(_normal())
    i = libro.find(b"PK\x01\x02")
    libro[i:i + 4] = b"XX\x01\x02"
    with pytest.raises(zipfile.BadZipFile):
        zipfile.ZipFile(io.BytesIO(bytes(libro)))
    assert fs._excel_liviano(bytes(libro), ".xlsx") is False


@pytest.mark.parametrize("valor, bytes_", [("1e308", 2 * 2**20), ("1e300", int(1e300 * 2**20))])
def test_un_umbral_enorme_no_rompe_la_subida(monkeypatch, valor, bytes_):
    """EXCEL_LIVIANO_MB=1e308 daba 500 en toda subida de Excel: en bytes no
    entra en un entero. Un valor así vale lo que vale mal escrito, el de
    defecto (punto 4 de la devolución)."""
    monkeypatch.setenv("EXCEL_LIVIANO_MB", valor)
    assert fs._mb_de_entorno("EXCEL_LIVIANO_MB", 2) == bytes_
    r = _subir(_normal())
    assert r.status_code == 200, r.text[:300]


@pytest.mark.parametrize("variable", ["EXCEL_LIVIANO_MB", "EXCEL_MAX_TEXTOS_MB",
                                      "EXCEL_MAX_PRIMERA_HOJA_MB", "EXCEL_MAX_DESCOMPRIMIDO_MB"])
def test_ningun_tope_de_excel_enorme_rompe_la_subida(monkeypatch, variable):
    """Los cuatro topes de Excel en MB: 1e308 no entra en bytes y vale el de
    defecto. EXCEL_MAX_DESCOMPRIMIDO_MB tenía su propia lectura y daba 400
    «cannot convert float infinity to integer» (adversario Sonnet alto)."""
    monkeypatch.setenv(variable, "1e308")
    r = _subir(_normal())
    assert r.status_code == 200, r.text[:300]


# Todo tope que lee la subida de Excel desde el entorno usa el de defecto si
# el valor no es finito, si no es positivo o si en bytes o elementos da 0
# (devolución de EXCEL-2b, 28/10 19:20, punto 1): con tope 0 no entra ningún
# Excel. Medio MB sí es un tope (512 KB); medio elemento, no.
_LECTORES = {
    "EXCEL_LIVIANO_MB": (lambda: fs._mb_de_entorno("EXCEL_LIVIANO_MB", 2), 2 * 2**20),
    "EXCEL_MAX_TEXTOS_MB": (lambda: fs._mb_de_entorno("EXCEL_MAX_TEXTOS_MB", 10), 10 * 2**20),
    "EXCEL_MAX_PRIMERA_HOJA_MB": (lambda: fs._mb_de_entorno("EXCEL_MAX_PRIMERA_HOJA_MB", 10), 10 * 2**20),
    "EXCEL_MAX_DESCOMPRIMIDO_MB": (fs._excel_max_descomprimido_bytes, 100 * 2**20),
    "EXCEL_MAX_ELEMENTOS_ESTILOS": (fs._elementos_de_entorno, 500_000),
    "MAX_UPLOAD_MB": (main._get_max_upload_bytes, 10 * 2**20),
}


@pytest.mark.parametrize("valor", ["1e-9", "0.5", "inf", "nan", "-0", "0", "-3"])
@pytest.mark.parametrize("variable", list(_LECTORES))
def test_un_tope_que_no_sirve_vale_el_de_defecto(monkeypatch, variable, valor):
    leer, defecto = _LECTORES[variable]
    monkeypatch.setenv(variable, valor)
    if valor == "0.5" and variable.endswith("_MB"):
        esperado = 2**19
    else:
        esperado = defecto
    try:
        obtenido = leer()
    except (OverflowError, ValueError) as e:
        pytest.fail(f"{variable}={valor} rompe la lectura del tope: {e!r}")
    assert obtenido == esperado, f"{variable}={valor} da un tope de {obtenido}, no {esperado}"


@pytest.mark.parametrize("valor", ["1e-9", "inf", "nan", "-0"])
@pytest.mark.parametrize("variable", list(_LECTORES))
def test_un_tope_que_no_sirve_no_traba_la_subida(monkeypatch, variable, valor):
    monkeypatch.setenv(variable, valor)
    r = _subir(_normal())
    assert r.status_code == 200, f"{variable}={valor}: {r.status_code} {r.text[:300]}"


def test_se_leen_exactamente_20_cabezas_de_imagen(monkeypatch):
    """El tope de lecturas es 20, no «alguno»: con 40 candidatas se miran 20
    cabezas, ni una más ni una menos."""
    leidas = []
    original = fs._cabeza_de

    def _contar(contents, info):
        leidas.append(info.filename)
        return original(contents, info)
    monkeypatch.setattr(fs, "_cabeza_de", _contar)
    imagenes = [(f"xl/media/image{i}.png", PNG + bytes(110 * 1024)) for i in range(40)]
    assert fs._excel_liviano(_con_entradas(_normal(), *imagenes), ".xlsx") is False
    assert len(leidas) == 20, len(leidas)


def test_una_entrada_que_no_se_puede_descomprimir_no_corta_la_medida():
    """Una entrada con el DEFLATE roto no es imagen y sigue contando, pero no
    impide descontar la imagen buena que viene después."""
    corrupta = "xl/media/image2.png"
    libro = bytearray(_con_entradas(_normal(), (corrupta, bytes(int(1.2 * 2**20))),
                                    ("xl/media/image1.png", PNG + bytes(2**20))))
    with zipfile.ZipFile(io.BytesIO(bytes(libro))) as z:
        info = z.getinfo(corrupta)
        xml = sum(i.file_size for i in z.infolist() if not i.filename.startswith("xl/media/"))
        imagen = z.getinfo("xl/media/image1.png").file_size
    inicio = info.header_offset + 30 + len(corrupta.encode())
    libro[inicio] = 0x06  # bloque de tipo 3: no existe
    with pytest.raises(zlib.error):
        zlib.decompressobj(-15).decompress(bytes(libro[inicio:inicio + 16]), 44)
    assert info.file_size > imagen  # se mira antes que la imagen buena
    assert xml + info.file_size + imagen > 2 * 2**20  # sin descontar la imagen, no entra
    assert xml + info.file_size <= 2 * 2**20  # descontándola, entra
    assert fs._excel_liviano(bytes(libro), ".xlsx") is True
