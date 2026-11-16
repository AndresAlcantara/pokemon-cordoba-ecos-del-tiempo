"""
portada_mezquita.py
===================
Portada propia: fondo con los arcos de la Mezquita de Córdoba (dovelas rojas y
crema) y la silueta de Dialga, con paleta nueva; y el logo recoloreado con la
misma gama (crema y rojo ladrillo).

Silueta de Dialga: arte oficial descargado del repositorio público de PokeAPI
(descargas/dialga/483.png); de él solo se usa la FORMA (canal alfa).

Datos que se cambian:
  - paleta del fondo: 208 colores en crudo en 0x1FCF1EC (se escribe en su sitio)
  - tiles 8bpp + mapa del fondo: a espacio libre; se repuntean la portada
    (0x1ECE508/0x1ECE74C y 0x1ECE510/0x1ECE754) y la transición que la precede
    (0x1ECE438 y 0x1ECE43C), que usa la misma paleta
  - paleta del logo: 16 colores en crudo en 0x1FD5300 (en su sitio)

Uso: python scripts/portada_mezquita.py [--vista]
"""
import math
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_comprimir  # noqa: E402
import portada_fondo as pf  # noqa: E402  (reutiliza a_tiles con fusión de tiles)
import portada_logo as pl   # noqa: E402

DIALGA = t.RAIZ / "descargas" / "dialga" / "arte_mascara.png"   # silueta del arte oficial (la que pidió el usuario)
PALETA_FONDO, N_COLORES = 0x1FCF1EC, 208
PTRS_TILES = (0x1ECE508, 0x1ECE74C, 0x1ECE438)
PTRS_MAPA = (0x1ECE510, 0x1ECE754, 0x1ECE43C)
PALETA_LOGO = 0x1FD5300
PTR_TILES_DESTELLO, PTR_MAPA_DESTELLO, PALETA_DESTELLO = 0x1ECE450, 0x1ECE454, 0x1FD59D0   # capa del destello (antes Hoopa)
K = 4                                    # se dibuja a 4x y se reduce (bordes más limpios)
CON_DIALGA = False                         # el usuario prefiere la portada sin la silueta
ALTO_DIALGA, ARRIBA_Y = 60, 99           # Dialga ENTERO, bajo "Ecos del Tiempo" (la silueta completa se reconoce)
W, H = 240 * K, 160 * K

# --- gama de la Mezquita ---
ROJO = (176, 44, 30); ROJO_OSC = (120, 28, 20); CREMA = (238, 218, 178); CREMA_OSC = (196, 168, 128)
COLUMNA = (150, 128, 104); COLUMNA_OSC = (96, 80, 64); FONDO_ARRIBA = (14, 6, 6); FONDO_ABAJO = (46, 16, 12)
LUZ = (250, 206, 132)

# Paleta del logo: mismos índices que el original, otros colores
LOGO = [(128, 248, 248), (252, 244, 228), (240, 220, 190), (220, 186, 150), (150, 40, 28), (120, 28, 22),
        (88, 20, 16), (56, 10, 10), (252, 248, 236), (248, 176, 128), (232, 112, 72), (196, 56, 36),
        (150, 36, 24), (100, 22, 16), (60, 12, 10), (0, 0, 0)]


def mezclar(c, f, hacia=(10, 4, 4)):
    return tuple(int(a * f + b * (1 - f)) for a, b in zip(c, hacia))


def herradura(d, cx, cy, R, r, ini, fin, n, oscuridad):
    """Anillo de dovelas alternas rojo/crema entre los ángulos ini y fin (grados, y hacia abajo)."""
    for i in range(n):
        a0 = math.radians(ini + (fin - ini) * i / n); a1 = math.radians(ini + (fin - ini) * (i + 1) / n)
        col = ROJO if i % 2 == 0 else CREMA
        pts = [(cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1)),
               (cx + r * math.cos(a1), cy + r * math.sin(a1)), (cx + r * math.cos(a0), cy + r * math.sin(a0))]
        d.polygon(pts, fill=mezclar(col, oscuridad))
    # filete exterior
    d.arc([cx - R, cy - R, cx + R, cy + R], ini, fin, fill=mezclar(ROJO_OSC, oscuridad), width=max(1, int(R * 0.05)))


