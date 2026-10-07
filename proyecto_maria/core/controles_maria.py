"""Controles antes de generar el TXT de MARIA (MARIA-1b).

Lo que impide un TXT válido es un error y no deja generar; lo dudoso es una
advertencia. No cambian lo que sale en el TXT: sólo cuándo se puede generar.
Los usan `/generate_maria` (frena con 400) y `/api/validate/smart` (el
semáforo y la pantalla de generar los muestran antes).
"""
import math
import re

from proyecto_maria.core.maria_generator import (
    _INCOTERMS_GRUPO_C_D, IMPORTE_MAXIMO, INCOTERMS_VALIDOS, importe_valido,
)

# Los que acepta el generador, más FAS (la pantalla lo ofrece) y los de 2000
# y 2010 que el generador todavía reconoce (DAT, DAF, DES, DEQ, DDU).
INCOTERMS_ACEPTADOS = INCOTERMS_VALIDOS | _INCOTERMS_GRUPO_C_D | {"FAS"}

# La única moneda confirmada con un archivo real es DOL: las demás avisan
# hasta que el despachante confirme sus códigos (devolución de MARIA-1b).
MONEDAS_CONFIRMADAS = {"DOL"}

# Campos de texto de la cabecera que van tal cual a una línea «CLAVE=valor».
CAMPOS_DE_TEXTO = (
    "operation_id", "vendedor_nombre", "vendedor_id", "comprador_nombre",
    "comprador_domicilio", "comprador_fecha_inic_activ", "cuit_agr",
    "comprador_cuit", "moneda", "incoterm", "fecha_embarque", "fecha_emision",
    "aduana_codigo", "tipo_destinacion",
)
CAMPOS_DE_TEXTO_DEL_ITEM = (
    "descripcion", "pieza", "ncm", "origen", "pais_origen", "procedencia",
    "pais_procedencia", "unidad", "unidad_medida", "um", "codigo_parte",
)

# Controles C0 y C1 (\x85 es «nueva línea»), y los separadores de línea y de
# párrafo de Unicode: cualquiera puede leerse como fin de línea.
_SALTOS_Y_CONTROLES = r"[\x00-\x1f\x7f-\x9f\u2028\u2029]"
_CONTROL_O_IGUAL = re.compile(_SALTOS_Y_CONTROLES[:-1] + "=]")


def limpiar_texto(valor):
    """Sin saltos de línea, tabulaciones ni «=»: no pueden partir ni inventar
    una línea del TXT (M10). Un salto o tabulación pasa a ser un espacio; el
    «=», un guion. Lo que no es texto vuelve igual."""
    if not isinstance(valor, str) or not _CONTROL_O_IGUAL.search(valor):
        return valor
    limpio = re.sub(_SALTOS_Y_CONTROLES + "+", " ", valor).replace("=", "-")
    return re.sub(r" {2,}", " ", limpio).strip()


def cuit_valido(cuit) -> bool:
    """11 dígitos con el dígito verificador de ARCA (igual que la pantalla,
    review.js validateCuitAR)."""
    norm = re.sub(r"[-\s]", "", str(cuit or ""))
    # Sólo 0-9: «\d» acepta dígitos de ancho completo o arábigos, y el TXT
    # los escribiría tal cual (devolución de MARIA-1b).
    if not re.fullmatch(r"[0-9]{11}", norm):
        return False
    pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    resto = sum(int(d) * p for d, p in zip(norm[:10], pesos)) % 11
    esperado = 0 if resto == 0 else 9 if resto == 1 else 11 - resto
    return esperado == int(norm[10])


def _numero_o_none(valor):
    """El número, o None si falta o es un texto que no es número (eso lo marca
    el control de siempre). Un entero enorme (10**400) es infinito y una lista
    u objeto no es un número: los dos son un monto inválido (EXCEL-2)."""
    if valor is None or isinstance(valor, bool) or (isinstance(valor, str) and not valor.strip()):
        return None
    if isinstance(valor, (list, dict)):
        return math.nan
    try:
        return float(valor)
    except OverflowError:
        return math.inf
    except (TypeError, ValueError):
        return None


def digitos_raros(valor) -> bool:
    """Si el texto tiene dígitos que no son 0-9 (de ancho completo, arábigos):
    el TXT los escribiría tal cual (EXCEL-2, de paso)."""
    return any(c.isdigit() and not ("0" <= c <= "9") for c in str(valor or ""))


def _fuera_de_rango(*valores) -> bool:
    """NaN, infinito o más que un billón, solo o multiplicado por la cantidad:
    un número así, aunque sea finito, llega al TXT como «inf» o «nan» al
    hacer las cuentas (revisión de la devolución de MARIA-1b)."""
    numeros = [v for v in valores if v is not None]
    if any(not math.isfinite(v) or abs(v) > IMPORTE_MAXIMO for v in numeros):
        return True
    producto = 1.0
    for v in numeros:
        producto *= v
    return len(numeros) > 1 and (not math.isfinite(producto) or abs(producto) > IMPORTE_MAXIMO)


