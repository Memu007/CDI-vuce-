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


# Corre en un python nuevo: arma la bomba, la lee con `leer_despacho_aparte`
# e imprime el resultado y la memoria máxima del proceso que leyó y la propia.
MEDIR = r"""
import asyncio, json, resource, sys
from tests import pdf_bombas
from proyecto_maria.core import despacho_lector
data = getattr(pdf_bombas, sys.argv[1])(*map(int, sys.argv[2:]))
try:
    r = asyncio.run(despacho_lector.leer_despacho_aparte(data, 120))
    salida = {"resultado": {k: r.get(k) for k in ("renglones", "sin_texto", "avisos")}}
except despacho_lector.PdfDemasiadoPesado as e:
    salida = {"pesado": str(e)}
salida["lector_mb"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024
salida["propio_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
print(json.dumps(salida))
"""
