# Decisión: los supuestos se muestran, no se adivinan

> Decisión de PM del 2026-07-26, tomada por delegación explícita del dueño.
> Incluye el ataque adversarial contra la propia decisión, como corresponde a
> un cambio que toca el TXT que va a la aduana.

---

## La decisión

**Todo campo que el sistema declara sin preguntar se le muestra al despachante
antes de generar. Ningún campo se inventa. Ningún campo se cambia sin
evidencia de un archivo real.**

En concreto:

| Situación | Qué hace el sistema |
|---|---|
| Sé el valor correcto (evidencia de archivo real) | Lo declaro bien |
| No lo sé y lo puedo calcular con seguridad | Lo calculo **y lo aviso** |
| No lo sé y no lo puedo calcular | **No declaro nada** y lo aviso |
| Va fijo porque todavía no se puede elegir | Lo declaro fijo **y lo aviso** |

Los avisos aparecen en la pantalla de generar, junto a los que ya existían. No
bloquean.

---

## Por qué esto y no otra cosa

Esta sesión encontró **cuatro campos** que el sistema elegía solo y nadie veía:

- el **año del `IEXT`**, escrito a mano como `"25"` — mal en toda declaración de
  2026 en adelante;
- la **procedencia**, igualada al origen — en el archivo real difieren;
- **`CARTUSO`**, fijo en `3` — el archivo real dice `2`;
- **`IVAADICIONAL1`**, fijo en `IVAAD1` — el archivo real dice `NO_VALIDA`.

Los cuatro producen un TXT que **pasa todas nuestras validaciones**. El error
aparece en la aduana, con el nombre del cliente encima.

El patrón es siempre el mismo: **no es que el sistema se equivoque, es que
decide en silencio.** Arreglar los cuatro casos uno por uno no evita el
quinto. Lo que lo evita es que ningún supuesto quede invisible.

Y coincide con lo que el producto ya prometía: *"la AI recomienda, el humano
confirma"*. Un valor asumido en silencio rompe esa promesa igual que uno
inventado.

---

## Ataque adversarial contra esta decisión

Lo que le respondería un Rojo, y qué contesto.

### 🔴 "Cambiaste el TXT de operaciones EXW sin que el dueño lo aprobara"

**Es cierto y es el reproche más justo.** Antes, una operación EXW emitía
`GTOS-POS-FOB=440.47`. Ahora, sin importe explícito, no emite ese bloque.
Cambié la salida de un archivo que va a la aduana basándome en parte en
resúmenes de buscador que **no pude abrir** (todos los sitios dieron 403).

**Qué me deja tranquila:** la elección del campo (ANT vs POS por condición de
venta) no sale de la web, sale de **los dos archivos reales del propio
dueño** — el EXW usa ANT, el DDP usa POS. Eso es evidencia primaria del
sistema real, no una interpretación.

**Qué no me deja tranquila:** el comportamiento nuevo (omitir) es tan
silencioso como el viejo (declarar mal). Por eso el aviso no es un adorno: es
lo que convierte este cambio en aceptable. Sin el aviso, habría que revertir.

**Cómo se revierte si el despachante dice que estaba bien antes:** un cambio,
en `maria_generator.py`, volver `campo_gastos` a `"GTOS-POS-FOB    "` fijo y
el importe a `flete + seguro`. Está aislado a propósito.

### 🔴 "Los avisos se ignoran. Estás agregando ruido, no arreglando nada"

**Parcialmente cierto.** Un aviso que aparece siempre se vuelve invisible en
dos semanas.

**Mitigación:** son **cuatro como máximo**, específicos, con el número del
ítem, y dos de ellos desaparecen solos en cuanto el dato se puede cargar
(gastos y procedencia). Los otros dos (`CARTUSO`, `IVAADICIONAL1`) están
puestos justamente para que molesten hasta que se construya la pantalla.

**Lo que no hago:** avisar de los 13 campos fijos del formato. Esos son
constantes reales, avisarlos sería ruido puro.

### 🔴 "Estás narrando en vez de arreglar. Arreglá CARTUSO de una vez"

**No, y a propósito.** No tengo ninguna evidencia de cuándo va `2` y cuándo
va `3`. Tengo un archivo con cada valor y ninguna fuente que explique la
regla — la especificación de la Interfaz Despachantes no es pública.

Si eligiera uno, estaría haciendo exactamente lo que este producto promete no
hacer. Prefiero declarar el valor de siempre y decirlo en voz alta, a inventar
una regla y que el despachante nunca se entere.

### 🔴 "Esto frena el deploy"

**No.** Es aditivo: un campo nuevo en la respuesta y avisos en una lista que
el frontend ya renderiza. Nada bloquea, nada cambia de flujo. 126 pruebas en
verde.

### 🔴 "Metiste demasiados cambios al generador en una sola sesión"

**Cierto, y vale registrarlo.** Se tocaron cuatro cosas del TXT: año del
`IEXT`, sub-ítems, gastos a FOB y estos avisos.

**Lo que las separa por riesgo:**

| Cambio | Evidencia | ¿Cambia lo que ya salía? |
|---|---|---|
| Año del `IEXT` | Dos archivos reales | Sí, **y estaba mal** |
| Sub-ítems | Un archivo real, calcado | No: es opcional |
| Avisos | — | No: son informativos |
| **Gastos a FOB** | Dos archivos + web sin abrir | **Sí — el único discutible** |

Tres de cuatro son seguros. El cuarto está marcado como tal en el `HANDOFF`,
en el `CHANGELOG` y acá.

---

## Lo que sigue necesitando al despachante

Ningún aviso reemplaza estas definiciones:

1. **`CARTUSO`** — cuándo va `2` y cuándo `3`.
2. **`IVAADICIONAL1`** — cuándo `IVAAD1` y cuándo `NO_VALIDA`.
3. **Código de proveedor** — el `(00272)` de `LDDTNOMFOD`: quién lo asigna.
4. **`BANCOSARGENTINA`** — si va siempre o sólo en algunas operaciones.
5. **Gastos a FOB** — confirmar la regla ANT/POS antes de darla por cerrada.

Mientras no estén, el sistema declara el valor de siempre **y lo dice**.
