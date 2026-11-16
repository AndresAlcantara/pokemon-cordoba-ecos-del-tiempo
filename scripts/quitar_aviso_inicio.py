"""
quitar_aviso_inicio.py
======================
Se salta la pantalla del principio "2016 - 2022 Skeli Games / NOT FOR SALE".

Es la pantalla de copyright de FireRed (rutina 0x080EC62C). Su estado vive en
gMain.state y en cada fotograma suma 1 (instrucción "adds r1, #1" en 0x080EC740);
al llegar a 140 (0x8C) empieza el fundido y sigue la intro.
Cambiando el +1 por +70 llega a 140 en 2 fotogramas: 0 -> 70 -> 140.
Además se pone en negro su paleta (0x1FB6490), para que ni esos 2 fotogramas
ni el fundido dejen ver el texto.
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

INSTRUCCION, PALETA = 0xEC740, 0x1FB6490
rom = bytearray(t.ROM.read_bytes())
actual = rom[INSTRUCCION:INSTRUCCION + 2]
if actual == bytes([0x46, 0x31]):
    sys.exit("Ya estaba aplicado.")
if actual != bytes([0x01, 0x31]):           # 0x3101 = adds r1, #1
    sys.exit(f"La instrucción no es la esperada: {actual.hex()}")
resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-quitar-aviso_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
rom[INSTRUCCION:INSTRUCCION + 2] = bytes([0x46, 0x31])      # adds r1, #0x46 (70)
rom[PALETA:PALETA + 32] = bytes(32)
t.ROM.write_bytes(rom)
print("Aviso de inicio saltado (2 fotogramas, en negro).")
