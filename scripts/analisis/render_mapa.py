"""
render_mapa.py
==============
Dibuja un mapa de la ROM a partir de su cabecera (solo lectura).

CONCEPTOS (para clase)
----------------------
* Un mapa es una cuadrícula de BLOQUES de 16x16. Cada celda guarda 2 bytes:
  número de bloque (10 bits), colisión (2 bits) y elevación (4 bits).
* Cada bloque son 8 tiles de 8x8: 4 en la capa de abajo y 4 en la de arriba.
* Los bloques salen de dos TILESETS: el primario (bloques 0-639) y el secundario
  (bloques 640 en adelante). Cada tileset trae sus tiles, sus paletas y la
  definición de sus bloques.

Uso: python render_mapa.py 0xCABECERA salida.png [--rejilla]
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from insertar_pokemon import lz77_descomprimir  # noqa: E402

ROM = (Path(__file__).resolve().parent.parent.parent / "MiHack.gba").read_bytes()
P = lambda o: struct.unpack("<I", ROM[o:o + 4])[0] - 0x08000000
H = lambda o: struct.unpack("<H", ROM[o:o + 2])[0]
PRIMARIOS = 640


def tileset(o):
    comprimido = ROM[o]
    tiles_ptr, pal_ptr, meta_ptr = P(o + 4), P(o + 8), P(o + 12)
    tiles = lz77_descomprimir(ROM, tiles_ptr) if comprimido else ROM[tiles_ptr:tiles_ptr + 0x8000]
    pals = [[((c & 31) * 8, ((c >> 5) & 31) * 8, ((c >> 10) & 31) * 8)
             for c in struct.unpack("<16H", ROM[pal_ptr + 32 * p:pal_ptr + 32 * p + 32])] for p in range(16)]
    return tiles, pals, meta_ptr


def dibujar(cabecera, rejilla=False):
    lay = P(cabecera)
    w, h = struct.unpack("<II", ROM[lay:lay + 8])
    datos = P(lay + 12)
    t1, t2 = P(lay + 16), P(lay + 20)
    tiles1, pals1, meta1 = tileset(t1)
    tiles2, pals2, meta2 = tileset(t2)
    pals = pals1[:7] + pals2[7:13] + pals1[13:]
    tiles = tiles1[:PRIMARIOS * 32].ljust(PRIMARIOS * 32, b"\0") + tiles2

    def tile(n, pal, hf, vf):
        im = Image.new("RGBA", (8, 8)); px = im.load()
        base = n * 32
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                o = base + sy * 4 + sx // 2
                v = tiles[o] if o < len(tiles) else 0
                v = (v >> 4) if sx & 1 else v & 15
                px[x, y] = (*pals[pal][v], 255) if v else (0, 0, 0, 0)
        return im

    cache = {}

    def bloque(n):
        if n in cache:
            return cache[n]
        meta = meta1 + 16 * n if n < PRIMARIOS else meta2 + 16 * (n - PRIMARIOS)
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
        for capa in range(2):
            for k in range(4):
                e = H(meta + 2 * (capa * 4 + k))
                im.alpha_composite(tile(e & 0x3FF, e >> 12, (e >> 10) & 1, (e >> 11) & 1), ((k % 2) * 8, (k // 2) * 8))
        cache[n] = im
        return im

    img = Image.new("RGBA", (w * 16, h * 16))
    celdas = []
    for y in range(h):
        for x in range(w):
            c = H(datos + 2 * (y * w + x))
            celdas.append(c)
            img.paste(bloque(c & 0x3FF), (x * 16, y * 16))
    if rejilla:
        d = ImageDraw.Draw(img)
        for y in range(h):
            for x in range(w):
                if (celdas[y * w + x] >> 10) & 3:
                    d.rectangle([x * 16 + 6, y * 16 + 6, x * 16 + 9, y * 16 + 9], fill=(255, 0, 0, 160))
    return img, (w, h, hex(t1 + 0x08000000), hex(t2 + 0x08000000))


if __name__ == "__main__":
    img, info = dibujar(int(sys.argv[1], 16), "--rejilla" in sys.argv)
    img.save(sys.argv[2]); print(info)
