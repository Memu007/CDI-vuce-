#!/usr/bin/env python3
"""Cuánto rinde el equipo, sacado de Git.

uso: python3 docs/pm/herramientas/medir.py DESDE HASTA     (fechas AAAA-MM-DD, hora local)

Trae las ramas de RAMAS y mide, entre DESDE 00:00 y HASTA 23:59:
  1. Piezas aceptadas y devueltas, por Dev, de día y de noche (00 a 08 h).
  2. Devoluciones: devueltas / (aceptadas + devueltas).
  3. Espera de la PM: del informe de la Dev al veredicto.
  4. Huecos: más de 2 h sin un commit de cada rol (la sesión se reconoce por
     el canal que más escribe, CANAL_DEL_ROL; usa el trailer Claude-Session
     de los commits).
  5. Escapes: commits «PM: escape en <PIEZA>».
  6. Cola de la Dev 1 en NOW.md («Cola, en orden:» hasta el próximo título)
     y a qué ritmo se termina.
Los veredictos se reconocen por el mensaje del commit de la PM
(«<PIEZA> aceptada» / «<PIEZA> vuelve», ver «Revisión y aceptación» en
ONBOARDING-PM.md). La lista sale entera para poder corregirla a ojo.
Las piezas se llaman en mayúsculas con guiones y un número: COBRO-ESTADOS-1.
"""
import re, statistics, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

# --- Configuración del proyecto (la completa la PM al instalar) ---
HORAS_UTC = -3                   # UTC-3: la zona del proyecto
ZONA = timezone(timedelta(hours=HORAS_UTC))
RAMAS = {"pm": "claude/practical-shannon-szpwkn",
         "dev1": "claude/dev1-tecnica",
         "dev2": "claude/dev2-maria"}
CANAL_DEL_ROL = {"docs/pm/PARA-PM.md": "Dev 1", "docs/pm/PARA-PM-2.md": "Dev 2",
                 "docs/pm/NOW.md": "PM principal", "docs/pm/VISUAL.md": "PM visual"}   # los que no existan no cuentan
# ------------------------------------------------------------------
PIEZA = r"([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*-\d+)"
ACEPTA = [re.compile(PIEZA + r"[^;:]{0,25}?\bacept"), re.compile(r"\bacepta " + PIEZA)]
VUELVE = [re.compile(PIEZA + r"(?:, segunda vuelta)?(?: —)? (?:vuelve|en devolución|devolución sobre)")]
ESCAPE = re.compile(r"escape en " + PIEZA)


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout


def commits(*refs, paths=()):
    sep = "\x1f"
    out = git("log", "--no-merges", "--name-only",
              f"--format=\x1e%H{sep}%aI{sep}%s{sep}%(trailers:key=Claude-Session,valueonly,separator=)",
              *refs, "--", *paths)
    res = []
    for bloque in out.split("\x1e")[1:]:
        cab, *archivos = bloque.strip("\n").split("\n")
        h, fecha, asunto, sesion = cab.split(sep)
        res.append(dict(sha=h[:7], t=datetime.fromisoformat(fecha).astimezone(ZONA), asunto=asunto,
                        sesion=sesion.rsplit("/", 1)[-1], archivos=[x for x in archivos if x]))
    return res


def noche(t):
    return t.hour < 8


