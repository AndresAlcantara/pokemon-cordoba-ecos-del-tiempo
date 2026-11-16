"""
portada_logo.py
===============
Nuevo logo de la portada: mantiene "POKéMON" del logo de Unbound y sustituye
"UNBOUND" por "CÓRDOBA" (con el mismo estilo dorado y los MISMOS 16 colores),
y añade "Ecos del Tiempo" debajo.

Datos del logo (capa BG0 de la portada, paleta nº 13), cargados por la rutina
de la portada desde su tabla de punteros en 0x1ECE430:
  tiles  LZ77 en 0x1FD4120 (puntero en 0x1ECE444)
  mapa   LZ77 en 0x1FD50A0 (puntero en 0x1ECE448)   32x20 entradas de 2 bytes
  paleta en crudo en 0x1FD5300 (no se cambia)

Uso:
  python scripts/portada_logo.py --vista     -> solo genera pruebas/portada_vista.png
  python scripts/portada_logo.py             -> escribe en MiHack.gba (con respaldo)
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
PTR_TILES, PTR_MAPA, PALETA = 0x1ECE444, 0x1ECE448, 0x1FD5300
BANCO = 13
BAJAR_LOGO = 0           # píxeles que se baja el logo (0 = posición original)
FUENTE = "C:/Windows/Fonts/georgiab.ttf"
FUENTE_SUB = "C:/Windows/Fonts/georgiaz.ttf"   # Georgia negrita cursiva

# Índices de la paleta del logo (medidos en el original)
HALO, CONTORNO, SOMBRA, ORO_OSC, ORO, BRILLO, BRILLO_MAX = 0x8, 0xE, 0xD, 0xC, 0xB, 0xA, 0x9
SUB_RELLENO, SUB_CONTORNO = 0x1, 0x6


def leer_logo(rom):
    p = lambda o: struct.unpack("<I", rom[o:o + 4])[0] - 0x08000000
    tiles = lz77_descomprimir(rom, p(PTR_TILES))
    mapa = lz77_descomprimir(rom, p(PTR_MAPA))
    img = [[0] * 256 for _ in range(160)]
    for ty in range(20):
        for tx in range(32):
            ent = struct.unpack("<H", mapa[2 * (ty * 32 + tx):2 * (ty * 32 + tx) + 2])[0]
            n, hf, vf = ent & 0x3FF, (ent >> 10) & 1, (ent >> 11) & 1
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                    b = tiles[n * 32 + sy * 4 + sx // 2]
                    img[ty * 8 + y][tx * 8 + x] = (b >> 4) if sx & 1 else b & 15
    return img


def mascara_texto(texto, fuente, tam, ancho=256, alto=60):
    f = ImageFont.truetype(fuente, tam)
    im = Image.new("1", (ancho, alto), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"                           # sin suavizado: píxeles puros
    bb = d.textbbox((0, 0), texto, font=f)
    d.text(((ancho - (bb[2] - bb[0])) // 2 - bb[0], 4 - bb[1]), texto, font=f, fill=1)
    px = im.load()
    return {(x, y) for y in range(alto) for x in range(ancho) if px[x, y]}


def dilatar(pts, r=1):
    return {(x + dx, y + dy) for x, y in pts for dx in range(-r, r + 1) for dy in range(-r, r + 1)
            if abs(dx) + abs(dy) <= r + (1 if r > 1 else 0)}


def dibujar_oro(img, mascara, oy):
    ys = [y for _, y in mascara]
    y0, y1 = min(ys), max(ys)
    alto = y1 - y0 + 1
    halo, borde = dilatar(mascara, 2), dilatar(mascara, 1)
    for x, y in halo - borde:
        if 0 <= x < 256 and 0 <= y + oy < 160: img[y + oy][x] = HALO
    for x, y in borde - mascara:
        if 0 <= x < 256 and 0 <= y + oy < 160: img[y + oy][x] = CONTORNO
    for x, y in mascara:
        rel = (y - y0) / max(1, alto - 1)
        c = ORO
        if 0.42 <= rel <= 0.58: c = BRILLO
        if 0.47 <= rel <= 0.53: c = BRILLO_MAX
        if (x, y + 1) not in mascara or (x + 1, y) not in mascara: c = SOMBRA        # sombra abajo/derecha
        elif (x, y + 2) not in mascara: c = ORO_OSC
        if (x, y - 1) not in mascara and c == ORO: c = BRILLO                      # luz arriba
        img[y + oy][x] = c


def dibujar_sub(img, mascara, oy):
    borde = dilatar(mascara, 1)
    for x, y in borde - mascara:
        if 0 <= y + oy < 160: img[y + oy][x] = SUB_CONTORNO
    for x, y in mascara:
        img[y + oy][x] = SUB_RELLENO


def construir(rom):
    img = leer_logo(rom)
    for y in range(58, 160):                # borrar "UNBOUND"
        img[y] = [0] * 256
    dibujar_oro(img, mascara_texto("CÓRDOBA", FUENTE, 27), 52)
    dibujar_sub(img, mascara_texto("Ecos del Tiempo", FUENTE_SUB, 12, alto=24), 89)
    # bajar todo el logo para dejar arriba sitio a la cabeza de Dialga
    return [[0] * 256 for _ in range(BAJAR_LOGO)] + img[:160 - BAJAR_LOGO]


def a_tiles(img):
    """Imagen de índices 256x160 -> (tiles 4bpp únicos, mapa 32x20), reutilizando tiles volteados."""
    tiles, indice, mapa = [], {}, bytearray()
    def bloque(tx, ty, hf, vf):
        out = bytearray()
        for y in range(8):
            yy = 7 - y if vf else y
            for x in range(0, 8, 2):
                a = img[ty * 8 + yy][tx * 8 + (7 - x if hf else x)]
                b = img[ty * 8 + yy][tx * 8 + (7 - (x + 1) if hf else x + 1)]
                out.append(a | (b << 4))
        return bytes(out)
    vacio = bytes(32); tiles.append(vacio); indice[vacio] = 0
    for ty in range(20):
        for tx in range(32):
            n, flags = None, 0
            for hf in (0, 1):
                for vf in (0, 1):
                    k = bloque(tx, ty, hf, vf)
                    if k in indice and n is None:
                        n, flags = indice[k], (hf << 10) | (vf << 11)
            if n is None:
                k = bloque(tx, ty, 0, 0); n = len(tiles); tiles.append(k); indice[k] = n
            mapa += struct.pack("<H", n | flags | (BANCO << 12))
    return b"".join(tiles), bytes(mapa), len(tiles)


def vista(img, rom):
    pal = [struct.unpack("<H", rom[PALETA + 2 * i:PALETA + 2 * i + 2])[0] for i in range(16)]
    cols = [((c & 31) * 8, ((c >> 5) & 31) * 8, ((c >> 10) & 31) * 8) for c in pal]
    fondo = t.RAIZ / "pruebas" / "capa_ss3_bg1.png"
    im = Image.open(fondo).convert("RGB") if fondo.exists() else Image.new("RGB", (240, 160))
    px = im.load()
    for y in range(160):
        for x in range(240):
            if img[y][x]: px[x, y] = cols[img[y][x]]
    im.resize((720, 480), Image.NEAREST).save(t.RAIZ / "pruebas" / "portada_vista.png")


def main():
    original = ORIGINAL.read_bytes()
    img = construir(original)
    vista(img, original)
    tiles, mapa, n = a_tiles(img)
    print(f"Logo nuevo: {n} tiles (máximo 512 en su zona de VRAM).")
    if n > 512:
        sys.exit("Demasiados tiles")
    if "--vista" in sys.argv:
        print("Vista previa en pruebas/portada_vista.png"); return
    rom = bytearray(t.ROM.read_bytes())
    for p in (PTR_TILES, PTR_MAPA):
        if len(t.punteros_a(original, struct.unpack("<I", original[p:p + 4])[0] - 0x08000000)) != 1:
            sys.exit("El logo tiene más referencias de las esperadas")
    datos_t, datos_m = lz77_comprimir(tiles), lz77_comprimir(mapa)
    o_t = t.buscar_libre(bytes(rom), len(datos_t), alinear=4); rom[o_t:o_t + len(datos_t)] = datos_t
    o_m = t.buscar_libre(bytes(rom), len(datos_m), alinear=4); rom[o_m:o_m + len(datos_m)] = datos_m
    rom[PTR_TILES:PTR_TILES + 4] = struct.pack("<I", 0x08000000 + o_t)
    rom[PTR_MAPA:PTR_MAPA + 4] = struct.pack("<I", 0x08000000 + o_m)
    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-logo_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(rom)
    print(f"Tiles en 0x{o_t:X} ({len(datos_t)} bytes) · mapa en 0x{o_m:X} ({len(datos_m)} bytes)")


if __name__ == "__main__":
    main()
