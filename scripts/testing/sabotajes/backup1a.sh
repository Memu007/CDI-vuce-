#!/usr/bin/env bash
# Negativos de BACKUP-1a: cada sabotaje rompe una regla de
# scripts/datos/copia_base.py y la prueba de esa regla tiene que fallar por ese
# motivo (tests/test_backup1a.py, con Postgres, y tests/test_backup1a_unidad.py).
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/backup1a.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia. Cada corrida levanta su
# propio Postgres 16 con scripts/testing/con_pg16.sh (un sabotaje que deja bases
# colgadas no ensucia al siguiente). Unos cinco minutos.
# Sale con error si un sabotaje no encuentra su patrón, no pone rojo, el rojo
# no dice lo esperado o alguna prueba se saltea.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0
C=scripts/datos/copia_base.py

# correr <-k>: las pruebas elegidas, con su Postgres.
correr() {
  PY="$PY" scripts/testing/con_pg16.sh "$PY" -m pytest -q --no-cov --timeout=120 -p no:cacheprovider \
    tests/test_backup1a.py tests/test_backup1a_unidad.py -k "$1" 2>&1 | tr -d '\0'
}

# reemplazar <archivo> <viejo> <nuevo>: <viejo> tiene que aparecer una sola vez.
reemplazar() {
  "$PY" - "$@" <<'PYEOF'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

limpiar() {
  git reset -q --hard "$SHA" && git clean -fdq
}

# sabotaje <nombre> <-k> <lo que el rojo tiene que decir> <comando que sabotea...>
# Lo esperado puede ser varios textos separados por «|»: tienen que estar todos.
sabotaje() {
  local nombre="$1" filtro="$2" esperado="$3"; shift 3
  limpiar
  if ! "$@"; then echo "ROTO  | $nombre: el sabotaje no se pudo aplicar"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo falta="" texto
  salida="$(correr "$filtro")"; codigo=$?
  if [ "$codigo" -eq 3 ] || grep -qE "[0-9]+ skipped|no tests ran|[0-9]+ error" <<<"$salida"; then
    echo "ROTO  | $nombre: no corrió entera (salida $codigo)"; tail -3 <<<"$salida"; FALLAS=$((FALLAS+1)); return
  fi
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  IFS='|' read -ra textos <<<"$esperado"
  for texto in "${textos[@]}"; do
    grep -qF -- "$texto" <<<"$salida" || falta="$texto"
  done
  if [ -z "$falta" ]; then
    echo "ROJO  | $nombre: dice «${esperado//|/» y «}»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$falta»"
    grep -E "^E |FAILED" <<<"$salida" | head -4; FALLAS=$((FALLAS+1))
  fi
}

echo "== sin sabotaje"
limpiar
salida="$(correr "")"; codigo=$?
if [ "$codigo" -eq 0 ] && ! grep -qE "[0-9]+ skipped" <<<"$salida"; then
  echo "VERDE | base: $(tail -1 <<<"$salida" | tr -d '=' | sed 's/^ *//; s/ *$//')"
else
  echo "ROJO  | base: las pruebas no pasan enteras sin sabotaje (salida $codigo)"; tail -5 <<<"$salida"; exit 1
fi

echo "== la comparación"
sabotaje "no compara el contenido" "fila_cambiada" "FAILED|copia verificada" \
  reemplazar $C 'elif a["sha256"] != d["sha256"]:' 'elif False:'
sabotaje "no compara las filas" "tabla_vacia" "public.ncm_cache: el contenido no coincide" \
  reemplazar $C 'elif a["filas"] != d["filas"]:' 'elif False:'
sabotaje "sólo mira las tablas de la copia" "tabla_de_mas_o_de_menos" "[CREATE TABLE de_mas|copia verificada" \
  reemplazar $C 'sorted(antes.keys() | despues.keys())' 'sorted(antes.keys())'
sabotaje "sólo mira las tablas restauradas" "tabla_de_mas_o_de_menos" "[DROP TABLE ncm_cache|copia verificada" \
  reemplazar $C 'sorted(antes.keys() | despues.keys())' 'sorted(despues.keys())'
sabotaje "ignora que pg_restore falló" "cortada" "falta en la restauración" \
  reemplazar $C 'if codigo != 0:' 'if False:'
sabotaje "no borra la base de restauración" "todas_las_tablas" "cdi_restauracion_" \
  reemplazar $C "await admin.execute(f'DROP DATABASE IF EXISTS \"{base}\" WITH (FORCE)')" 'pass'
sabotaje "pg_dump no usa el instante de la huella" "escritura_durante" "public.ncm_cache: 3 filas al copiar, 2 al restaurar" \
  reemplazar $C '"--no-password", f"--snapshot={instante}",' '"--no-password",'
sabotaje "la huella usa el orden alfabético de la base" "orden_alfabetico" "public.orden: el contenido no coincide" \
  reemplazar $C 'ROW(t.*)::text COLLATE "C" AS fila' 'ROW(t.*)::text AS fila'
for ajuste in "SET TimeZone TO 'UTC'" "SET DateStyle TO 'ISO, YMD'" "SET IntervalStyle TO 'postgres'" \
              "SET extra_float_digits TO 3" "SET bytea_output TO 'hex'"; do
  sabotaje "la sesión no fija «$ajuste»" "configuracion" "public.tipos_extra: el contenido no coincide" \
    reemplazar $C "    \"$ajuste\",
" ""
done

echo "== la marca de verificada"
sabotaje "verificar no borra la marca vieja" "fila_cambiada" "quedó marcada como verificada" \
  reemplazar $C '    if os.path.lexists(_de_marca(archivo)):
        os.unlink(_de_marca(archivo))
' ''
sabotaje "una copia vacía queda verificada" "copia_vacia" "copia verificada: 0 tablas, 0 filas|copia verificada: 2 tablas, 0 filas" \
  reemplazar $C 'if not filas:' 'if False:'
sabotaje "copiar fija una copia vacía" "copia_vacia" "vuelta 1: quedó algo" \
  reemplazar $C '            _filas(tablas)
' ''
sabotaje "copiar sale bien aunque la verificación falle" "sale_con_error" "LA COPIA NO SIRVE|pg_restore falló (salida 1)" \
  reemplazar $C 'return await verificar(archivo)' 'await verificar(archivo); return 0'
sabotaje "la huella sólo mira public" "otro_esquema" "copia verificada" \
  reemplazar $C "WHERE c.relkind = 'r'" "WHERE c.relkind = 'r' AND n.nspname = 'public'"
sabotaje "una huella que no se entiende llega a la base" "huella_que_no_se_entiende" "falta la variable COPIA_PRUEBA_URL" \
  reemplazar $C 'if not re.fullmatch(r"[A-Z0-9_]+", str(datos.get("codificacion", ""))):' 'if False:'

echo "== un corte"
sabotaje "sin plazo" "un_corte" "copia verificada" \
  reemplazar $C 'loop.call_later(int(plazo), cortar, f"no terminó en {plazo} s")' 'pass'
sabotaje "un plazo que no se entiende corre igual" "plazo_que_no_se_entiende" "no terminó en 0 s|no terminó en -5 s" \
  reemplazar $C 'if not re.fullmatch(r"[0-9]+", plazo) or int(plazo) == 0:' 'if not plazo.lstrip("-").isdigit():'
sabotaje "un plazo con «²» rompe" "plazo_que_no_se_entiende" "ValueError: invalid literal for int()" \
  reemplazar $C 'if not re.fullmatch(r"[0-9]+", plazo) or int(plazo) == 0:' 'if not plazo.isdigit() or int(plazo) == 0:'
sabotaje "la señal mata sin limpiar" "un_corte" "(-15 == 1" \
  reemplazar $C 'loop.add_signal_handler(senal, cortar, f"se cortó por {senal.name} antes de terminar")' 'pass'
sabotaje "una señal ignorada corta igual" "un_corte" "se cortó por SIGHUP" \
  reemplazar $C 'if signal.getsignal(senal) is not signal.SIG_IGN:' 'if True:'
sabotaje "cortar no mata al hijo" "un_corte" "pg_restore quedó corriendo" \
  reemplazar $C '        if proc.returncode is None:
            proc.kill()
            await proc.wait()
' ''

sabotaje "la limpieza no está protegida del corte" "durante_el_borrado" "close']" \
  reemplazar $C 'await asyncio.shield(tarea)' 'await tarea'
sabotaje "el borrado no tiene tope" "colgado" "Timeout" \
  reemplazar $C 'asyncio.wait_for(borrar(), TOPE_BORRADO_S)' 'borrar()'

echo "== no pisar"
# Sin este control, _fijar igual no pisa: el rojo es que falta el aviso de antes de copiar.
sabotaje "copiar no avisa antes de copiar" "no_pisa_una_copia" "'no se pisa una copia' in 'error: ya existe /" \
  reemplazar $C 'raise Falla(f"ya existe {ruta}: no se pisa una copia")' 'pass'
sabotaje "_fijar pisa" "fijar_no_pisa" "DID NOT RAISE" \
  reemplazar $C 'os.link(temporal, ruta)' 'shutil.copyfile(temporal, ruta)'

echo "== la dirección y la clave"
sabotaje "sin COPIA_ORIGEN_URL no lo dice" "direccion_entra" "COPIA_ORIGEN_URL no es una dirección postgresql://" \
  reemplazar $C 'raise Falla(f"falta la variable {variable}")' 'pass'
sabotaje "copia antes de saber dónde probarla" "direccion_entra" "copió sin saber dónde probarla" \
  reemplazar $C '    Direccion("COPIA_PRUEBA_URL")  # que falte se sabe antes de copiar
' ''
sabotaje "argparse repite la dirección" "direccion_entra" "el error repite la clave" \
  reemplazar $C 'message = message.replace(arg, "***")' 'pass'
sabotaje "la clave va en la URL de pg_dump" "clave_no_va_en_los_argumentos" "la clave va en pg_dump" \
  reemplazar $C 'lugar = f"{self.usuario}@{self.servidor}"' 'lugar = f"{self.usuario}:{quote(self.clave or str(), safe=str())}@{self.servidor}"'
sabotaje "tapar no tapa" "tapar_no_deja" "queda la clave escrita como" \
  reemplazar $C 'return _tapar(texto, secretos, visibles - secretos)' 'return texto'
sabotaje "tapar no mira ?password=" "tapar_no_deja" "en_la_consulta|queda la clave escrita como" \
  reemplazar $C 'secretos |= {v, quote(v, safe="")}' 'pass'

echo "== enviar"
sabotaje "los archivos los lee cualquiera" "lleva_la_copia_verificada" "copia.dump: 0o100644" \
  reemplazar $C 'os.umask(0o077)' 'pass'
sabotaje "enviar sin huella" "sin_su_huella" "copia.dump.huella.json" \
  reemplazar $C '    leer_huella(archivo)
    # La marca va última' '    # La marca va última'
sabotaje "enviar sin marca la da por verificada" "cortada" "destino/copia.dump" \
  reemplazar $C 'raise Falla(f"la copia {archivo} no está verificada: correr verificar") from None' 'verificada = sha256_de(archivo)'
sabotaje "enviar no mira si cambió" "copia_que_cambio" "la copia llegó distinta" \
  reemplazar $C 'if sha256_de(archivo) != verificada:' 'if False:'
sabotaje "enviar no mira lo que llegó" "llego_distinta" "DID NOT RAISE" \
  reemplazar $C 'if origen == archivo and sha256_de(temporal) != verificada:' 'if False:'
sabotaje "enviar no mira el destino antes" "lleva_la_copia_verificada" "error: ya existe /" \
  reemplazar $C 'raise Falla(f"ya existe en el destino: {final}")' 'pass'
sabotaje "enviar a un servicio" "carpeta_local" "[s3:|tiene que ser una carpeta local" \
  reemplazar $C 'if "://" in destino:' 'if False:'
sabotaje "enviar a una ruta relativa" "carpeta_local" "[relativo|enviada a" \
  reemplazar $C 'if not os.path.isabs(destino) or not os.path.isdir(destino):' 'if not os.path.isdir(destino):'
sabotaje "enviar a una carpeta que no existe" "carpeta_local" "no_existe|FileNotFoundError" \
  reemplazar $C 'if not os.path.isabs(destino) or not os.path.isdir(destino):' 'if not os.path.isabs(destino):'
sabotaje "sin COPIA_DESTINO no lo dice" "carpeta_local" "[-falta la variable COPIA_DESTINO]|tiene que ser una carpeta local" \
  reemplazar $C 'raise Falla("falta la variable COPIA_DESTINO")' 'pass'

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
