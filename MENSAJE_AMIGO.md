# Mensaje para el despachante amigo (beta cerrada)

Plantilla lista para mandar por WhatsApp / mail. Reemplaza los `{{...}}`
antes de enviar.

---

## Version corta (WhatsApp)

> Hola {{nombre}}! Estoy probando una herramienta nueva para automatizar
> la carga de operaciones en MARIA. Toma el PDF de la factura del
> proveedor, extrae los items, te sugiere el NCM contra VUCE, y te
> arma el TXT para pegar.
>
> Esta en beta cerrada y queria que vos seas uno de los primeros en
> verla. Te paso el link y te aviso un par de cosas:
>
> Link: {{URL_RAILWAY}}
>
> Como entrar:
> 1. Crea una cuenta con tu mail.
> 2. En el formulario te va a pedir tarjeta — es de mentira. Hace
>    click en "usar tarjeta de prueba" y completa solo. No se cobra
>    nada, no me llega ningun dato real tuyo de pago.
>
> Que SI funciona:
> - Subir PDF de factura del proveedor
> - Sugerencias de NCM y deteccion de intervenciones (ANMAT, ENACOM,
>   etc) contra VUCE
> - Memoria por cliente (la segunda factura del mismo importador ya
>   te sugiere los NCMs de la anterior)
> - Generar el TXT para MARIA
>
> Que NO funciona todavia:
> - Pagos reales (todo es simulado)
> - Mails de confirmacion (no llegan)
> - Algunas pantallas pueden estar con datos de demo
>
> Si encontras algo raro o se rompe, mandame screenshot por aca o por
> mail a {{tu_email}}. Cualquier feedback me sirve un monton.
>
> Adjunto un PDF de ejemplo por si no tenes uno a mano para probar.
>
> Gracias!

---

## Version larga (mail formal)

**Asunto:** CDI Despachos - acceso beta cerrada

Hola {{nombre}},

Te escribo porque venimos trabajando con un equipo en una herramienta
para despachantes que automatiza varias tareas tediosas de la carga
en MARIA, y queria que la pruebes vos primero antes de abrirla.

**El acceso:** {{URL_RAILWAY}}

**Que hace la herramienta:**

1. Subis el PDF de la factura comercial del proveedor.
2. Lee los items con IA y los pone en una grilla editable.
3. Te sugiere el NCM correcto, valida contra VUCE, y te avisa si
   alguno requiere intervencion (ANMAT, ENACOM, INPI, etc).
4. Para cada cliente importador guarda la memoria de NCMs que
   usaste antes, asi la segunda operacion del mismo cliente arranca
   casi cargada sola.
5. Te genera el TXT en formato MARIA para pegar directo.

**Como entrar (pasos exactos):**

1. Abri el link arriba.
2. Click en "Ingresar" arriba a la derecha.
3. Tab "Crear cuenta" - completa con tu mail real (uno cualquiera).
4. En la parte de "metodo de pago": **es simulado**. Hace click en
   "usar tarjeta de prueba" y se completa solo. **No se cobra
   absolutamente nada y los datos no se guardan en ningun lado real.**
5. Te logueas automaticamente (no hay confirmacion por mail en
   esta version).
6. Crea un cliente importador (botón arriba a la derecha o en el
   estado vacio).
7. Subi un PDF (te adjunto uno de ejemplo si necesitas).
8. Revisa los items, completa los NCMs faltantes, guarda.
9. Probá subir un segundo PDF del MISMO cliente para ver la magia
   de la memoria (te va a tirar los NCMs en verde).
10. Descarga el TXT para MARIA.

**Que esta funcionando:**

- Lectura de PDF con IA (Gemini)
- Sugerencia y validacion de NCM contra VUCE
- Deteccion de intervenciones por NCM
- Memoria por cliente (lo mas nuevo)
- Generacion del TXT para MARIA
- Multi cliente (cada despachante tiene su espacio aislado)
- Cotizacion del dolar en vivo

**Que NO esta funcionando todavia (saberlo de antemano):**

- Pagos reales (Stripe / MercadoPago) - todo es simulado
- Mails de confirmacion / verificacion
- Catalogo del proveedor se reinicia con cada deploy (limitacion temporal)
- Algunas pantallas de admin pueden estar incompletas
- No esta optimizada para mobile fino

**Como avisarme bugs / feedback:**

- WhatsApp: {{tu_whatsapp}}
- Mail: {{tu_email}}
- Si podes mandar screenshot del error y un audio explicando que
  estabas haciendo, mejor.

Si no funciona algo basico (no carga, error 500, no podes loguearte),
mandame un mensaje y lo arreglo en el dia. Es beta, eso es esperable.

Cualquier feedback (incluso "esto deberia ser un boton mas grande", o
"a mi me gustaria que..."), todo suma.

Muchas gracias por darle una vuelta, te debo un cafe.

Saludos,
{{tu_nombre}}

PD: adjunto un PDF de factura de ejemplo para que pruebes sin
necesidad de buscar uno tuyo.

---

## Checklist antes de mandar

- [ ] Reemplazar `{{nombre}}`, `{{URL_RAILWAY}}`, `{{tu_email}}`,
      `{{tu_whatsapp}}`, `{{tu_nombre}}`.
- [ ] Verificar que la URL responde 200 desde un navegador incognito.
- [ ] Verificar que el flow alta -> cliente -> PDF -> NCM -> TXT
      funciona end-to-end.
- [ ] Adjuntar un PDF de ejemplo (si tenes uno listo).
- [ ] Confirmar que tu mail/WhatsApp esta atento a recibir feedback
      las primeras 24-48hs.
- [ ] Tener Railway logs abiertos en otra pestana mientras el amigo
      prueba (asi cazas un 500 si pasa).

## Que NO incluir en el primer mensaje

- Detalles tecnicos (Postgres, FastAPI, deploy, etc) - no le suma.
- Roadmap a futuro - confunde el foco.
- Pedidos de feedback estructurado tipo "completa este form de 20
  preguntas" - mata la disposicion. Mejor: "contame que pensas".

## Despues que lo pruebe

Pedirle 3 cosas concretas en el follow-up:

1. Que es lo primero que cambiarias.
2. Si te ahorrara tiempo en tu dia a dia, cuanto?
3. Algo que esperabas que estuviera y no encontraste.
