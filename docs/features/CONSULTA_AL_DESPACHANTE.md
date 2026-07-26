# Consulta al despachante — 5 campos del MARIA.TXT

> Para copiar y pegar. Está escrito para alguien que sabe de aduana pero no
> conoce nuestro sistema: no menciona código ni pantallas.
>
> Contexto: comparamos el TXT que genera CDI contra dos declaraciones reales
> (una EXW de 2026 y una DDP de 2025). La mayoría coincide. Quedaron cinco
> campos donde los dos archivos difieren y no encontramos la regla.

---

## El mensaje

Hola. Estoy armando un sistema que genera el TXT para cargar en el Kit María
(Acciones → Interfaz Despachantes → Lectura de Archivos). Ya funciona, pero
comparando contra dos declaraciones reales me quedaron cinco dudas de
criterio. Son todas de cabecera o de ítem. ¿Me las podés contestar?

**1. Uso de la mercadería (`CARTUSO`)**
En un archivo dice `2` y en el otro `3`.
→ ¿Qué significa cada valor y cómo se decide cuál va?

**2. IVA adicional (`IVAADICIONAL1`)**
En un archivo dice `IVAAD1` y en el otro `NO_VALIDA`.
→ ¿Cuándo corresponde cada uno?

**3. Código de proveedor**
El nombre del proveedor va con un número adelante entre paréntesis, así:
`(00272) NOMBRE DEL PROVEEDOR`.
→ ¿Ese número de dónde sale? ¿Lo asignás vos por proveedor, lo da el sistema,
o sale de algún registro?

**4. Banco (`BANCOSARGENTINA`)**
En un archivo aparece con valor `191` y en el otro no aparece.
→ ¿Cuándo hay que declararlo y de dónde sale el número?

**5. Gastos respecto del FOB**
Entiendo que con condición **EXW** va `GTOS-ANT-FOB` y con condiciones de los
grupos **C y D** (CIF, CFR, DDP, etc.) va `GTOS-POS-FOB`, y que el importe es
la diferencia entre el valor en la condición pactada y el FOB declarado.
En el archivo EXW figura `150.00`, que no es flete + seguro (esos dan 440.47).
→ ¿Está bien así? ¿Y con FCA, FAS o FOB puro qué corresponde?

Gracias.

---

## Qué hacemos con cada respuesta (nota interna, no enviar)

| Campo | Hoy el sistema… | Con la respuesta |
|---|---|---|
| `CARTUSO` | Declara `3` siempre y lo avisa | Se elige por operación o se saca de la ficha del cliente |
| `IVAADICIONAL1` | Declara `IVAAD1` siempre y lo avisa | Ídem |
| Código de proveedor | No lo declara | Pasa a la ficha del proveedor: se carga una vez |
| `BANCOSARGENTINA` | No lo declara | Se agrega, probablemente a la ficha del cliente |
| Gastos a FOB | Ya implementado con esa regla | Se confirma o se revierte (un solo lugar) |

Los tres primeros hoy salen del valor por defecto **y el despachante lo ve en
pantalla antes de generar**. No es que estén mal escondidos: están declarados
como siempre y avisados. Pero mientras no haya respuesta, no se pueden elegir.

**Ninguno de los cinco frena el deploy.** Son mejoras de calidad del TXT, no
condiciones para salir a producción.
