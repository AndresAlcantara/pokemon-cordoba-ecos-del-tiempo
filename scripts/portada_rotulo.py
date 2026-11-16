"""
portada_rotulo.py
=================
Cambia el rótulo de la intro "Skeli Games PRESENTS" por "Randes PRESENTA".

  - "Skeli Games": 36 tiles (18x2, en orden por filas) LZ77 en 0xEF23D4,
    puntero en 0xECB6C. Paleta nº 13 (dorados y contorno marrón).
  - "PRESENTS": sprite de 8 tiles (64x8) LZ77 en 0xEF2674, puntero en 0x40BBE0.
    Solo cambia la última letra: S -> A.

Uso: python scripts/portada_rotulo.py [--vista]
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_comprimir, lz77_descomprimir  # noqa: E402

ORIGINAL = t.RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba"
NOMBRE_DATOS, NOMBRE_PTR = 0xEF23D4, 0xECB6C
PRESENTA_DATOS, PRESENTA_PTR = 0xEF2674, 0x40BBE0
NOMBRE = "Randes"
FUENTE = "C:/Windows/Fonts/georgiab.ttf"
CREMA, ORO, ORO_OSC, MARRON, BLANCO = 1, 2, 3, 4, 5


def texto_tiles():
    f = ImageFont.truetype(FUENTE, 17)
    im = Image.new("1", (144, 16), 0); d = ImageDraw.Draw(im); d.fontmode = "1"
    bb = d.textbbox((0, 0), NOMBRE, font=f)
    d.text(((144 - (bb[2] - bb[0])) // 2 - bb[0], (15 - (bb[3] - bb[1])) // 2 - bb[1]), NOMBRE, font=f, fill=1)
    px = im.load()
    m = {(x, y) for y in range(16) for x in range(144) if px[x, y]}
    ys = [y for _, y in m]; y0, y1 = min(ys), max(ys)
    img = [[0] * 144 for _ in range(16)]
    for x, y in m:
        rel = (y - y0) / max(1, y1 - y0)
        c = CREMA if rel < 0.3 else (ORO if rel < 0.65 else ORO_OSC)
        if (x, y - 1) not in m or (x - 1, y) not in m: c = BLANCO if rel < 0.3 else CREMA   # luz arriba/izquierda
        img[y][x] = c
    for x, y in m:                                   # contorno marrón abajo y a la derecha
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            nx, ny = x + dx, y + dy
            if nx < 144 and ny < 16 and (nx, ny) not in m: img[ny][nx] = MARRON
    tiles = bytearray()
    for t_ in range(36):
        tx, ty = (t_ % 18) * 8, (t_ // 18) * 8
        for y in range(8):
            for x in range(0, 8, 2):
                tiles.append(img[ty + y][tx + x] | (img[ty + y][tx + x + 1] << 4))
    return bytes(tiles), img


def presenta(rom):
    d = bytearray(lz77_descomprimir(rom, PRESENTA_DATOS))
    A = ["..555..", ".55.55.", "66...66", "5555555", "66...66", "55...55", ".......", "......."]
    tile = bytearray()
    for y in range(8):
        fila = [int(c) if c != "." else 0 for c in A[y]] + [0]
        for x in range(0, 8, 2):
            tile.append(fila[x] | (fila[x + 1] << 4))
    d[7 * 32:8 * 32] = tile
    return bytes(d)


def main():
    original = ORIGINAL.read_bytes()
    tiles, img = texto_tiles()
    nuevo_presenta = presenta(original)
    cols = {0: (0, 0, 0), 1: (248, 224, 184), 2: (216, 168, 80), 3: (200, 144, 8), 4: (112, 56, 0), 5: (248, 248, 248), 6: (200, 200, 200)}
    vista = Image.new("RGB", (240, 160)); px = vista.load()
    for y in range(16):
        for x in range(144): px[48 + x, 72 + y] = cols[img[y][x]]
    for t_ in range(8):
        for i in range(32):
            b = nuevo_presenta[t_ * 32 + i]
            for k, v in ((0, b & 15), (1, b >> 4)):
                if v: px[88 + t_ * 8 + (i % 4) * 2 + k, 104 + i // 4] = cols.get(v, (255, 255, 255))
    vista.resize((720, 480), Image.NEAREST).save(t.RAIZ / "pruebas" / "rotulo_vista.png")
    if "--vista" in sys.argv:
        print("Vista previa: pruebas/rotulo_vista.png"); return
    rom = bytearray(t.ROM.read_bytes())
    for ptr_, datos in ((NOMBRE_PTR, tiles), (PRESENTA_PTR, nuevo_presenta)):
        comp = lz77_comprimir(datos)
        o = t.buscar_libre(bytes(rom), len(comp), alinear=4)
        rom[o:o + len(comp)] = comp
        rom[ptr_:ptr_ + 4] = struct.pack("<I", 0x08000000 + o)
        print(f"Datos para el puntero 0x{ptr_:X} en 0x{o:X} ({len(comp)} B)")
    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-rotulo_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(rom)


if __name__ == "__main__":
    main()
