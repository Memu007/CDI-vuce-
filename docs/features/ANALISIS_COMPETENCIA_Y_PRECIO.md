# Competencia, precio y valuación

> Análisis de PM del 2026-07-26, pedido por el dueño. Incluye el ataque
> adversarial contra las propias conclusiones.
>
> **Advertencia de método, primero:** ningún competidor publica precios, y no
> pude abrir **ninguna** de sus webs desde el entorno de la IA (todas dieron
> 403). Lo que sigue sobre precios de la competencia es **inferencia, no dato
> verificado**. Lo que sí está verificado son las *funcionalidades* que
> describen públicamente y los precios propios del repo.

---

## 1. Contra quién competimos

| Competidor | Qué es | Antigüedad |
|---|---|---|
| **Report System** | Software de comercio exterior para despachantes. Módulo PRE-MARIA con SIMI. | **Desde 1989** |
| **Gruposoft (GS Kit)** | GS Kit Pre María | Años en el rubro |
| **Darsys** | Línea de software de gestión para despachantes | Años en el rubro |
| **DATACDA / PSM** | Web, flujo SIMI completo → exporta TXT a María. *Es el sistema del manual que aportó el dueño.* | Actual |
| **Kit María (AFIP)** | El destino, no competencia. Gratis y obligatorio. | Oficial |

### ⚠️ El dato que hay que mirar de frente

La descripción pública de **Report System** dice que su módulo PRE-MARIA
incluye:

> *"control y armado de ítems **y subítems**"* y *"**lectura automatizada de
> planillas y archivos PDF** para la carga"*

Es decir: **leer el PDF de la factura y armar ítems con subítems ya lo hace
una empresa desde hace décadas.** Incluso los sub-ítems que implementamos hoy.

`docs/IDEAS_PREMIUM_FEATURES.md` afirma que la extracción de PDF con IA es
algo que *"nadie más tiene bien"*. La palabra clave puede ser **"bien"** —
pero como diferenciador de venta, "leemos el PDF" **no alcanza**. El
comprador ya escuchó eso.

---

## 2. Dónde estamos realmente parados

### Lo que NO es diferencial

- Leer la factura en PDF → la competencia lo ofrece hace años.
- Generar el TXT para el Kit María → es la categoría entera, no una ventaja.
- Sub-ítems → recién nos pusimos a la par.

### Lo que sí puede serlo

| Ventaja | ¿Qué tan sólida? |
|---|---|
| **Web, sin instalar** | Sólida contra los de escritorio; DATACDA también es web |
| **Interfaz de esta década** | Real, y el repo lo dice: la competencia tiene UI de los 90 |
| **Memoria por cliente y proveedor** | Buena, y difícil de copiar rápido |
| **"La IA recomienda, el humano confirma"** | **La más fuerte, y está desaprovechada** |
| **Precio bajo** | Es un arma, pero la peor de todas (ver abajo) |

### La ventaja que nadie está vendiendo

Esta sesión encontró, en un día, **cuatro campos que salían mal en silencio**:
el año del `IEXT`, la procedencia, `CARTUSO` e `IVAADICIONAL1`. Ninguno
rompía nada visible. Todos fallan **en la aduana**.

Un software de los 90 no te avisa de eso. Nosotros ahora sí, y encima
mostramos **todo lo que el sistema decidió sin preguntar**.

> Eso no es "un software más rápido". Es **"un software que no te deja mandar
> una declaración con un error que no ibas a ver"**.

Ese es el ángulo de venta, y es el que aguanta un precio alto.

---

## 3. Precio: qué cobraría

### Lo que cobramos hoy

`billing_service.py`: **$45.000 ARS/mes · 15 operaciones · 3 usuarios**, más
top-up de $10.000 por 10 operaciones extra.

### El problema no es el precio, es el tope

Según lo que se publica del mercado, un despachante cobra **entre $10.000 y
$30.000 ARS por operación**.

Entonces:

| | Cuenta |
|---|---|
| Factura del despachante con 15 ops | $150.000 – $450.000 ARS |
| Lo que le cobramos | $45.000 ARS |
| **Nuestra tajada** | **10% a 30% de lo que él factura** |

Eso es **muchísimo** para una herramienta —lo normal es 1% a 5%— y al mismo
tiempo **$45.000 ARS/mes es baratísimo** en términos absolutos para software
B2B profesional.

Las dos cosas son ciertas a la vez. **La culpa es del tope de 15
operaciones**, que:

1. Hace que el precio *por operación* se vea carísimo.
2. **Nos limita justo con los mejores clientes**: el despachante que hace 60
   despachos por mes es el que más nos necesita, y el que menos nos puede
   pagar bajo este esquema.
3. Convierte el top-up en un peaje molesto en vez de una expansión natural.

### Lo que propongo

Cobrar por **tamaño del estudio**, no por operación:

| Plan | Precio (ARS/mes) | Para quién | Incluye |
|---|---|---|---|
| **Despachante solo** | $60.000 | 1 matrícula | Operaciones sin tope, 1 usuario |
| **Estudio** | $150.000 | 2–5 personas | Sin tope, 5 usuarios, memoria compartida |
| **Corporativo** | desde $400.000 | Estudios grandes / importadores | Sin tope, usuarios ilimitados, API |

