# Sincronizar CDI (vuce) → repo de Railway

## El problema

Estuve trabajando en `/Users/Emi/Desktop/CDI (vuce)` pero ese folder NO es
un repo git. El repo conectado a GitHub (`Memu007/CDI`) y a Railway esta en
`/Users/Emi/CDI`.

Los dos divergen:

| Archivo | Desktop (yo) | /Users/Emi/CDI (Railway) |
|---|---:|---:|
| `proyecto_maria/main.py` | 168 KB | 153 KB |
| `proyecto_maria/templates/landing.html` | 28 KB | 56 KB |
| `proyecto_maria/templates/dashboard_v2.html` | 68 KB | 64 KB |
| `proyecto_maria/static/v2/app_v2.css` | 110 KB | 104 KB |
| `proyecto_maria/static/v2/landing.css` | existe | NO existe |

Ademas `/Users/Emi/CDI` tiene cambios sin commitear desde antes de hoy:

```
 M proyecto_maria/main.py
 M proyecto_maria/static/v2/app_v2.css
 M proyecto_maria/static/v2/app_v2.js
 M proyecto_maria/static/v2/screens/clientes.js
 M proyecto_maria/static/v2/screens/review.js
 M proyecto_maria/static/v2/topbar_financials.js
 M proyecto_maria/templates/dashboard_v2.html
```

Ultimo commit pusheado a Railway: 2026-04-21 (`feat(p4): Tarifar/VUCE
reales - source propagado, latencia y /api/system/connectors`).

## Por que no hice el push solo

Sobrescribir cualquiera de los dos lados puede destruir trabajo:

- Si copio "Desktop -> CDI" piso los cambios sin commitear de CDI
  (si es trabajo tuyo o de otra sesion mia, se pierde).
- Si pusheo CDI tal cual, va sin todo lo de hoy (banner beta,
  empty states, errores amigables, copy del pago, etc).

## Opciones (elegi una y avisame)

### Opcion A — "Confio en lo de hoy, lo de CDI sin commitear no me importa"
Pisar `/Users/Emi/CDI` con el contenido de `Desktop/CDI (vuce)` y pushear.
Es lo mas rapido y seguro respecto a los cambios de hoy, pero perdes los
cambios sin commit del repo CDI.

```bash
# Yo lo hago si me confirmas A
rsync -av --delete \
  --exclude='.git' --exclude='.env' --exclude='*.db' --exclude='__pycache__' \
  --exclude='.pytest_cache' --exclude='.coverage' --exclude='.firebase' \
  "/Users/Emi/Desktop/CDI (vuce)/" /Users/Emi/CDI/
cd /Users/Emi/CDI
git add -A
git commit -m "feat(beta): MVP lanzable en Railway - banner beta, empty states, errores amigables, pago simulado polish"
git push origin main
```

### Opcion B — "Mira primero que perderia si vamos por A"
Reviso los cambios sin commitear de CDI archivo por archivo y los
intento mergear con lo de hoy.

### Opcion C — Hacer el push manual vos
Te dejo lo de hoy aplicado en CDI (sin pushear) y vos revisas con tu
herramienta favorita, hacemos commit + push juntos.

### Opcion D — "Cambiamos el remote del Desktop"
En `/Users/Emi/Desktop/CDI (vuce)` hacer `git init` + agregar remote
+ rebase con CDI. Mas trabajo, pero unifica los dos folders. No lo
recomiendo si es para una beta esta noche.

## Mi recomendacion (PM)

**Opcion A**, porque:

1. Los cambios sin commit del repo CDI son de hace >1 dia (estan en el
   `git status` desde antes que empezaramos hoy).
2. Si esos cambios eran importantes ya los habrias commiteado.
3. Tenemos un deadline de 24h para mostrar al amigo. Mergear archivo por
   archivo nos puede quemar 1-2h sin valor visible.

Si elegis A, en el siguiente mensaje me decis "dale A" y lo hago en un
solo paso (sync + commit + push). Mientras Railway buildea (~3-5 min),
verificamos en logs.

## Despues del push

Independiente de la opcion:

1. **Adjuntar Postgres** al servicio backend (ver `RAILWAY_SETUP.md` paso 1).
2. **Setear las env vars** del bloque del paso 2 de `RAILWAY_SETUP.md`.
3. **Generar dominio** en Settings -> Networking -> Generate Domain.
4. **Re-actualizar** `FRONTEND_URL` y `ALLOWED_ORIGINS` con la URL real.
5. **Verificar** `curl https://TU-SUBDOMINIO.up.railway.app/health` -> 200.
6. **Probar el flow** completo en incognito (alta + cliente + PDF + memoria).
