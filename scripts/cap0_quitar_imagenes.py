"""
cap0_quitar_imagenes.py
=======================
Deshace cap0_imagenes.py: devuelve el script de la intro a su forma original
(páginas 1 y 2 sin desvío) y devuelve el hueco de especie 254 a su sprite "??".
Los textos en español de cap0_intro.py se mantienen: están escritos en su sitio
y los punteros de las páginas 1 y 2 apuntan a ellos igual que en el original.
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from cap0_imagenes import PAGINA1, VUELTA  # noqa: E402
from insertar_pokemon import TABLA_FRONTAL, TABLA_PAL_NORMAL  # noqa: E402

original = (t.RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba").read_bytes()
rom = bytearray(t.ROM.read_bytes())
resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-quitar-imagenes_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
shutil.copy2(t.ROM, resp)
print("Respaldo:", resp.relative_to(t.RAIZ))

rom[PAGINA1:VUELTA] = original[PAGINA1:VUELTA]
for tabla in (TABLA_FRONTAL, TABLA_PAL_NORMAL):
    e = tabla + 8 * 254
    rom[e:e + 8] = original[e:e + 8]
t.ROM.write_bytes(rom)

ok = rom[PAGINA1:VUELTA] == original[PAGINA1:VUELTA]
ok &= all(rom[tb + 8 * 254:tb + 8 * 254 + 8] == original[tb + 8 * 254:tb + 8 * 254 + 8]
          for tb in (TABLA_FRONTAL, TABLA_PAL_NORMAL))
print("Intro sin imágenes y hueco 254 restaurado:", "CORRECTO" if ok else "FALLO")
