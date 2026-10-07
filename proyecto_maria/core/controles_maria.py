"""Controles antes de generar el TXT de MARIA (MARIA-1b).

Lo que impide un TXT válido es un error y no deja generar; lo dudoso es una
advertencia. No cambian lo que sale en el TXT: sólo cuándo se puede generar.
Los usan `/generate_maria` (frena con 400) y `/api/validate/smart` (el
semáforo y la pantalla de generar los muestran antes).
"""
import re

from proyecto_maria.core.maria_generator import INCOTERMS_VALIDOS

# Monedas habituales en despachos, con el código de MARIA (el dólar es DOL).
# Es la misma lista que la pantalla de revisión (review.js, MONEDA_WHITELIST).
MONEDAS_HABITUALES = {"DOL", "EUR", "BRL", "ARS", "CLP", "UYU", "GBP", "JPY", "CNY"}

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

_CONTROL_O_IGUAL = re.compile(r"[\x00-\x1f\x7f=]")


def limpiar_texto(valor):
    """Sin saltos de línea, tabulaciones ni «=»: no pueden partir ni inventar
    una línea del TXT (M10). Un salto o tabulación pasa a ser un espacio; el
    «=», un guion. Lo que no es texto vuelve igual."""
    if not isinstance(valor, str) or not _CONTROL_O_IGUAL.search(valor):
        return valor
    limpio = re.sub(r"[\x00-\x1f\x7f]+", " ", valor).replace("=", "-")
    return re.sub(r" {2,}", " ", limpio).strip()


def cuit_valido(cuit) -> bool:
    """11 dígitos con el dígito verificador de ARCA (igual que la pantalla,
    review.js validateCuitAR)."""
    norm = re.sub(r"[-\s]", "", str(cuit or ""))
    if not re.fullmatch(r"\d{11}", norm):
        return False
    pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    resto = sum(int(d) * p for d, p in zip(norm[:10], pesos)) % 11
    esperado = 0 if resto == 0 else 9 if resto == 1 else 11 - resto
    return esperado == int(norm[10])


def _numero(valor):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _control_ncm(pieza, n: int, errores: list, advertencias: list) -> None:
    """Si la NCM perdió el 0 inicial (Excel guarda 01012100 como 1012100), es
    un error y se propone con el 0. Si no está en el nomenclador, se avisa:
    el que tenemos es el de 2018 (`nomenclador_19122018.txt`) y le faltan las
    posiciones de la enmienda de 2022 (p. ej. 8517.13.00), así que no frena."""
    from proyecto_maria.core.ncm_catalog import find_by_code

    texto = re.sub(r"[\s.]", "", str(pieza or "")).upper()
    if not texto:
        return  # la falta de NCM ya la marca la validación de siempre
    m = re.fullmatch(r"(\d+)([A-Z]?)", texto)
    if not m:
        return  # formato raro: lo marca la validación de la posición SIM
    digitos, letra = m.groups()
    # SIM completa (11 dígitos y letra) o NCM sola (8 dígitos).
    if len(digitos) in (11, 8):
        if find_by_code(digitos[:8]) is None:
            advertencias.append(
                f"Item {n}: la NCM {digitos[:8]} no está en el nomenclador que tenemos "
                "(el de 2018). Revisá que esté vigente."
            )
        return
    # Le falta el 0 inicial: 10 dígitos y letra, o 7 dígitos.
    if len(digitos) in (10, 7) and find_by_code("0" + digitos[:7]) is not None:
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

    moneda = str(cabecera.get("moneda") or "").strip().upper()
    if not moneda:
        errores.append("Falta la moneda de la operación.")
    elif moneda == "USD":
        errores.append("La moneda «USD» en MARIA se escribe «DOL».")
    elif not re.fullmatch(r"[A-Z]{3}", moneda):
        errores.append(f"La moneda «{moneda}» no es un código de 3 letras.")
    elif moneda not in MONEDAS_HABITUALES:
        advertencias.append(
            f"La moneda «{moneda}» no es una de las habituales "
            f"({', '.join(sorted(MONEDAS_HABITUALES))}). Revisá el código."
        )

    incoterm = str(cabecera.get("incoterm") or "").strip().upper()
    if not incoterm:
        errores.append("Falta el incoterm de la operación.")
    elif incoterm not in INCOTERMS_VALIDOS:
        errores.append(
            f"El incoterm «{incoterm}» no es válido "
            f"({', '.join(sorted(INCOTERMS_VALIDOS))})."
        )

    cuit = str(cabecera.get("comprador_cuit") or "").strip()
    if not cuit:
        # La pantalla de revisión lo deja opcional («extranjeros sin CUIT»):
        # vacío avisa; si exigirlo es una decisión de la PM (MARIA-1b, D20).
        advertencias.append(
            "Falta el CUIT del importador: completalo acá o en el Kit SIM antes de presentar."
        )
    elif not cuit_valido(cuit):
        errores.append(
            f"El CUIT del importador «{cuit}» no es válido: tiene que tener 11 "
            "dígitos y el dígito verificador correcto."
        )

    for campo, nombre in (("flete", "flete"), ("seguro", "seguro")):
        valor = _numero(cabecera.get(campo))
        if valor is not None and valor < 0:
            errores.append(f"El {nombre} no puede ser negativo ({valor:g}).")

    return errores, advertencias
