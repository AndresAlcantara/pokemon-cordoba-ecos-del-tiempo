"""
portada_quitar_aros.py
======================
En el logo de Unbound la "O" de UNBOUND era un aro dorado animado (un sprite,
no parte del logo). Con el logo nuevo, ese aro tapa la R y la D de "CÓRDOBA".

Los gráficos del aro (y de las esferas del rótulo "Skeli Games presents")
son 80 tiles LZ77 en 0x1FD5A74, apuntados desde 0x1FABCD4. Este script pone en
su lugar 80 tiles vacíos (transparentes): el sprite sigue existiendo, pero no
se ve.
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_comprimir, lz77_descomprimir  # noqa: E402

import sys as _s
# Por defecto: aros (0x1FD5A74, puntero 0x1FABCD4). Con --destellos: los destellos de Hoopa
# (12 tiles en 0x1FD59F0, puntero 0x1FABCE4), que quedaban como puntos rojos sobre Dialga.
if "--destellos" in _s.argv:
    PUNTERO, ORIGEN = 0x1FABCE4, 0x1FD59F0
else:
    PUNTERO, ORIGEN = 0x1FABCD4, 0x1FD5A74

rom = bytearray(t.ROM.read_bytes())
actual = struct.unpack("<I", rom[PUNTERO:PUNTERO + 4])[0] - 0x08000000
if actual != ORIGEN:
    sys.exit(f"El puntero ya no apunta a los aros originales (0x{actual:X}); ¿ya se aplicó?")
tam = len(lz77_descomprimir(rom, ORIGEN))
vacio = lz77_comprimir(bytes(tam))
o = t.buscar_libre(bytes(rom), len(vacio), alinear=4)
resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-quitar-aros_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
rom[o:o + len(vacio)] = vacio
rom[PUNTERO:PUNTERO + 4] = struct.pack("<I", 0x08000000 + o)
t.ROM.write_bytes(rom)
print(f"{tam // 32} tiles vacíos en 0x{o:X}; puntero 0x{PUNTERO:X} actualizado.")
