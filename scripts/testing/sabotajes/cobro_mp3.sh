#!/usr/bin/env bash
# Negativos de COBRO-MP-3: cada sabotaje deshace una regla de la pieza y
# tests/test_cobro_mp3.py (Mercado Pago simulado) tiene que fallar en el caso
# de esa regla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cobro_mp3.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos, y nada sale a Mercado Pago. El timeout del SDK
# (billing_service.sdk_mp) no tiene prueba: el SDK simulado no espera.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local archivo="$1" nombre="$2" esperado="$3"; shift 3
  git checkout -q -- proyecto_maria/
  rm -f test.db
  if ! "$PY" - "$archivo" "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

T=tests/test_cobro_mp3.py
M=proyecto_maria/main.py
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov --timeout=120 -p no:cacheprovider -W ignore "$T" 2>&1; }

rm -f test.db
git checkout -q -- proyecto_maria/
if ! correr >/dev/null; then
  echo "BASE  | $T ya está en rojo: no se puede medir"; exit 1
fi
echo "BASE  | $T en verde"

TRABADO="FAILED $T::test_un_mercado_pago_trabado_no_frena_el_servidor"
sabotaje $M "Mercado Pago se consulta en el hilo del servidor" "$TRABADO" \
  "    return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kw), limiter=_HILOS_MP)" \
  "    return fn(*args, **kw)"
sabotaje $M "las consultas a Mercado Pago usan los hilos de todo el servidor" "$TRABADO" \
  "    return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kw), limiter=_HILOS_MP)" \
  "    return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kw))"
sabotaje $M "el pago de un aviso se consulta fuera del hilo" "$TRABADO" \
  '        pay_resp = await _en_hilo_mp(_consultar_mp, lambda: sdk.payment().get(payment_id), f"pago {payment_id}")' \
  '        pay_resp = _consultar_mp(lambda: sdk.payment().get(payment_id), f"pago {payment_id}")'
sabotaje $M "la recarga crea el cobro fuera del hilo" "$TRABADO" \
  "        checkout = await _en_hilo_mp(billing_service.create_topup_checkout, db_user," \
  "        checkout = (billing_service.create_topup_checkout)(db_user,"
sabotaje $M "el checkout crea la suscripción fuera del hilo" "$TRABADO" \
  "        checkout = await _en_hilo_mp(billing_service.create_checkout, db_user, plan_id, org_id=org_id)" \
  "        checkout = billing_service.create_checkout(db_user, plan_id, org_id=org_id)"

LIMITE="FAILED $T::test_el_aviso_de_pago_tiene_limite_de_pedidos"
CUENTA=$'        if limiter.enabled and not limiter.limiter.hit(_LIMITE_AVISOS_MP, "aviso_mp", get_client_ip(request)):\n            raise HTTPException(status_code=429, detail="Demasiados avisos")\n'
sabotaje $M "el aviso de pago sin límite de pedidos" "$LIMITE" "$CUENTA" ""
sabotaje $M "el límite cuenta también los avisos sin firma" "$LIMITE" "$CUENTA" "" \
  $'@app.post("/api/payments/webhook")\n' $'@app.post("/api/payments/webhook")\n@limiter.limit("60/minute")\n'

SIN_FIRMA="FAILED $T::test_un_aviso_sin_firma_verificable_no_cambia_nada"
sabotaje $M "sin clave, en desarrollo, el aviso pasa sin verificar" "${SIN_FIRMA}[sin-secreto-dev]" \
  $'    if not MP_WEBHOOK_SECRET:\n        return False' \
  $'    if not MP_WEBHOOK_SECRET:\n        return not IS_PRODUCTION'
sabotaje $M "se atiende un IPN por la URL, sin firma" "('ipn', 200" \
  "        if not _verify_mp_webhook_signature(request, raw_body):" \
  "        if request.query_params.get(\"topic\"):
            raw_body = json.dumps({\"type\": request.query_params[\"topic\"],
                                   \"data\": {\"id\": request.query_params.get(\"id\")}}).encode()
        elif not _verify_mp_webhook_signature(request, raw_body):"
sabotaje $M "un cuerpo que no es un objeto rompe la verificación" "'cuerpo que no es un objeto'" \
  "    data = body.get(\"data\") if isinstance(body, dict) else None" \
  "    data = body.get(\"data\")"
sabotaje $M "un data que no es un objeto rompe la verificación" "'data que no es un objeto'" \
  "    data_id = str(data.get(\"id\", \"\")) if isinstance(data, dict) else \"\"" \
  "    data_id = str(data.get(\"id\", \"\")) if data else \"\""
sabotaje $M "la firma se compara como texto" "'firma con letras no ascii'" \
  "    return _hmac.compare_digest(expected.encode(), received_v1.encode())" \
  "    return _hmac.compare_digest(expected, received_v1)"

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
