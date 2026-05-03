# PLAYBOOK DEL PROYECTO

Este documento fija reglas simples de trabajo, define responsabilidades y mantiene un registro vivo de decisiones y acciones. Debe leerse primero antes de proponer cambios grandes.

## Checklist: Antes de tocar código
- ¿Objetivo en 1 línea y criterio de aceptación definidos?
- ¿Solución más simple posible (sin overengineering)?
- ¿Impacta valor real para el usuario que no programa?
- ¿Hace falta test mínimo (pytest/curl) para validar?
- ¿Actualizarás este PLAYBOOK/README al finalizar?

## Reglas del proyecto
- Simplicidad primero: sin overengineering. Opción más simple que cumpla con calidad.
- El usuario NO programa: interfaces y scripts deben ser claros y reproducibles.
- Evitar bucles manuales: automatizar tareas repetitivas con scripts simples.
- Stack mínimo: FastAPI + HTML/CSS/JS plano, persistencia JSON/SQLite si hace falta.
- Tests cuando aporten valor: validar flujos críticos (pytest) y endpoints clave.
- Código limpio: nombres claros, funciones cortas, early return, poca anidación.
- Documentar lo necesario: README y este PLAYBOOK actualizados.

## Roles y cómo operamos
- Full‑stack senior “on demand”: actuar como especialista en backend, frontend, datos o DevOps cuando se requiera.
- Equipo externo cuando haga falta: si una tarea excede 1-2 días o requiere expertise legal/AFIP/RPA → recomendar armado de equipo y dividir entregables.
- Criterio de corte: si una solución agrega complejidad sin beneficio directo al usuario final, se descarta.
 - Revisor Técnico (QA/Tech Lead): valida criterio/objetivo, contrato de API, tests y simplicidad. Aprueba o pide cambios.

## Flujo de trabajo
1) Definir objetivo y criterio de aceptación (1 línea).
2) Implementar la versión más simple posible.
3) Probar con pytest/curl o flujo manual corto.
4) Documentar en este archivo y en README si aplica.
5) Planificar el siguiente paso (máx. 3 bullets).

## Guía rápida de decisiones
- ¿Agregar una librería nueva? Solo si impacta directo en valor/tiempo.
- ¿Nueva base de datos? Empezar con JSON/CSV. Migrar si es requisito.
- ¿Feature premium? No romper MVP; detrás de rutas/flags claras.
- ¿Rendimiento? Optimizar lo que el usuario percibe (debounce, cargas perezosas).

## Rol: Revisor Técnico (QA/Tech Lead)

- Responsabilidades
  - Confirmar objetivo y criterio de aceptación de cada cambio.
  - Verificar contrato de API (JSON con `success`, `detail`, rutas con y sin barra, validaciones de negocio con `success=false`).
  - Asegurar consistencia con tests y agregar/ajustar cuando cambie un contrato o regla.
  - Velar por simplicidad: evitar frameworks/abstracciones innecesarias.
  - Revisar nombres claros, early returns y manejo de errores con contexto (sin silencios).
  - Confirmar `DATA_DIR`, descargas y rutas de salida (`data/generated/`).
  - Exigir documentación mínima (README/PLAYBOOK) ante cambios relevantes.

- Checklist de revisión (pre-merge)
  - [ ] Objetivo y criterio en 1 línea al inicio del cambio
  - [ ] Contrato API respetado (JSON estándar, rutas, errores)
  - [ ] Tests actualizados o añadidos si aplica; `python3 -m pytest -q tests` verdes
  - [ ] Validaciones críticas cubiertas con mensajes “humanos” en UI/servidor
  - [ ] Sin overengineering; código claro y corto; sin capturas vacías
  - [ ] Scripts/README/PLAYBOOK actualizados si hubo impacto operativo
  - [ ] Sin romper MVP; premium detrás de UI/flags sin afectar básico

- Cuándo pedir revisión externa (Claude 4.1)
  - Cambios de contrato, reglas de validación sensibles, rendimiento o decisiones no triviales.
  - Prompt sugerido:
