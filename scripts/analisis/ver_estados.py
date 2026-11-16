"""ver_estados.py - Dice en qué mapa y casilla está cada estado guardado de mGBA.
Uso: python ver_estados.py [carpeta]   (por defecto, la raíz del proyecto: MiHack.ss1..9)

CONCEPTO: gSaveBlock1Ptr (0x03005008, en IWRAM) apunta a SaveBlock1 en EWRAM;
sus primeros bytes son la posición (x, y) y el mapa actual (banco, número)."""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from estado_mgba import leer

raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
for f in sorted(raiz.glob("*.ss[0-9]")):
    m = leer(f)
    p = struct.unpack("<I", m["iwram"][0x5008:0x500C])[0]
    if not 0x02000000 <= p < 0x02040000:
        print(f"{f.name}: fuera del mundo (pantalla de título / intro)"); continue
    o = p - 0x02000000
    x, y = struct.unpack("<hh", m["ewram"][o:o + 4]); banco, mapa = m["ewram"][o + 4], m["ewram"][o + 5]
    print(f"{f.name}: mapa {banco}.{mapa}  casilla ({x},{y})")
