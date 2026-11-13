#!/usr/bin/env python3
"""Avance del roadmap, contado desde las marcas de ROADMAP.md.

Cada pieza lleva una marca en su celda: ✅ aceptada, 🔵 en curso o lista sin
revisar, ⏳ espera a alguien de afuera, ⚪ sin empezar. El porcentaje es
aceptadas sobre el total; una pieza sin marca no se cuenta y se avisa.
"""
import re
import sys
from pathlib import Path

MARCAS = {"✅": "aceptadas", "🔵": "en curso", "⏳": "esperan", "⚪": "sin empezar"}
ROADMAP = Path(__file__).resolve().parents[1] / "ROADMAP.md"
FILA = re.compile(r"^\|(?: \d+ \|)? (✅|🔵|⏳|⚪) ([A-Z0-9-]+) \|")


def main() -> int:
    fase = None
    piezas: dict[str, tuple[str, str]] = {}
    for linea in ROADMAP.read_text(encoding="utf-8").splitlines():
        if linea.startswith("### Fase"):
            fase = linea[4:].split(" — ")[0]
            continue
        m = FILA.match(linea)
        if m and fase:
            marca, nombre = m.groups()
            if nombre in piezas:
                print(f"repetida: {nombre}", file=sys.stderr)
                return 1
            piezas[nombre] = (fase, marca)
    if not piezas:
        print("no encontré piezas marcadas en ROADMAP.md", file=sys.stderr)
        return 1

    def linea(nombre: str, grupo: list[str]) -> str:
        hechas = sum(1 for p in grupo if piezas[p][1] == "✅")
        cuenta = ", ".join(
            f"{sum(1 for p in grupo if piezas[p][1] == m)} {t}"
            for m, t in MARCAS.items()
            if any(piezas[p][1] == m for p in grupo)
        )
        return f"{nombre}: {round(100 * hechas / len(grupo))} % ({hechas} de {len(grupo)}; {cuenta})"

    print(linea("Total", list(piezas)))
    for fase in dict.fromkeys(f for f, _ in piezas.values()):
        print("  " + linea(fase, [p for p, (f, _) in piezas.items() if f == fase]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