Razones:

- **Sacar el tope** elimina el peor mensaje del producto ("pagaste y no podés
  trabajar") y multiplica el ingreso del mejor cliente.
- **$60.000 sigue siendo menos que UNA operación** de las que él cobra. Ese
  es el argumento de venta, y no cambia aunque subamos el precio.
- Sube el ticket ~33% en el plan de entrada y abre 3x y 8x arriba, sin tocar
  el producto.

**Antes de tocar precios: preguntarles a los 5 clientes actuales cuántas
operaciones hacen por mes.** Si el promedio es 8, el tope no molesta y me
equivoco. Si es 40, el tope nos está costando plata todos los meses. **Ese
dato lo tenemos en la base y nadie lo miró.**

---

## 4. Valuación: a cuánto lo vendería

### Lo que dice el plan actual

`goldenplan.md` apunta a **$50.000 USD**, partiendo de 5 usuarios y **$150
USD de ingreso mensual**.

### Mi número, honesto

| Enfoque | Resultado |
|---|---|
| Múltiplo SaaS normal (3–5× ingreso anual) | **$5.000 – $9.000 USD** |
| Costo de reposición ("build vs buy") | $30.000 USD *si el comprador acepta ese marco* |
| **Comprador estratégico, hoy** | **$10.000 – $18.000 USD** |
| Objetivo del goldenplan | $50.000 USD |

**Para llegar a $50.000 USD hace falta llegar a $1.000–1.500 USD de ingreso
mensual**, o sea unos **30 a 50 clientes pagando**. Con los precios que
propongo arriba, son ~20–25 clientes. Eso es el trabajo real. No hay atajo de
narrativa que lo reemplace.

### El activo más valioso no está en el goldenplan

El plan valora el motor de cálculo y el scraping. Yo valoro más otra cosa:

> **El formato del TXT, validado contra archivos reales y blindado con
> pruebas.**

Es lo que a un comprador le cuesta meses reproducir, porque **la
especificación de la Interfaz Despachantes del Kit María no es pública** — lo
comprobé buscando: `CARTUSO`, `CARTSBITEM`, `LDDTNOMFOD` no aparecen
documentados en ningún lado. Se aprende con archivos reales y con
despachantes, no leyendo un manual.

Eso sí es un foso. El scraping, no: lo copia cualquiera con tiempo.

---

## 5. Ataque contra este análisis

### 🔴 "No verificaste un solo precio de la competencia"

**Cierto, y es la debilidad más grande de todo esto.** Ninguno publica
precios y no pude abrir sus sitios. Todo lo que digo sobre lo que cobran es
inferencia.

**Cómo se arregla en una tarde, sin programar:** pedirle a tres colegas
despachantes qué pagan hoy de abono. Tres llamadas valen más que este
documento entero.

### 🔴 "El goldenplan apuesta la valuación al Pilar B — que está roto"

Encontré esto en mi propia sesión y no puedo callarlo:

> El **Pilar B (presupuestos compartibles)** es uno de los tres pilares con
> los que el plan justifica el salto a $50.000 USD.
>
> **`tests/test_pilar_b_quotes.py` tiene 6 pruebas en rojo, hoy.**

Estaban tapadas por el cuelgue de la suite. No sé si la funcionalidad no
anda o si las pruebas quedaron viejas — **pero no se puede vender como activo
algo que no sabemos si funciona.** Es lo primero que revisaría un comprador
técnico.

### 🔴 "5 usuarios no es product-market fit"

El goldenplan dice que 5 despachantes pagando *"demuestra que la barrera de
confianza fue vulnerada"*. Cinco personas demuestran que cinco personas
dijeron que sí. Es una señal linda y no es PMF. Un comprador serio va a pedir
retención por cohorte, y el propio `HANDOFF` la tiene pendiente.

### 🔴 "Estás recomendando subir precios de un producto al 70%"

**El reproche más fuerte contra mí.** Yo misma dije ayer que el producto está
al 70% en correctitud del TXT, y ahora propongo subir el precio 33%.

**Mi respuesta:** el precio no se sube por lo que el producto es hoy, sino
por lo que vale para quien lo usa — y ahí el tope de 15 operaciones ya está
mal calibrado. Pero **el orden importa**: primero que un TXT nuestro entre en
el Kit María real, después se toca la lista de precios. Subir el precio de
algo que todavía no se validó punta a punta es la forma más rápida de perder
los 5 clientes que hay.

---

## 6. Qué haría, en orden

1. **Tres llamadas** a colegas despachantes: qué pagan hoy, cuántas
   operaciones hacen por mes. Sin eso, todo lo de arriba es opinión.
2. **Mirar en nuestra propia base** cuántas operaciones hace cada uno de los
   5 clientes. El dato está y nadie lo miró.
3. **Revisar el Pilar B** — 6 pruebas en rojo sobre un activo de valuación.
4. **Validar un TXT en el Kit María real.**
5. Recién ahí, tocar precios.
