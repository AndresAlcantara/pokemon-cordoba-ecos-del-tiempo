"""
rotulo_colores.py
=================
Recolorea el rótulo "Randes PRESENTA" y su animación (esferas y chispas) con la
gama roja y blanca de la Mezquita, en lugar del dorado y morado de Unbound.
Las tres paletas están en crudo (16 colores) y se escriben en su sitio:
  0x1FD60BC  esferas y chispas (sprites, banco 1)
  0xEF2654   texto "Randes" (fondo, banco 13)
  0xEF26E0   sprite "PRESENTA" (banco 2): sus filas alternan los colores 5 y 6,
             así que queda a rayas blancas y rojas, como las dovelas.
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

def gba(c):
    r, g, b = (min(31, round(v / 8)) for v in c)
    return struct.pack("<H", r | (g << 5) | (b << 10))

PALETAS = {
    0x1FD60BC: [(128, 248, 248), (255, 250, 240), (250, 232, 210), (232, 128, 96), (184, 48, 32), (128, 30, 22),
                (72, 14, 10), (214, 64, 44), (196, 52, 36), (176, 44, 30), (130, 30, 22), (90, 18, 14),
                (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],
    0xEF2654: [(0, 0, 0), (252, 238, 214), (214, 70, 48), (166, 36, 24), (70, 10, 8), (255, 252, 244)]
              + [(0, 0, 0)] * 10,
    0xEF26E0: [(24, 40, 72), (0, 0, 0), (136, 120, 16), (184, 168, 16), (70, 10, 8), (252, 244, 230),
               (196, 48, 32), (248, 0, 248), (248, 0, 248), (248, 0, 248), (248, 0, 248), (216, 216, 216),
               (24, 40, 72), (80, 80, 80), (176, 176, 176), (248, 248, 248)],
}

rom = bytearray(t.ROM.read_bytes())
resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-colores-rotulo_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
for off, cols in PALETAS.items():
    rom[off:off + 32] = b"".join(gba(c) for c in cols)
    print(f"Paleta en 0x{off:X} recoloreada")
t.ROM.write_bytes(rom)