def montos_fuera_de_rango(items, cabecera: dict) -> list:
    """Errores por montos que no son números de verdad, en los productos, sus
    subítems y la cabecera. Mismo texto que el control de siempre
    (validate_items_for_maria) y que el generador (importe_valido)."""
    errores: list = []
    for n, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            continue
        cantidad = _numero_o_none(item.get("cantidad"))
        valor = _numero_o_none(item.get("valor_unitario"))
        total = _numero_o_none(item.get("valor_total"))
        peso_kg = _numero_o_none(item.get("peso_kg"))
        peso_unitario = _numero_o_none(item.get("peso_unitario"))
        if _fuera_de_rango(cantidad):
            errores.append(f"Item {n}: Cantidad inválida")
        if _fuera_de_rango(cantidad, valor) or _fuera_de_rango(total):
            errores.append(f"Item {n}: Valor inválido")
        if _fuera_de_rango(peso_kg) or _fuera_de_rango(cantidad, peso_unitario):
            errores.append(f"Item {n}: Peso inválido")
        for m, sub in enumerate(item.get("subitems") or [], start=1):
            if not isinstance(sub, dict):
                continue
            sub_cant = _numero_o_none(sub.get("cantidad"))
            sub_valor = _numero_o_none(sub.get("valor_unitario"))
            if _fuera_de_rango(sub_cant):
                errores.append(f"Item {n}, sub-ítem {m}: Cantidad inválida")
            if _fuera_de_rango(sub_cant, sub_valor):
                errores.append(f"Item {n}, sub-ítem {m}: Valor inválido")
    for campo, nombre in _IMPORTES_DE_LA_CABECERA:
        valor = cabecera.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            continue
        try:
            importe_valido(valor, nombre)
        except ValueError as e:
            errores.append(str(e))
    return errores

_IMPORTES_DE_LA_CABECERA = (
    ("flete", "Flete"), ("seguro", "Seguro"),
    ("gastos_fob", "Gastos (gastos_fob)"), ("gastos_anteriores_fob", "Gastos (gastos_anteriores_fob)"),
)


_CODIGOS = None


def _en_el_nomenclador(codigo8: str) -> bool:
    """Búsqueda directa: find_by_code recorre el catálogo entero por cada
    ítem, y con miles de ítems trababa el servidor."""
    global _CODIGOS
    if _CODIGOS is None:
        from proyecto_maria.core.ncm_catalog import load_catalog
        codigos = frozenset(i.codigo for i in load_catalog())
        if not codigos:
            return True  # sin catálogo no se puede mirar: no se avisa en falso
        _CODIGOS = codigos
    return codigo8 in _CODIGOS


def _control_ncm(pieza, n: int, errores: list, advertencias: list) -> None:
    """Si la NCM perdió el 0 inicial (Excel guarda 01012100 como 1012100), es
    un error y se propone con el 0. Si no está en el nomenclador, se avisa:
    el que tenemos es el de 2018 (`nomenclador_19122018.txt`) y le faltan las
    posiciones de la enmienda de 2022 (p. ej. 8517.13.00), así que no frena."""
    texto = re.sub(r"[\s.]", "", str(pieza or "")).upper()
    if not texto:
        return  # la falta de NCM ya la marca la validación de siempre
    m = re.fullmatch(r"(\d+)([A-Z]?)", texto)
    if not m:
        return  # formato raro: lo marca la validación de la posición SIM
    digitos, letra = m.groups()
    # SIM completa (11 dígitos y letra) o NCM sola (8 dígitos).
    if len(digitos) in (11, 8):
        if not _en_el_nomenclador(digitos[:8]):
            advertencias.append(
                f"Item {n}: la NCM {digitos[:8]} no está en el nomenclador que tenemos "
                "(el de 2018). Revisá que esté vigente."
            )
        return
    # Le falta el 0 inicial: 10 dígitos y letra, o 7 dígitos.
    if len(digitos) in (10, 7) and _en_el_nomenclador("0" + digitos[:7]):
        propuesta = "0" + digitos + letra
        errores.append(
            f"Item {n}: la NCM {texto} parece haber perdido el 0 inicial "
            f"(Excel lo borra en los números). ¿Es {propuesta}?"
        )


def controles_antes_de_generar(items, cabecera: dict) -> tuple[list, list]:
    """(errores, advertencias) de la operación entera."""
    errores: list = []
    advertencias: list = []

    for n, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            continue
        _control_ncm(item.get("ncm") or item.get("pieza"), n, errores, advertencias)
    errores.extend(montos_fuera_de_rango(items, cabecera))

    moneda = str(cabecera.get("moneda") or "").strip().upper()
    if not moneda:
        errores.append("Falta la moneda de la operación.")
    elif moneda == "USD":
        errores.append("La moneda «USD» en MARIA se escribe «DOL».")
    elif not re.fullmatch(r"[A-Z]{3}", moneda):
        errores.append(f"La moneda «{moneda}» no es un código de 3 letras.")
    elif moneda not in MONEDAS_CONFIRMADAS:
        advertencias.append(
            f"La moneda «{moneda}»: sólo DOL está confirmada con un archivo real. "
            "Confirmá con el despachante que ése es el código de MARIA."
        )

    incoterm = str(cabecera.get("incoterm") or "").strip().upper()
    if not incoterm:
        errores.append("Falta el incoterm de la operación.")
    elif incoterm not in INCOTERMS_ACEPTADOS:
        errores.append(
            f"El incoterm «{incoterm}» no es válido "
            f"({', '.join(sorted(INCOTERMS_ACEPTADOS))})."
        )

    for campo, nombre in (("vendedor_id", "identificador del vendedor"),):
        if digitos_raros(cabecera.get(campo)):
            errores.append(f"El {nombre} «{cabecera.get(campo)}» tiene dígitos que no son 0-9.")

    cuit = str(cabecera.get("comprador_cuit") or "").strip()
    if not cuit:
        # Sin el CUIT del importador el TXT no sirve para presentar (D20).
        errores.append("Falta el CUIT del importador.")
    elif not cuit_valido(cuit):
        errores.append(
            f"El CUIT del importador «{cuit}» no es válido: tiene que tener 11 "
            "dígitos y el dígito verificador correcto."
        )

    return errores, advertencias
