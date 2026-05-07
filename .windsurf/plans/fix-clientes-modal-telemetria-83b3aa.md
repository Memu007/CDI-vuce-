# Plan: modal de eliminar cliente y estabilidad visual

Resumen: mejorar la experiencia de eliminar clientes con un modal propio de la app y reducir falsos errores de consola por telemetría bloqueada.

## Alcance chico recomendado

1. Confirmar el origen del ruido de consola
   - Revisar `CDI.track` en `app_v2.js`.
   - Validar que `ERR_BLOCKED_BY_CLIENT` viene de bloqueador/extensión y no de un fallo funcional.
   - Si hace falta, hacer que la telemetría sea silenciosa cuando el navegador la bloquee.

2. Reemplazar confirmación nativa de eliminar cliente
   - Cambiar `window.confirm` en `clientes.js` por un modal consistente con el diseño existente.
   - Mantener el texto claro: qué cliente se elimina y que no se puede deshacer.
   - Evitar borrar automáticamente sin confirmación explícita.

3. Verificar flujo de clientes
   - Probar eliminar cliente desde listado/detalle.
   - Probar cancelar eliminación.
   - Probar que si el cliente eliminado estaba activo, quede desactivado como hoy.

4. Cierre del cambio
   - Actualizar `CHANGELOG.md`.
   - Actualizar `HANDOFF.md` solo si cambia el estado visible del producto.
   - Hacer commit y push sin force, siguiendo reglas del repo.

## No incluido salvo que aparezca en la prueba

- No tocar backend si no hay error 500 real.
- No cambiar endpoints ni base de datos.
- No desactivar telemetría completa; solo evitar que el bloqueo ensucie o afecte UX.
