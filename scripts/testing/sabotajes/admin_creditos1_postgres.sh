#!/usr/bin/env bash
# Negativos en Postgres 16 de la carga de créditos desde el panel de admin
# (scripts/testing/admin_creditos1_postgres.py): cada sabotaje deshace la parte
# que sostiene dos pedidos a la vez y exige la fila MAL que la mira.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/admin_creditos1_postgres.sh [SHA]
# Trabaja en un worktree descartable y levanta su propio Postgres 16 con
# scripts/testing/con_pg16.sh. Sale con error si una corrida no da lo esperado.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
# Relativo, dejaría de valer después del cd al worktree.
case "$PY" in */*) PY="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")";; esac
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT"
FALLAS=0
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test

mal() { echo "MAL   | $1"; tail -25 <<<"$2"; FALLAS=$((FALLAS+1)); }

# creditos <nombre> <salida esperada> <texto>...: la corrida tiene que tener cada texto.
creditos() {
  local nombre="$1" esperada="$2" salida codigo texto; shift 2
  salida="$(PY="$PY" scripts/testing/con_pg16.sh "$PY" scripts/testing/admin_creditos1_postgres.py 2>&1)"; codigo=$?
  for texto in "$@"; do
    if [ "$codigo" -ne "$esperada" ] || ! grep -qF -- "$texto" <<<"$salida"; then
      mal "$nombre: salida $codigo, esperaba $esperada y «$texto»" "$salida"; return
    fi
  done
  echo "BIEN  | $nombre: salida $codigo, $(grep -c '^MAL' <<<"$salida") filas MAL"
  grep '^MAL' <<<"$salida" | sed 's/^/        /'
}

# en_codigo <archivo> <viejo> <nuevo>...: cambia el producto; lo deshace la
# llamada siguiente o el final del script.
en_codigo() {
  git checkout -q -- proyecto_maria
  "$PY" - "$@" <<'PYEOF' || { echo "PATRÓN | $2"; FALLAS=$((FALLAS+1)); return 1; }
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
for viejo, nuevo in zip(sys.argv[2::2], sys.argv[3::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez: {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

R=proyecto_maria/routers/admin_router.py
MO=proyecto_maria/database/models.py
DOS="MAL | el mismo pedido para dos cuentas"

creditos "sin sabotaje" 0 "filas MAL: 0; rondas sin armar: 0"

# El segundo insert con el mismo pedido choca con la clave y la ruta lo atrapa.
en_codigo "$R" '        try:
            await db.commit()
        except IntegrityError:
            # Otro pedido con la misma clave entró primero: se deshace lo sumado y se responde con el suyo.
            await db.rollback()
            previa, ya = await db.get(CreditoAdmin, carga.pedido), True' '        await db.commit()' &&
  creditos "sin atrapar el choque de la clave" 1 "$DOS" "[200, 500]"
# La clave del pedido es la que hace chocar al segundo: sin ella entran los dos.
en_codigo "$MO" '    pedido = Column(String(36), primary_key=True)' '    pedido = Column(String(36))
    __mapper_args__ = {"primary_key": [pedido]}' &&
  creditos "el pedido sin clave en la tabla" 1 "$DOS" "[200, 200]"
# Sin candado, la carga que espera detrás de la recarga escribe lo que leyó antes y la pisa.
en_codigo "$R" '    bloqueada = await cuenta_bloqueada(db, username)' \
  '    db_user = (await db.execute(select(User).where(User.username == username))).scalars().first()
    org = db_user and db_user.organization_id and await db.get(Organization, db_user.organization_id)
    bloqueada = db_user and (db_user, org or db_user)' &&
  creditos "la carga sin candado" 1 "MAL | recarga + carga | usuario | créditos vencidos" "MAL | recarga + carga | org | créditos al día"
# Sin candado en la cuenta, la carga y el guardado que van detrás leen lo mismo y uno pisa al otro.
C=proyecto_maria/database/candados.py
en_codigo "$C" '        .with_for_update(key_share=True, of=User)
' '' '            .with_for_update(key_share=True, of=Organization)
' '' &&
  creditos "la cuenta sin candado" 1 "MAL | carga + guardado | usuario" "MAL | carga + guardado | org"
# Sin candado en la recarga, lee antes de que la carga que espera delante escriba y la pisa.
en_codigo proyecto_maria/main.py 'cuenta = (await session.execute(consulta.with_for_update())).scalars().first()' \
  'cuenta = (await session.execute(consulta)).scalars().first()' &&
  creditos "la recarga sin candado" 1 "MAL | carga + recarga | usuario" "MAL | carga + recarga | org"
# El reintento del mismo pedido lo frenan dos cosas: se busca con la cuenta bloqueada y, si
# igual entra, choca con la clave. Sin buscarlo ni atrapar el choque, el segundo da 500.
en_codigo "$R" '    previa = await db.get(CreditoAdmin, carga.pedido)
    ya = previa is not None' '    previa = None
    ya = previa is not None' '        try:
            await db.commit()
        except IntegrityError:
            # Otro pedido con la misma clave entró primero: se deshace lo sumado y se responde con el suyo.
            await db.rollback()
            previa, ya = await db.get(CreditoAdmin, carga.pedido), True' '        await db.commit()' &&
  creditos "la ruta no reconoce el pedido repetido" 1 "MAL | el mismo pedido dos veces, usuario" "MAL | el mismo pedido dos veces, org"
# Cada arranque crea sólo lo que falta: con las demás tablas ya creadas, crearlas de nuevo choca.
en_codigo proyecto_maria/database/connection.py 'Base.metadata.create_all, checkfirst=True' 'Base.metadata.create_all, checkfirst=False' &&
  creditos "el arranque crea tablas que ya existen" 1 "MAL | el primer arranque falla"
# Sólo la tabla de cargas sin checkfirst: el primer arranque la crea y el segundo choca.
CREAR='        await conn.run_sync(Base.metadata.create_all, checkfirst=True)'
en_codigo proyecto_maria/database/connection.py "$CREAR" \
  '        await conn.run_sync(Base.metadata.create_all, tables=[t for t in Base.metadata.sorted_tables if t.name != "creditos_admin"])
        await conn.run_sync(Base.metadata.tables["creditos_admin"].create)' &&
  creditos "la tabla de cargas se crea sin mirar si existe" 1 "MAL | el segundo arranque falla"
# El arranque no puede tocar las otras tablas ni dejar cargas.
en_codigo proyecto_maria/database/connection.py "$CREAR" "$CREAR
        await conn.execute(text(\"update users set roles = '[]'\"))" &&
  creditos "el arranque cambia otra tabla" 1 "MAL | migración: creditos_admin con 0 filas" "public.users: el contenido no coincide"
en_codigo proyecto_maria/database/connection.py "$CREAR" "$CREAR
        await conn.execute(text(\"insert into creditos_admin (pedido, admin, cuenta, usuario, cantidad, vigentes_antes) values (gen_random_uuid()::text, 'a', 'a', 'a', 1, 0)\"))" &&
  creditos "el arranque deja cargas" 1 "MAL | migración: creditos_admin con 2 filas"
git checkout -q -- proyecto_maria
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
