"""PDFs sintéticos chicos que se inflan al leerlos (DESPACHO-1b).

Sin imports pesados: `medir_lectura_aparte` corre en un python nuevo y chico,
porque la memoria que se mide del proceso que lee incluye la que hereda al
nacer (`RUSAGE_CHILDREN` cuenta la del fork)."""
import zlib


def _pdf(armar):
    objs = []

    def add(b):
        objs.append(b)
        return len(objs)

    catalogo = armar(add, objs)
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, catalogo, xref)
    return out


def _flujo(add, inicio, relleno, fin=b""):
    """Un flujo comprimido de `inicio` + `relleno` espacios + `fin`, sin tener
    nunca el relleno entero en memoria."""
    z = zlib.compressobj(9)
    partes = [z.compress(inicio)]
    bloque = b" " * (1 << 20)
    for _ in range(relleno >> 20):
        partes.append(z.compress(bloque))
    partes += [z.compress(b" " * (relleno & ((1 << 20) - 1)) + fin), z.flush()]
    data = b"".join(partes)
    return add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream")


def _hojas(add, objs, contenidos, fuentes=None):
    raiz = add(b"")
    fuente = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    hojas = []
    for c in contenidos:
        recursos = fuentes or b"/F1 %d 0 R" % fuente
        hojas.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 842 595] "
                         b"/Resources << /Font << %s >> >> /Contents %d 0 R >>" % (raiz, recursos, c)))
    objs[raiz - 1] = (b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % h for h in hojas)
                      + b"] /Count %d >>" % len(hojas))
    return add(b"<< /Type /Catalog /Pages %d 0 R >>" % raiz)


def hojas(contenidos):
    """Una hoja por (texto, relleno): `texto` en Courier y después `relleno`
    bytes de espacios en el contenido, que no cambian el texto."""
    def armar(add, objs):
        return _hojas(add, objs, [_flujo(add, b"BT /F1 9 Tf 20 500 Td (%s) Tj ET\n" % texto.encode(), relleno)
                                  for texto, relleno in contenidos])
    return _pdf(armar)


def hojas_pesadas(cuantas, mb):
    """`cuantas` hojas cuyo contenido descomprimido pesa `mb` MB cada una."""
    return hojas([(f"HOJA PESADA {n}", mb << 20) for n in range(cuantas)])


def muchas_fuentes(fuentes, kb):
    """Una hoja con `fuentes` fuentes, cada una con un mapa de caracteres de
    `kb` KB: cada flujo pasa los topes por flujo, pero todos juntos no."""
    def armar(add, objs):
        fs = [add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /ToUnicode %d 0 R >>"
                  % _flujo(add, b"%% %d\n" % n, kb << 10)) for n in range(fuentes)]
        recursos = b" ".join(b"/F%d %d 0 R" % (n, o) for n, o in enumerate(fs))
        return _hojas(add, objs, [_flujo(add, b"BT /F0 9 Tf 20 500 Td (HOLA) Tj ET", 0)], recursos)
    return _pdf(armar)


def trabajo(hojas=20, operaciones=14000):
    """`hojas` hojas que comparten un contenido de menos de 512 KB con
    `operaciones` operaciones de texto: el PDF pesa unos 50 KB y cada hoja
    queda debajo del tope de bytes, pero leerla cuesta casi un segundo."""
    lineas = b"".join(b"BT /F1 9 Tf %d %d Td (XX) Tj ET\n" % (i % 800, i % 500) for i in range(operaciones))

    def armar(add, objs):
        z = zlib.compress(lineas, 9)
        c = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(z) + z + b"\nendstream")
        return _hojas(add, objs, [c] * hojas)
    return _pdf(armar)


def parseo_caro(hojas=200, renglones=500):
    """`hojas` hojas que comparten `renglones` líneas de 40 rótulos
    («Tipo Lista Estado Unidad» diez veces): entender el texto de una hoja
    cuesta unas tres veces lo que extraerlo, así que el tope de CPU que
    cubría sólo la extracción dejaba gastar varias veces más (DESPACHO-1b)."""
    lineas = b"".join(b"BT /F1 9 Tf 10 %d Td (%s) Tj ET\n" % (i, b"Tipo Lista Estado Unidad " * 10)
                      for i in range(renglones))

    def armar(add, objs):
        z = zlib.compress(lineas, 9)
        c = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(z) + z + b"\nendstream")
        return _hojas(add, objs, [c] * hojas)
    return _pdf(armar)


def una_hoja_cara(kb=80):
    """Una sola hoja con `kb` KB de saltos de renglón («T*»): pesa poco y
    queda debajo del tope de bytes, pero leerla cuesta el cuadrado de lo que
    pesa (80 KB, unos 6 s). El tope de CPU entre hojas no la cortaba."""
    def armar(add, objs):
        return _hojas(add, objs, [_flujo(add, b"BT /F1 9 Tf 1 TL " + b"T* " * (kb * 1024 // 3), 0, b"ET\n")])
    return _pdf(armar)


def run_length(mb):
    """Una hoja cuyo contenido, con RunLengthDecode, se infla a `mb` MB (128
    espacios cada dos bytes), y después una hoja normal. Los topes de pypdf
    no son sólo para Flate."""
    def armar(add, objs):
        crudo = b"BT /F1 9 Tf 20 500 Td (HOJA INFLADA) Tj ET\n"
        data = bytes([len(crudo) - 1]) + crudo + b"\x81 " * ((mb << 20) // 128) + b"\x80"
        inflada = add(b"<< /Length %d /Filter /RunLengthDecode >>\nstream\n" % len(data) + data
                      + b"\nendstream")
        return _hojas(add, objs, [inflada, _flujo(add, b"BT /F1 9 Tf 20 500 Td (HOJA NORMAL) Tj ET\n", 0)])
    return _pdf(armar)


def texto_largo(hojas, lineas=100, ancho=4000):
    """`hojas` hojas con `lineas` líneas de `ancho` letras cada una, en letra
    de un punto: cada hoja da unos 400 000 caracteres de texto."""
    def armar(add, objs):
        fila = b"X" * ancho
        contenido = b"".join(b"BT /F1 1 Tf 0 %d Td (%s) Tj ET\n" % (590 - 5 * i, fila) for i in range(lineas))
        return _hojas(add, objs, [_flujo(add, contenido, 0) for _ in range(hojas)])
    return _pdf(armar)


# Corre en un python nuevo: arma la bomba, la lee con `leer_despacho_aparte`
# e imprime el resultado, la memoria máxima del proceso que leyó y la propia, y
# la CPU que gastó el que leyó. LIMITE_CPU cambia su tope de CPU.
MEDIR = r"""
import asyncio, json, os, resource, sys
from tests import pdf_bombas
from proyecto_maria.core import despacho_lector
data = getattr(pdf_bombas, sys.argv[1])(*map(int, sys.argv[2:]))
try:
    tope = {"limite_cpu_s": float(os.environ["LIMITE_CPU"])} if "LIMITE_CPU" in os.environ else {}
    r = asyncio.run(despacho_lector.leer_despacho_aparte(data, 120, **tope))
    salida = {"resultado": {k: r.get(k) for k in ("renglones", "sin_texto", "avisos")}}
except despacho_lector.PdfDemasiadoPesado as e:
    salida = {"pesado": str(e)}
salida["lector_mb"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024
salida["propio_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
hijos = resource.getrusage(resource.RUSAGE_CHILDREN)
salida["lector_cpu_s"] = hijos.ru_utime + hijos.ru_stime
print(json.dumps(salida))
"""
