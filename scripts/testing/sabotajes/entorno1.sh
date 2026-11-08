#!/usr/bin/env bash
# Negativos de ENTORNO-1: cada sabotaje vuelve a abrir una puerta de desarrollo
# con ENVIRONMENT ausente o desconocido, y tests/test_entorno1.py tiene que
# fallar por esa puerta. El último cierra todas en desarrollo y tiene que
# fallar el contrapunto.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entorno1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
source "$(dirname "$0")/_entorno_comun.sh"
CF=proyecto_maria/config.py

# Cada puerta vuelve a la condición vieja: abierta salvo con «production».
sabotaje $M "usuarios demo salvo en producción" \
  $'            if not _es_desarrollo():\n                demo_users = []' \
  $'            if IS_PRODUCTION:\n                demo_users = []' \
  "$C[demo]" "demo $VIEJO"
sabotaje $M "login con la contraseña guardada salvo en producción" \
  'if not is_valid and _es_desarrollo() and stored_password == password:' \
  'if not is_valid and not IS_PRODUCTION and stored_password == password:' \
  "$C[login_con_lo_guardado]" "login_con_lo_guardado $VIEJO"
sabotaje $M "webhook sin secreto acepta salvo en producción" \
  $'    if not MP_WEBHOOK_SECRET:\n        return _es_desarrollo()' \
  $'    if not MP_WEBHOOK_SECRET:\n        return not IS_PRODUCTION' \
  "$C[webhook_sin_secreto]" "webhook_sin_secreto $VIEJO"
sabotaje $M "link de reset por consola salvo en producción" \
  $'        if not _es_desarrollo():\n            logging.warning("SMTP no configurado' \
  $'        if IS_PRODUCTION:\n            logging.warning("SMTP no configurado' \
  "$C[link_de_reset_en_stdout]" "link_de_reset_en_stdout $VIEJO"
sabotaje $M "cobro simulado salvo en producción" \
  $'    if not _es_desarrollo():\n        raise HTTPException(status_code=404, detail="Not Found")\n\n    result = await db.execute(select(User).where(User.username == user["username"]))' \
  $'    if IS_PRODUCTION:\n        raise HTTPException(status_code=404, detail="Not Found")\n\n    result = await db.execute(select(User).where(User.username == user["username"]))' \
  "$C[cobro_simulado]" "cobro_simulado $VIEJO"
sabotaje $M "clave JWT de desarrollo salvo en producción" \
  'if not _es_desarrollo() and (_is_default_key' 'if IS_PRODUCTION and (_is_default_key' \
  "$C[clave_jwt_de_desarrollo]" "clave_jwt_de_desarrollo $VIEJO"

# El lugar único: sin mirar mayúsculas ni espacios, o con un valor más.
sabotaje $CF "desarrollo sin mirar mayúsculas ni espacios" \
  'return os.getenv("ENVIRONMENT") in ("development", "test", "testing")' \
  'return (os.getenv("ENVIRONMENT") or "").strip().lower() in ("development", "test", "testing")' \
  "$C[demo]" "$C[cobro_simulado]" "cobro_simulado no queda cerrada: {'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}"
sabotaje $CF "staging cuenta como desarrollo" \
  'in ("development", "test", "testing")' 'in ("development", "test", "testing", "staging")' \
  "$C[webhook_sin_secreto]" "webhook_sin_secreto no queda cerrada: {'staging': 'abierta'}"
sabotaje $CF "variable ausente cuenta como desarrollo" \
  'return os.getenv("ENVIRONMENT") in' 'return os.getenv("ENVIRONMENT", "development") in' \
  "$C[login_con_lo_guardado]" "login_con_lo_guardado no queda cerrada: {None: 'abierta'}"

# Contrapunto: si las puertas no abren en ningún lado, la prueba lo ve.
sabotaje $CF "ninguna puerta abre ni en desarrollo" \
  'return os.getenv("ENVIRONMENT") in ("development", "test", "testing")' 'return False' \
  "FAILED $T::test_puerta_abierta_en_desarrollo[demo]" \
  "FAILED $T::test_puerta_abierta_en_desarrollo[cobro_simulado]" \
  "demo no queda abierta: {'development': 'cerrada', 'test': 'cerrada', 'testing': 'cerrada'}"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
