"""donde.py - Posición y orientación de los personajes en un estado de mGBA (por defecto MiHack.ss9).
gObjectEvents (0x02036E38): 16 objetos de 0x24 bytes; coordenadas en +0x10 (con 7 de margen)."""
import sys, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from estado_mgba import leer
ruta = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[2] / "MiHack.ss9")
e = leer(ruta)["ewram"]; o = 0x36E38
DIR = {1: "abajo", 2: "arriba", 3: "izquierda", 4: "derecha"}
for i in range(16):
    b = e[o + 0x24 * i:o + 0x24 * (i + 1)]
    if b[0] & 1:
        x, y = struct.unpack("<hh", b[0x10:0x14])
        print(f"objeto {i}: gfx {b[5]}  casilla ({x-7},{y-7})  mira {DIR.get(b[0x18] & 15, '?')}")
