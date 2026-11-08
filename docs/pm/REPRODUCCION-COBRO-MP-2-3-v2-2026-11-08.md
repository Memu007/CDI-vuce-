# Reproducción COBRO-MP-2 vuelta 2 + COBRO-MP-3 (Dev técnica), 2026-11-08

Sobre `71e15df` (informe `335d287b`). Veredicto: **devolución**, por un camino
real de producto y por huecos de prueba en familias ya pedidas.

| Qué | Resultado |
|---|---|
| tests de cobro de la entrega | `211 passed` |
| `cobro_mp3.sh 71e15df` | 18 ROJO, sin falla |
| `cobro_mp2.sh 71e15df` | al veredicto: 41 ROJO de 77, ningún VERDE; seguía corriendo (log `/tmp/cdi-pm/mp23-sab2.log`) |
| adversario Opus alto | 30 mutaciones; 7 verdes que importan y un camino real |

## Camino real (reproducido por mí)

Quien abrió la suscripción del estudio cancela; MP cancela pero la respuesta
se pierde y la relectura falla:

```
1er intento: 503 'No se pudo confirmar la cancelación en Mercado Pago. Probá de nuevo en unos minutos.'
reintento de quien abrió: 403 'Sólo quien administra el estudio o quien abrió la suscripción que lo paga puede cancelar el plan.'
billing/me: {'billing_status': 'active', 'renueva': True, 'suscripcion_abierta': True}
reactivar de quien abrió: 403 '… puede reactivar el plan.'
```

No se cobra de más (MP quedó `cancelled`), pero CDI dice que renueva y el
reintento que pide el texto no funciona para ella; sólo la dueña lo destraba.
Contradice la D112 del informe («al reintentar se concilia»): vale para la
dueña, no para quien abrió.

El caso, para copiar a `tests/`:

```python
import httpx
from tests.test_cobro_mp2 import (SUS, FALLA, PEDIDOS, _RUTA_SUS, _org_con_suscripcion, _leer, _mp, client)  # noqa: F401
from tests.test_cobro_mp1 import _leer_org

def test_abrio_cancela_mp_cancela_pero_contesta_mal_y_queda_trabada(client):
    nombres, sid, org_id, _ = _org_con_suscripcion(client, "abrio")
    def _cancela_y_contesta_500(request):
        s = _RUTA_SUS.fullmatch(str(request.url)).group(1)
        if request.method == "PUT":
            SUS[s] = "cancelled"
            return httpx.Response(500, json={})
        if FALLA.get("lecturas", 0) >= 1:
            return httpx.Response(500, json={})
        FALLA["lecturas"] = FALLA.get("lecturas", 0) + 1
        return httpx.Response(200, json={"id": s, "status": SUS[s]})
    FALLA["PUT"] = FALLA["GET"] = _cancela_y_contesta_500
    r1 = client.post("/api/billing/cancel")
    FALLA.clear()
    r2 = client.post("/api/billing/cancel")
    # hoy: r1 503, r2 403, org sigue active con el sid anotado
```

## Mutaciones verdes del adversario (`main.py` en `71e15df`)

| # | mutación | familia |
|---|---|---|
| W1 | la firma no compara el primer carácter (l.10675) | 1 firma |
| W2 | compara sólo los 8 primeros y el último | 1 firma |
| W7 | no compara los caracteres 30 a 33 | 1 firma |
| W4 | dos `v1=` en el encabezado: acepta sin comparar | 1 firma |
| X1 | el 503 de sacar dice «ya no está en el estudio» (l.10086) | 5 texto |
| X2 | el 503 del checkout dice «tu plan sigue igual» (l.11056) con la vieja ya cancelada | 5 texto |
| T1 | checkout: cada lectura inicial con su propio plazo (l.11028) | 3 plazo |
| A3 | reactivar: un sid propio que no paga alcanza | 2 quién toca |
| R1 | sin la guarda «No podés removerte a vos mismo» (l.10079) | fuera de la pieza |

Inocuas o sólo visibles con candados reales (no se piden): W3, W5, W6, A2, C5,
C6, T2.

No corrí la suite completa en esta vuelta (tomo la de la Dev: 4585 passed).
