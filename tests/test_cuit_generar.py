"""Con un CUIT del despachante que no es un CUIT no se genera el TXT: iría al
CDDTAGR. Vale para el que ya estaba guardado en el perfil y para el que manda
la operación en `cuit_agr`, y el error dice dónde se corrige.

Lo mismo en el navegador: `scripts/testing/pantalla_cuit_generar1.js`.
"""
import re

import pytest
from sqlalchemy import func, select

from proyecto_maria.database.models import Estudio, Operation
from tests.test_maria7_rechazos_24_10 import _pedido
from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    _bearer, _consulta, _http, _login, _poner, _sin_limites, _tablas, _usuario,
)

BUENO, OTRO_BUENO, MALO = "20111111112", "30712345671", "20999999998"
EN_EL_PERFIL = "Corregilo en «Mi perfil», campo «Mi CUIT (despachante)»."
EN_LA_OPERACION = ("No es el de tu perfil: lo mandó la operación. Si ya lo corregiste en «Mi perfil», "
                   "recargá la página.")
EN_EL_ESTUDIO = "Es el del estudio elegido: en «Mi perfil», «Mis estudios», borralo y agregalo de nuevo."
# de dónde sale el malo → (guardado en el perfil, `cuit_agr`, el del estudio elegido, el que se nombra, dónde se corrige)
MALOS = {
    "guardado en el perfil": (MALO, "", None, MALO, EN_EL_PERFIL),
    "guardado en el perfil, como lo manda la pantalla": (MALO, MALO, None, MALO, EN_EL_PERFIL),
    "guardado con guiones y un espacio": ("20-99999999 8", "", None, MALO, EN_EL_PERFIL),
    "en cuit_agr, con uno bueno en el perfil": (BUENO, "30712345670", None, "30712345670", EN_LA_OPERACION),
    "en cuit_agr con guiones, sin CUIT en el perfil": (None, "20-99999999-8", None, MALO, EN_LA_OPERACION),
    "en cuit_agr de puros espacios, sin CUIT en el perfil": (None, "   ", None, "", EN_LA_OPERACION),
    "en el estudio elegido, con uno bueno en el perfil y en cuit_agr": (BUENO, BUENO, MALO, MALO, EN_EL_ESTUDIO),
}
# qué se usa → (guardado en el perfil, `cuit_agr`, con estudio elegido, CDDTAGR)
BUENOS = {
    "el del perfil": (BUENO, "", False, BUENO),
    "cuit_agr, aunque el del perfil sea malo": (MALO, OTRO_BUENO, False, OTRO_BUENO),
    "el estudio, aunque los otros dos sean malos": (MALO, MALO, True, OTRO_BUENO),
    # los dos verificadores que no salen de «11 − resto»: el 0 y el 9
    "cuit_agr con verificador 0": (None, "20111111120", False, "20111111120"),
    "cuit_agr con verificador 9, guiones y un espacio": (None, "20-11111118 9", False, "20111111189"),
}


def _cuenta(cuit):
    """Una cuenta nueva con ese CUIT puesto directo en la base (la API no guarda uno malo) y su sesión."""
    u, _ = _usuario()
    if cuit:
        _poner(u, cuit=cuit)
    return u, _bearer(_login(u))


def _estudio_en_la_base(u, cuit):
    """El id de un estudio puesto directo en la base: el alta no guarda uno con un CUIT malo."""
    async def _alta(s):
        estudio = Estudio(owner_username=u, nombre="Estudio Inventado", cuit=cuit)
        s.add(estudio)
        await s.flush()
        return estudio.id
    return _consulta(_alta)


def _operaciones(u):
    async def _contar(s):
        return (await s.execute(select(func.count()).select_from(Operation).where(Operation.owner_username == u))).scalar()
    return _consulta(_contar)


@pytest.mark.parametrize("origen", MALOS)
def test_con_un_cuit_del_despachante_malo_no_se_genera_y_dice_donde_corregirlo(origen):
    perfil, cuit_agr, del_estudio, nombrado, donde = MALOS[origen]
    u, sesion = _cuenta(perfil)
    pedido = _pedido(cuit_agr=cuit_agr)
    if del_estudio:
        pedido["estudio_id"] = _estudio_en_la_base(u, del_estudio)
    r = _http().post("/generate_maria", json=pedido, headers=sesion)
    assert r.status_code == 400, f"{origen}: {r.status_code} {r.text[:300]}"
    assert r.json()["detail"] == {"errors": [
        f"El CUIT del despachante «{nombrado}» no es válido: son 11 dígitos (0-9) y el último es el verificador. {donde}"]}
    assert _operaciones(u) == 0, "lo que no se genera no queda contado ni guardado"


@pytest.mark.parametrize("usado", BUENOS)
def test_con_un_cuit_del_despachante_bueno_se_genera(usado):
    perfil, cuit_agr, con_estudio, cddtagr = BUENOS[usado]
    u, sesion = _cuenta(perfil)
    pedido = _pedido(cuit_agr=cuit_agr)
    if con_estudio:
        r = _http().post("/api/estudios", json={"nombre": "Estudio Inventado", "cuit": cddtagr}, headers=sesion)
        assert r.status_code == 200, r.text
        pedido["estudio_id"] = r.json()["estudio"]["id"]
    r = _http().post("/generate_maria", json=pedido, headers=sesion)
    assert r.status_code == 200, f"{usado}: {r.status_code} {r.text[:300]}"
    assert re.findall(r"^CDDTAGR=(.*?)\r?$", r.json()["content"], re.M) == [cddtagr]
    assert _operaciones(u) == 1