def capa_arcos(R, cy, oscuridad, desfase=0):
    """Arquería de la Mezquita: arcos de herradura que comparten columnas y, encima,
    arcos de medio punto que arrancan de pilares sobre esas mismas columnas."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = R * 0.60
    paso = 2 * R * math.cos(math.radians(20))              # los arcos se tocan en las columnas
    arranque = cy + R * math.sin(math.radians(20))
    cy2 = cy - R * 1.25                                    # centro del arco superior
    R2 = paso / 2; r2 = R2 * 0.62
    col_w = R * 0.24
    x = desfase - paso * 2
    while x < W + paso * 2:
        cxp = x - paso / 2                                 # columna entre dos arcos
        d.rectangle([cxp - col_w * 0.85, cy2, cxp + col_w * 0.85, arranque], fill=mezclar(CREMA_OSC, oscuridad * 0.8))
        d.rectangle([cxp - col_w / 2, arranque, cxp + col_w / 2, H], fill=mezclar(COLUMNA, oscuridad))
        d.rectangle([cxp - col_w / 2, arranque, cxp - col_w / 6, H], fill=mezclar(COLUMNA_OSC, oscuridad))
        d.rectangle([cxp - col_w * 0.8, arranque - R * 0.07, cxp + col_w * 0.8, arranque + R * 0.05],
                    fill=mezclar(CREMA, oscuridad))
        herradura(d, x, cy2, R2, r2, 180, 360, 11, oscuridad * 0.85)
        herradura(d, x, cy, R, r, 160, 380, 15, oscuridad)
        x += paso
    return im


def silueta_dialga(alto):
    a = Image.open(DIALGA).convert("L")
    bb = a.getbbox(); a = a.crop(bb)
    esc = alto / a.height
    a = a.resize((round(a.width * esc), alto), Image.LANCZOS)
    a = a.point(lambda v: 255 if v > 127 else 0)   # la máscara ya está limpia: sin filtros que borren detalles
    return a


def fondo():
    base = Image.new("RGB", (W, H))
    px = np.zeros((H, W, 3))
    for y in range(H):
        f = y / H
        px[y, :] = [FONDO_ARRIBA[i] * (1 - f) + FONDO_ABAJO[i] * f for i in range(3)]
    # resplandor cálido en el centro, detrás de Dialga
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W * 0.30)) ** 2 + ((yy - H * 0.78) / (H * 0.45)) ** 2)   # luz detrás de la cabeza
    glow = np.clip(1 - dist, 0, 1) ** 0.9 * 1.0
    for i in range(3):
        px[:, :, i] = px[:, :, i] * (1 - glow) + LUZ[i] * glow
    base = Image.fromarray(px.astype(np.uint8))
    # tres planos de arcos, del fondo al frente
    for R, cy, osc, des in ((20 * K, 70 * K, 0.28, 20 * K),
                            (32 * K, 84 * K, 0.52, 0),
                            (50 * K, 100 * K, 0.95, 120 * K)):
        base = Image.alpha_composite(base.convert("RGBA"), capa_arcos(R, cy, osc, des)).convert("RGB")
    # Dialga: silueta oscura con borde de luz dorada
    sil = silueta_dialga(ALTO_DIALGA * K)
    ox, oy = (W - sil.width) // 2, ARRIBA_Y * K   # centrada
    global SIL_POS
    SIL_POS = (sil, ox, oy)
    borde = sil.filter(ImageFilter.MaxFilter(3 * K + 1))
    capa_borde = Image.new("RGB", (W, H), (250, 226, 170)); capa_sil = Image.new("RGB", (W, H), (6, 2, 2))
    m_borde = Image.new("L", (W, H), 0); m_borde.paste(borde, (ox, oy))
    m_sil = Image.new("L", (W, H), 0); m_sil.paste(sil, (ox, oy))
    if CON_DIALGA:
        base.paste(capa_borde, (0, 0), m_borde); base.paste(capa_sil, (0, 0), m_sil)
    return base.resize((240, 160), Image.LANCZOS)


# --- "PULSA START" con letras de 5 píxeles ---
LETRAS = {
    "P": ["######.", "##...##", "######.", "##.....", "##....."],
    "U": ["##...##", "##...##", "##...##", "##...##", ".#####."],
    "L": ["##.....", "##.....", "##.....", "##.....", "#######"],
    "S": ["######.", "##.....", ".#####.", ".....##", "######."],
    "A": ["..###..", ".##.##.", "##...##", "#######", "##...##"],
    "T": ["########", "...##...", "...##...", "...##...", "...##..."],
    "R": ["######.", "##...##", "######.", "##..##.", "##...##"],
    " ": ["....", "....", "....", "....", "...."],
}


def escribir(img, texto, y, color, sombra):
    ancho = sum(len(LETRAS[c][0]) + 1 for c in texto) - 1
    x = (240 - ancho) // 2
    d = ImageDraw.Draw(img)
    for c in texto:
        for f, fila in enumerate(LETRAS[c]):
            for k, ch in enumerate(fila):
                if ch == "#":
                    d.point((x + k + 1, y + f + 1), fill=sombra)
        for f, fila in enumerate(LETRAS[c]):
            for k, ch in enumerate(fila):
                if ch == "#":
                    d.point((x + k, y + f), fill=color)
        x += len(LETRAS[c][0]) + 1


def construir():
    img = fondo()
    escribir(img, "PULSA START", 148, CREMA, (40, 8, 6))
    q = img.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:96 * 3]
    cols = [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]
    idx = np.zeros((160, 256), dtype=np.uint8)
    idx[:, :240] = np.array(q)
    # índice 0 = color de fondo transparente en BG (no se usa en la imagen: se desplazan +1)
    idx[:, :240] += 1
    cols = [(0, 0, 0)] + cols
    return idx, cols


def destello():
    """Capa del destello previo a la portada (BG2, 4bpp, paleta nº 14): la misma silueta
    de Dialga, en el mismo sitio, en lugar de la de Hoopa."""
    sil, ox, oy = SIL_POS
    m = Image.new("L", (W, H), 0); m.paste(sil, (ox, oy))
    b = Image.new("L", (W, H), 0); b.paste(sil.filter(ImageFilter.MaxFilter(2 * K + 1)), (ox, oy))
    m = np.array(m.resize((240, 160), Image.LANCZOS)) > 127
    b = np.array(b.resize((240, 160), Image.LANCZOS)) > 127
    if not CON_DIALGA:
        m[:] = False; b[:] = False          # destello sin silueta (capa vacía)
    img = np.zeros((160, 256), dtype=np.uint8)
    img[:, :240][b] = 2; img[:, :240][m] = 1
    tiles, indice, mapa = [bytes(32)], {bytes(32): 0}, bytearray()
    for ty in range(20):
        for tx in range(32):
            blk = img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            k = bytes(int(blk[y, x]) | (int(blk[y, x + 1]) << 4) for y in range(8) for x in range(0, 8, 2))
            if k not in indice: indice[k] = len(tiles); tiles.append(k)
            mapa += struct.pack("<H", indice[k] | (14 << 12))
    pal = [(0, 0, 0), (12, 5, 5), (250, 226, 170)] + [(0, 0, 0)] * 13
    return b"".join(tiles), bytes(mapa), b"".join(gba(c) for c in pal)


def gba(c):
    r, g, b = (min(31, round(v / 8)) for v in c)
    return struct.pack("<H", r | (g << 5) | (b << 10))


def vista(idx, cols, rom):
    tiles, mapa, n, fus = pf.a_tiles(idx)
    # reconstruir desde los tiles finales (para ver el efecto de las fusiones)
    out = np.zeros((160, 256), dtype=np.uint8)
    for k in range(640):
        ent = struct.unpack("<H", mapa[2 * k:2 * k + 2])[0]; nn, hf, vf = ent & 0x3FF, (ent >> 10) & 1, (ent >> 11) & 1
        b = np.frombuffer(tiles[nn * 64:nn * 64 + 64], dtype=np.uint8).reshape(8, 8)
        if hf: b = b[:, ::-1]
        if vf: b = b[::-1, :]
        out[(k // 32) * 8:(k // 32) * 8 + 8, (k % 32) * 8:(k % 32) * 8 + 8] = b
    rgb = np.array([cols[i] if i < len(cols) else (0, 0, 0) for i in range(256)], dtype=np.uint8)[out[:, :240]]
    im = Image.fromarray(rgb)
    logo = pl.construir(t.ROM.read_bytes() if False else pl.ORIGINAL.read_bytes())
    px = im.load()
    for y in range(160):
        for x in range(240):
            if logo[y][x]: px[x, y] = LOGO[logo[y][x]]
    im.resize((720, 480), Image.NEAREST).save(t.RAIZ / "pruebas" / "portada_mezquita_vista.png")
    return tiles, mapa, n, fus


def main():
    rom = bytearray(t.ROM.read_bytes())
    idx, cols = construir()
    tiles, mapa, n, fus = vista(idx, cols, rom)
    print(f"Fondo: {len(cols)} colores, {n} tiles ({fus} fusiones). Vista: pruebas/portada_mezquita_vista.png")
    if "--vista" in sys.argv:
        return
    if len(cols) > N_COLORES:
        sys.exit("Demasiados colores")
    paleta = b"".join(gba(c) for c in cols) + gba((0, 0, 0)) * (N_COLORES - len(cols))
    dt, dm = lz77_comprimir(tiles), lz77_comprimir(mapa)
    o_t = t.buscar_libre(bytes(rom), len(dt), alinear=4); rom[o_t:o_t + len(dt)] = dt
    o_m = t.buscar_libre(bytes(rom), len(dm), alinear=4); rom[o_m:o_m + len(dm)] = dm
    for p in PTRS_TILES: rom[p:p + 4] = struct.pack("<I", 0x08000000 + o_t)
    for p in PTRS_MAPA: rom[p:p + 4] = struct.pack("<I", 0x08000000 + o_m)
    rom[PALETA_FONDO:PALETA_FONDO + 2 * N_COLORES] = paleta
    rom[PALETA_LOGO:PALETA_LOGO + 32] = b"".join(gba(c) for c in LOGO)
    td, md, pd = destello()
    for ptr_, datos in ((PTR_TILES_DESTELLO, td), (PTR_MAPA_DESTELLO, md)):
        comp = lz77_comprimir(datos)
        o = t.buscar_libre(bytes(rom), len(comp), alinear=4); rom[o:o + len(comp)] = comp
        rom[ptr_:ptr_ + 4] = struct.pack("<I", 0x08000000 + o)
    rom[PALETA_DESTELLO:PALETA_DESTELLO + 32] = pd
    print(f"Destello: {len(td) // 32} tiles con la silueta de Dialga (Hoopa eliminado)")
    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-mezquita_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(rom)
    print(f"Tiles 0x{o_t:X} ({len(dt)} B) · mapa 0x{o_m:X} ({len(dm)} B) · paletas escritas en su sitio")


if __name__ == "__main__":
    main()