```text
Rol: Revisor Técnico. Objetivo (1 línea): <...>. Cambios: <resumen>. Muestra: <diff/fragmentos>.
Pedir: 1) riesgos/regresiones, 2) mejoras mínimas, 3) ok/no‑ok con razones.
Máx 250 palabras.
```

### Revisor técnico por defecto

- Revisor: Emi (Owner del proyecto)
- Alternativa: Asistente IA con rol de “Revisor Técnico” cuando Emi no esté disponible.
- Cada cambio deberá incluir: objetivo/criterio en 1 línea y enlace al diff.

## Registro vivo (changelog operativo)
- 2025-09-21: Unificado servidor con `server_funcional`, tests verdes (47).
- 2025-09-21: README “Cómo ejecutar” y “Cómo usar (2 minutos)”.
- 2025-09-21: Debounce en agrupación, aviso >100 ítems (premium/basic).
- 2025-09-21: Preferencias UI persistidas (auto agrupar, cliente, modo).
- 2025-09-21: Endpoint `POST /validate_items/` + test de integración.
- 2025-09-21: Panel de validación en UI (resumen, auto-validar, CSV) y mensajes humanos.

## Próximos pasos sugeridos
- Botón “Validar” en pantalla de agrupación que use `/validate_items/` y muestre errores.
- Exportación simple de historial por cliente (CSV ya expuesto, mejorar UI).
- Script de copia de seguridad diaria de `data/` (cron/manual).

## Mantenimiento
- Mantener este PLAYBOOK sincronizado con cambios relevantes.
- Si una decisión contradice estas reglas, justificar en una línea en el registro vivo.

## Checklist de producción mínima

- Entorno
  - Python 3.11 instalado.
  - Dependencias: `pip install -r requirements.txt`.
  - Variables: `DATA_DIR` (por defecto `data/`).
- Directorios y permisos
  - Crear: `data/`, `data/generated/`, `data/uploads/`, `data/logs/`.
  - Asegurar escritura del usuario que ejecuta el servicio.
- Arranque simple
  - Desarrollo: `./dev.sh` (recarga automática).
  - Producción: `./prod.sh` (sin recarga).
  - Opcional (background): `nohup ./prod.sh >> data/logs/app.log 2>&1 &`.
- Logs básicos
  - Uvicorn escribe a stdout; redirigir a `data/logs/app.log` si corre en background.
  - Rotación manual sencilla: copiar y truncar archivo semanalmente si crece mucho.
  - Script de rotación opcional: `./rotate_logs.sh` (5MB por defecto), puede correrse con cron.
- Verificación rápida
  - Salud: `curl http://127.0.0.1:8001/health` → debe devolver `{ status: "ok", ... }`.
  - Flujo: ejecutar `python ejemplo_uso.py` y comprobar archivo en `data/generated/`.
- Backups
  - Manual: `python3 backup_data.py`.
  - Programado: ver cron de ejemplo en `README.md`.
- Seguridad mínima
  - No exponer públicamente sin proxy/restricciones (nginx, firewall).
  - Mantener `--reload` desactivado en producción.

### Deploy sugerido (Nginx + systemd)

1) Variables de entorno: copiar `.env.example` a `.env` y ajustar `DATA_DIR`, `UVICORN_HOST`, `UVICORN_PORT`.
2) Servicio systemd (`/etc/systemd/system/caca.service`):
```ini
[Unit]
Description=CACA - Optimizador MARIA
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/caca
EnvironmentFile=/opt/caca/.env
ExecStart=/usr/bin/bash -lc '/opt/caca/prod.sh'
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
3) Nginx (proxy inverso):
```nginx
server {
    listen 80;
    server_name ejemplo.tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
4) Activar y monitorear:
```bash
sudo systemctl daemon-reload
sudo systemctl enable caca
sudo systemctl start caca
sudo systemctl status caca
```
5) Logs:
```bash
journalctl -u caca -f
```
