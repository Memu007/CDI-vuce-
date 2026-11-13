#!/usr/bin/env bash
# Levanta un Postgres 16 descartable, sólo en 127.0.0.1 y con clave, corre el
# comando con BACKUP1A_PG_URL apuntando a él y lo borra al terminar. La clave
# es sintética, de esta corrida, y tiene caracteres que en una URL se escapan.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/con_pg16.sh <comando...>
#      (PG16_BIN cambia la carpeta de los binarios; por defecto la de Ubuntu)
# Sale con el código del comando, o 3 si el Postgres no levantó.
set -uo pipefail
BIN="${PG16_BIN:-/usr/lib/postgresql/16/bin}"
PY="${PY:-python3}"
[ "$#" -gt 0 ] || { echo "uso: $0 <comando...>" >&2; exit 2; }
"$BIN/postgres" --version | grep -q ' 16\.' || { echo "no hay Postgres 16 en $BIN" >&2; exit 3; }

DIR="$(mktemp -d /tmp/cdi-pg16.XXXXXX)"
como_pg() {
  if [ "$(id -u)" -eq 0 ]; then runuser -u postgres -- "$@"; else "$@"; fi
}
cerrar() {
  como_pg "$BIN/pg_ctl" -D "$DIR/data" -m fast -w stop >/dev/null 2>&1
  case "$DIR" in /tmp/cdi-pg16.??????) rm -rf -- "$DIR" ;; esac
}
trap cerrar EXIT
[ "$(id -u)" -eq 0 ] && chown postgres "$DIR"

PG_PUERTO="$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
CLAVE="$("$PY" -c 'import secrets; print(secrets.token_urlsafe(12) + " :@%/;ñ")')"
URL="$("$PY" -c 'import sys, urllib.parse as u; print(f"postgresql://cdi:{u.quote(sys.argv[1], safe=str())}@127.0.0.1:{sys.argv[2]}/postgres")' "$CLAVE" "$PG_PUERTO")"

printf '%s\n' "$CLAVE" > "$DIR/clave"
[ "$(id -u)" -eq 0 ] && chown postgres "$DIR/clave"
como_pg "$BIN/initdb" -D "$DIR/data" -U cdi --auth=scram-sha-256 --pwfile="$DIR/clave" \
  --encoding=UTF8 --locale=C.UTF-8 >"$DIR/initdb.log" 2>&1 || { cat "$DIR/initdb.log" >&2; exit 3; }
rm -f -- "$DIR/clave"
como_pg "$BIN/pg_ctl" -D "$DIR/data" -l "$DIR/pg.log" -w \
  -o "-p $PG_PUERTO -k $DIR -c listen_addresses=127.0.0.1" start >/dev/null || { cat "$DIR/pg.log" >&2; exit 3; }

BACKUP1A_PG_URL="$URL" PG16_BIN="$BIN" "$@"
