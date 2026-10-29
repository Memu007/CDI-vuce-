"""Corta los tramos del video crudo (Playwright) en secuencias de cuadros PNG a
30 fps, usando las marcas de tiempo que dejó capture.js. Cada tramo puede ir
acelerado: fps de extracción = 30 / velocidad."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

out = Path(sys.argv[1])          # carpeta con marks.json y video.txt
clips_dir = Path(sys.argv[2])    # destino: clips/<nombre>/0000.png…
video = Path((out / "video.txt").read_text().strip())
m = {x["name"]: x["t"] for x in json.loads((out / "marks.json").read_text())}

# nombre: velocidad, [(inicio, fin), …]
CLIPS = {
    "subir":   (1.0,  [(m["upload_excel"] - 0.2, m["picker"] + 0.5), (m["review"] - 0.7, m["review"] + 0.75)]),
    "revisar": (1.5,  [(m["review"] + 0.6, m["ncm"] - 0.05)]),
    "ncm":     (1.15, [(m["ncm"] + 0.9, m["ncm_done"] + 0.15)]),
    "validar": (1.25, [(m["validating"] + 0.15, m["validating_done"] + 0.15)]),
    "listo":   (1.0,  [(m["ready"] - 0.15, m["end"] - 0.05)]),
}

shutil.rmtree(clips_dir, ignore_errors=True)
for name, (speed, segments) in CLIPS.items():
    dest = clips_dir / name
    dest.mkdir(parents=True)
    i = 0
    for start, end in segments:
        tmp = clips_dir / f"_{name}"
        tmp.mkdir()
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
            "-i", str(video), "-vf", f"fps={30 / speed:.4f}", str(tmp / "%04d.png"),
        ], check=True)
        for frame in sorted(tmp.iterdir()):
            frame.rename(dest / f"{i:04d}.png")
            i += 1
        tmp.rmdir()
    print(f"{name}: {i} cuadros, x{speed}")