def main(desde, hasta):
    ini = datetime.fromisoformat(desde).replace(tzinfo=ZONA)
    fin = datetime.fromisoformat(hasta).replace(tzinfo=ZONA) + timedelta(days=1)
    for r in RAMAS.values():
        if r.startswith("{{"):
            continue
        subprocess.run(["git", "fetch", "-q", "origin", f"+refs/heads/{r}:refs/remotes/origin/{r}"])
    refs = [f"origin/{r}" for r in RAMAS.values() if not r.startswith("{{")]
    todos = {c["sha"]: c for c in commits(*refs)}.values()
    dentro = [c for c in todos if ini <= c["t"] < fin]
    dias = (fin - ini).days

    # Rol de cada sesión, por el canal que más escribe.
    votos = defaultdict(Counter)
    for c in todos:
        for a in c["archivos"]:
            if a in CANAL_DEL_ROL and c["sesion"]:
                votos[c["sesion"]][CANAL_DEL_ROL[a]] += 1
    rol = {s: v.most_common(1)[0][0] for s, v in votos.items()}

    # 1-3. Veredictos e informes.
    informes = [dict(c, dev=CANAL_DEL_ROL[a]) for c in todos for a in c["archivos"]
                if a in ("docs/pm/PARA-PM.md", "docs/pm/PARA-PM-2.md")
                and "informe" in c["asunto"].lower() and "sin entrega" not in c["asunto"]]
    # De quién es cada pieza: del canal donde la informó (un veredicto puede
    # tocar los dos canales).
    dev_de = {}
    for i in sorted(informes, key=lambda i: i["t"]):
        for p in re.findall(PIEZA, i["asunto"]):
            dev_de[p] = i["dev"]
    pm = [c for c in dentro if c["asunto"].startswith("PM")]
    veredictos, vistos = [], {}
    for c in sorted(pm, key=lambda c: c["t"]):
        for patrones, tipo in ((ACEPTA, "aceptada"), (VUELVE, "devuelta")):
            m = next((m for p in patrones if (m := p.search(c["asunto"]))), None)
            if m:
                pieza = m.group(1)
                # El mismo veredicto en dos commits seguidos cuenta una vez.
                if (pieza, tipo) in vistos and c["t"] - vistos[(pieza, tipo)] < timedelta(hours=1):
                    break
                vistos[(pieza, tipo)] = c["t"]
                quien = dev_de.get(pieza) or ("Dev 2" if "docs/pm/PARA-DEV-2.md" in c["archivos"] else "Dev 1")
                veredictos.append(dict(c, pieza=pieza, tipo=tipo, dev=quien))
                break
    print(f"== {desde} a {hasta} ({dias} días, hora local)\n")
    print("Veredictos (corregir a ojo si alguno está mal leído):")
    esperas = []
    for v in veredictos:
        previos = [i["t"] for i in informes if i["dev"] == v["dev"] and i["t"] <= v["t"]]
        espera = (v["t"] - max(previos)) if previos else None
        if espera is not None and espera < timedelta(hours=24):
            esperas.append(espera)
        e = f"{espera.total_seconds() / 3600:4.1f} h" if espera is not None else "   ? "
        print(f"  {v['t']:%d/%m %H:%M} {'noche' if noche(v['t']) else 'día  '} {v['dev']} "
              f"{v['tipo']:9} {v['pieza']:28} espera {e}  {v['sha']}")
    print()
    for dev in ("Dev 1", "Dev 2"):
        a = [v for v in veredictos if v["dev"] == dev and v["tipo"] == "aceptada"]
        d = [v for v in veredictos if v["dev"] == dev and v["tipo"] == "devuelta"]
        tasa = f"{len(d) / (len(a) + len(d)):.0%}" if a or d else "—"
        print(f"{dev}: {len(a)} aceptadas ({len(a) / dias:.1f} por día; "
              f"{sum(noche(v['t']) for v in a)} de noche), {len(d)} devueltas (devoluciones {tasa})")
    total = sum(v["tipo"] == "aceptada" for v in veredictos)
    print(f"Total: {total} aceptadas, {total / dias:.1f} por día")
    if esperas:
        h = sorted(e.total_seconds() / 3600 for e in esperas)
        print(f"Espera de la PM, del informe al veredicto: mediana {statistics.median(h):.1f} h, "
              f"máxima {h[-1]:.1f} h ({len(h)} veredictos)")

    # 4. Huecos de más de 2 h por rol.
    print("\nHuecos de más de 2 h sin commits, por rol (de noche = empieza entre 00 y 08 h):")
    por_rol = defaultdict(list)
    for c in dentro:
        if c["sesion"] in rol:
            por_rol[rol[c["sesion"]]].append(c["t"])
    for r in dict.fromkeys(CANAL_DEL_ROL.values()):
        ts = sorted(set(por_rol.get(r, [])))
        huecos = [(a, b) for a, b in zip(ts, ts[1:]) if b - a > timedelta(hours=2)]
        horas = sum((b - a).total_seconds() for a, b in huecos) / 3600
        de_noche = sum(noche(a) for a, _ in huecos)
        print(f"  {r:13} {len(ts):3} commits, {len(huecos)} huecos ({de_noche} de noche), {horas:.0f} h en total"
              + "".join(f"\n      {a:%d/%m %H:%M} → {b:%d/%m %H:%M}" for a, b in huecos))

    # 5. Escapes.
    escapes = [(c, m.group(1)) for c in dentro if (m := ESCAPE.search(c["asunto"]))]
    print(f"\nEscapes (problemas de piezas ya aceptadas): {len(escapes)}"
          + "".join(f"\n  {c['t']:%d/%m %H:%M} {p}: {c['asunto'][:90]}" for c, p in escapes))

    # 6. Cola de la Dev 1.
    now = git("show", f"origin/{RAMAS['pm']}:docs/pm/NOW.md")
    m = re.search(r"Cola, en orden:(.*?)(?:\n#|\Z)", now, re.S)
    if m:
        cola = re.findall(r"`([A-Z0-9-]+-\d+)`", m.group(1))
        ritmo = sum(v["tipo"] == "aceptada" and v["dev"] == "Dev 1" for v in veredictos) / dias
        print(f"\nCola de la Dev 1: {len(cola)} piezas")
        if ritmo:
            listo = datetime.now(ZONA) + timedelta(days=len(cola) / ritmo)
            print(f"  al ritmo de la Dev 1 en este período ({ritmo:.1f} por día) termina ~{listo:%d/%m}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
