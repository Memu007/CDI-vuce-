# Datos públicos para las Devs

| Archivo | Qué es | De dónde |
|---|---|---|
| `arancel_ARCA_07102026.zip` | Arancel Integrado Aduanero de ARCA: `nomenclador_07102026.txt` (10.504 NCM, con la enmienda de 2022), `capitulo_07102026.txt` (notas de capítulos) y `sufijos_07102026.txt` (sufijos de valor del SIM). SHA-256 `0fb407ceebd3db6ef4b9314ba51c204383db9c5d5c707eb34ce6ced85f2b5d44` | Lo bajó Emi y lo pasó por el chat el 2026-10-07 (desde acá la red bloquea `www.arca.gob.ar`). El de julio era otro (`d14605c9…`, `nomenclador_19122018.txt`) |

Son datos públicos: no hay nada de Emi ni del despachante. Se usan con
`scripts/import_arancel_nomenclador.py` (CATALOGO-NCM-1) y, los sufijos, en
MARIA-6.
