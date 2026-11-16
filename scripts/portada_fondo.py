"""
portada_fondo.py
================
Nuevo fondo de la portada (capa BG1, 8 bits por píxel, paleta de 256 colores):
  1. quita la silueta del legendario de Unbound (y sus aros dorados) y rellena
     el hueco con la nebulosa, reflejando la textura de los lados;
  2. dibuja la silueta de DIALGA (a partir de su sprite frontal de Unbound,
     ampliado y suavizado) con un borde blanco de 1 píxel, como la original;
  3. cambia "SKELI" por "RANDES" con la misma fuente que "PRESS START".

Datos (cargados por la rutina de la portada):
  tiles 8bpp LZ77 en 0x1FC94FC  (punteros en 0x1ECE508 y 0x1ECE74C)
  mapa       LZ77 en 0x1FCED50  (punteros en 0x1ECE510 y 0x1ECE754)
  paleta en crudo en 0x1FCF1EC  (no se cambia: solo se usan colores que ya existen)

Uso:  python scripts/portada_fondo.py [--vista] [--dialga]
  Por defecto SOLO cambia "SKELI" por "RANDES". --dialga activa la silueta de
  Dialga (EXPERIMENTAL: el relleno de la nebulosa aún deja parches; no usar todavía).
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_comprimir, lz77_descomprimir, TABLA_FRONTAL, TABLA_PAL_NORMAL  # noqa: E402

ORIGINAL = t.RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba"
TILES, MAPA, PALETA, N_COLORES = 0x1FC94FC, 0x1FCED50, 0x1FCF1EC, 208
PTRS_TILES, PTRS_MAPA = (0x1ECE508, 0x1ECE74C), (0x1ECE510, 0x1ECE754)
NEGRO, BORDE = 149, 160              # índices de la silueta original y de su borde blanco
DIALGA = 536
MAX_TILES = 512                      # hasta 0x8000, donde empiezan los tiles del logo


def decodificar(rom):
    tiles = lz77_descomprimir(rom, TILES); mapa = lz77_descomprimir(rom, MAPA)
    img = np.zeros((160, 256), dtype=np.uint8)
    for ty in range(20):
        for tx in range(32):
            ent = struct.unpack("<H", mapa[2 * (ty * 32 + tx):2 * (ty * 32 + tx) + 2])[0]
            n, hf, vf = ent & 0x3FF, (ent >> 10) & 1, (ent >> 11) & 1
            b = np.frombuffer(tiles[n * 64:n * 64 + 64], dtype=np.uint8).reshape(8, 8)
            if hf: b = b[:, ::-1]
            if vf: b = b[::-1, :]
            img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = b
    pal = [struct.unpack("<H", rom[PALETA + 2 * i:PALETA + 2 * i + 2])[0] for i in range(N_COLORES)]
    cols = np.array([((c & 31) * 8, ((c >> 5) & 31) * 8, ((c >> 10) & 31) * 8) for c in pal])
    return img, cols


def dilatar(m, r=1):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def rellenar(img, mascara):
    """Rellena cada fila reflejando (en zig-zag) los píxeles libres más cercanos."""
    out = img.copy()
    for y in range(160):
        fila = mascara[y, :240]
        x = 0
        while x < 240:
            if not fila[x]:
                x += 1; continue
            a = x
            while x < 240 and fila[x]: x += 1
            b = x                                   # tramo enmascarado [a, b)
            for xx in range(a, b):
                if (xx - a <= b - 1 - xx and a > 0) or b >= 240:
                    L = a; d = xx - a; k = d % (2 * L)
                    src = a - 1 - k if k < L else k - L
                else:
                    L = 240 - b; d = b - 1 - xx; k = d % (2 * L)
                    src = b + k if k < L else 239 - (k - L)
                out[y, xx] = img[y, src]
    return out


def silueta_dialga(rom, alto=132):
    p = struct.unpack("<I", rom[TABLA_FRONTAL + 8 * DIALGA:TABLA_FRONTAL + 8 * DIALGA + 4])[0] - 0x08000000
    d = lz77_descomprimir(rom, p)
    m = np.zeros((64, 64), dtype=np.uint8)
    for tl in range(64):
        tx, ty = (tl % 8) * 8, (tl // 8) * 8
        for i in range(32):
            b = d[tl * 32 + i]
            m[ty + i // 4, tx + (i % 4) * 2] = 255 if b & 15 else 0
            m[ty + i // 4, tx + (i % 4) * 2 + 1] = 255 if b >> 4 else 0
    ys, xs = np.nonzero(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    esc = alto / m.shape[0]
    im = Image.fromarray(m).resize((round(m.shape[1] * esc), alto), Image.BICUBIC)   # suavizado
    return np.array(im) > 110


# --- letras: copiadas de "PRESS START" (filas 150-154 del fondo) y N, D dibujadas igual ---
def glifos(img):
    banda = img[150:155, 70:175]
    claro = banda >= 160                       # índices 160-166: blancos y grises del texto
    cols = np.nonzero(claro.any(0))[0]
    grupos, g = [], [cols[0]]
    for c in cols[1:]:
        if c == g[-1] + 1: g.append(c)
        else: grupos.append(g); g = [c]
    grupos.append(g)
    letras = [banda[:, g[0]:g[-1] + 1] * claro[:, g[0]:g[-1] + 1] for g in grupos]
    # P, R, E, S salen limpias; "TART" sale pegada (las letras se tocan), así que la A se dibuja a mano
    P, R, E, S = letras[:4]
    colores = [int(np.max(E[f])) for f in range(5)]       # color de cada fila (degradado)
    def hacer(patron):
        arr = np.zeros((5, len(patron[0])), dtype=np.uint8)
        for f, linea in enumerate(patron):
            for c, ch in enumerate(linea):
                if ch == "#": arr[f, c] = colores[f]
        return arr
    A = hacer(["..###..", ".##.##.", "##...##", "#######", "##...##"])
    N = hacer(["##...##", "###..##", "##.#.##", "##..###", "##...##"])
    D = hacer(["######.", "##...##", "##...##", "##...##", "######."])
    return {"R": R, "A": A, "N": N, "D": D, "E": E, "S": S}


def construir(rom, con_dialga=False):
    img, cols = decodificar(rom)
    br = cols.sum(1)
    if not con_dialga:
        return poner_nombre(img, rom), cols
    # 1. máscara de la silueta: negro + grises oscuros + dorados, ampliada 1 px (el borde blanco)
    oro = (cols[:, 0] >= 120) & (cols[:, 1] >= 80) & (cols[:, 2] <= 70)
    base = np.isin(img, [NEGRO, 148]) | oro[img]
    zona = np.zeros_like(base); zona[:, 15:225] = True
    mascara = dilatar(base & zona, 2)
    texto = (img >= 160) & (img <= 166)
    texto_press = np.zeros_like(texto); texto_press[149:156, 70:175] = texto[149:156, 70:175]
    mascara &= ~texto_press
    mascara[:, 240:] = False
    img = rellenar(img, mascara)
    # 2. Dialga
    sil = silueta_dialga(rom)
    h, w = sil.shape
    ox, oy = 120 - w // 2, 160 - h + 6
    lienzo = np.zeros((160 + 20, 256), dtype=bool)
    ys, xs = np.nonzero(sil)
    ok = (ys + oy >= 0) & (ys + oy < 160) & (xs + ox >= 0) & (xs + ox < 240)
    lienzo[ys[ok] + oy, xs[ok] + ox] = True
    lienzo = lienzo[:160]
    borde = dilatar(lienzo, 1) & ~lienzo
    img[borde & ~texto_press] = BORDE
    img[lienzo & ~texto_press] = NEGRO
    return poner_nombre(img, rom), cols


def poner_nombre(img, rom):
    # "SKELI" -> "RANDES": borrar copiando la nebulosa de debajo (espejo en la fila 8) y escribir
    for y in range(2, 9):
        img[y, 0:40] = img[16 - y, 0:40]
    g = glifos(decodificar(rom)[0])
    x = 3
    for letra in "RANDES":
        arr = g[letra]
        for f in range(5):
            for c in range(arr.shape[1]):
                if arr[f, c]: img[3 + f, x + c] = arr[f, c]
        x += arr.shape[1] + 1
    return img


PROTEGIDAS = set(range(18 * 32, 20 * 32))   # filas de tiles del texto inferior: nunca se fusionan


def a_tiles(img):
    """Imagen 8bpp -> tiles únicos (reutilizando tiles volteados) y mapa 32x20.
    Si hay más de MAX_TILES, fusiona los tiles más parecidos entre sí."""
    bloques = [img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] for ty in range(20) for tx in range(32)]
    def variantes(b):
        return [(b, 0), (b[:, ::-1], 1 << 10), (b[::-1, :], 1 << 11), (b[::-1, ::-1], 3 << 10)]
    unicos, indice, ref = [], {}, []
    for b in bloques:
        hallado = None
        for v, fl in variantes(b):
            k = v.tobytes()
            if k in indice: hallado = (indice[k], fl); break
        if hallado is None:
            indice[b.tobytes()] = len(unicos); hallado = (len(unicos), 0); unicos.append(b.copy())
        ref.append(hallado)
    fusiones = 0
    if len(unicos) > MAX_TILES:
        arr = np.array([u.reshape(-1) for u in unicos]).astype(np.int16)
        usos = np.bincount([r[0] for r in ref], minlength=len(unicos))
        destino = list(range(len(unicos)))
        vivos = set(range(len(unicos)))
        intocables = {ref[k][0] for k in PROTEGIDAS if k < len(ref)}
        while len(vivos) > MAX_TILES - 2:
            vl = sorted(vivos)
            sub = arr[vl]
            dif = (sub[:, None, :] != sub[None, :, :]).sum(2) + np.eye(len(vl), dtype=np.int64) * 999
            prot = np.array([v in intocables for v in vl])
            dif[prot, :] += 999; dif[:, prot] += 999
            i, j = np.unravel_index(np.argmin(dif + usos[vl][None, :] * 0), dif.shape)
            a, b = vl[i], vl[j]
            quitar = b if usos[b] <= usos[a] else a
            queda = a if quitar == b else b
            destino[quitar] = queda; vivos.discard(quitar); usos[queda] += usos[quitar]; fusiones += 1
        def raiz(k):
            while destino[k] != k: k = destino[k]
            return k
        nuevos = {k: n for n, k in enumerate(sorted(vivos))}
        ref = [(nuevos[raiz(r[0])], r[1]) for r in ref]
        unicos = [unicos[k] for k in sorted(vivos)]
    tiles = b"".join(u.tobytes() for u in unicos)
    mapa = b"".join(struct.pack("<H", n | fl) for n, fl in ref)
    return tiles, mapa, len(unicos), fusiones


def main():
    original = ORIGINAL.read_bytes()
    img, cols = construir(original, con_dialga="--dialga" in sys.argv)
    Image.fromarray(cols[img[:, :240]].astype(np.uint8)).resize((720, 480), Image.NEAREST) \
        .save(t.RAIZ / "pruebas" / "fondo_vista.png")
    Image.fromarray(img).save(t.RAIZ / "pruebas" / "fondo_indices.png")
    tiles, mapa, n, fus = a_tiles(img)
    print(f"Fondo nuevo: {n} tiles ({fus} fusiones de tiles parecidos); máximo {MAX_TILES}.")
    if "--vista" in sys.argv:
        print("Vista previa: pruebas/fondo_vista.png"); return
    rom = bytearray(t.ROM.read_bytes())
    dt, dm = lz77_comprimir(tiles), lz77_comprimir(mapa)
    o_t = t.buscar_libre(bytes(rom), len(dt), alinear=4); rom[o_t:o_t + len(dt)] = dt
    o_m = t.buscar_libre(bytes(rom), len(dm), alinear=4); rom[o_m:o_m + len(dm)] = dm
    for p in PTRS_TILES: rom[p:p + 4] = struct.pack("<I", 0x08000000 + o_t)
    for p in PTRS_MAPA: rom[p:p + 4] = struct.pack("<I", 0x08000000 + o_m)
    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-fondo_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(rom)
    print(f"Tiles en 0x{o_t:X} ({len(dt)} B) · mapa en 0x{o_m:X} ({len(dm)} B)")


if __name__ == "__main__":
    main()
