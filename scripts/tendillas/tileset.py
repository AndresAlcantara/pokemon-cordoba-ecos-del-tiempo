"""
tendillas/tileset.py
====================
Tileset SECUNDARIO nuevo para la Plaza de las Tendillas.

Parte del tileset de la ciudad costera de Unbound (0x744D8C: pavimento gris claro,
farolas de globo, sombrillas, macetas, bancos...) y lo cambia:
  1. Paletas "cordobesas": fachadas crema, tejados de terracota.
  2. Bloques nuevos en los huecos libres: la fuente redonda de la estatua,
     los surtidores del suelo y el reloj de la fachada.

CONCEPTOS (para clase)
----------------------
* Un TILESET tiene: tiles (dibujos de 8x8), paletas (16 colores cada una),
  BLOQUES o metatiles (16x16 = 2 capas x 4 tiles) y ATRIBUTOS de cada bloque
  (qué es: suelo, agua, hierba...).
* El primario (bloques 0-639) es común a muchos mapas; el secundario (640+) es
  propio de cada zona. Por eso solo tocamos el SECUNDARIO, y en una COPIA.
* En el secundario solo cuentan las paletas 7 a 12.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_descomprimir  # noqa: E402

PRIMARIO = 0x2D4A94
BASE = 0x744D8C            # secundario de la ciudad costera de Unbound
N_PRIM = 640


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Cambios de color: paleta -> {índice: color nuevo}
CAMBIOS_PALETA = {
    7: {10: "f0c8a0", 11: "e0a878", 12: "d08c60", 13: "c07450", 14: "a86040", 15: "884830"},   # tejados: terracota
    8: {6: "f0e0b8", 7: "e0c898", 8: "c8a878", 9: "806040"},                                     # fachadas: crema
}


class Tileset:
    """Copia editable de un tileset secundario."""

    def __init__(self, base=BASE, libres=(), bloques_libres=()):
        """libres / bloques_libres: tiles y bloques del original que el mapa no usa y se pueden
        reaprovechar para los dibujos nuevos (ver construir_optimizado en mapa.py)."""
        self.libres = sorted(libres)
        self.bloques_libres = sorted(bloques_libres)
        rom = t.ROM.read_bytes()
        P = lambda o: struct.unpack("<I", rom[o:o + 4])[0] - 0x08000000
        self.rom = rom
        self.tiles = bytearray(lz77_descomprimir(rom, P(base + 4)))
        pal = P(base + 8)
        self.paletas = [[((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)
                         for c in struct.unpack("<16H", rom[pal + 32 * p:pal + 32 * p + 32])] for p in range(16)]
        meta, attr = P(base + 12), P(base + 20)
        self.n_bloques = (attr - meta) // 16
        self.meta = bytearray(rom[meta:meta + 16 * self.n_bloques])
        self.attr = bytearray(rom[attr:attr + 4 * self.n_bloques])
        # primario (solo lectura, para dibujar)
        self.prim_tiles = lz77_descomprimir(rom, P(PRIMARIO + 4))
        pp = P(PRIMARIO + 8)
        self.prim_pal = [[((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)
                          for c in struct.unpack("<16H", rom[pp + 32 * p:pp + 32 * p + 32])] for p in range(16)]
        self.prim_meta = rom[P(PRIMARIO + 12):P(PRIMARIO + 12) + 16 * N_PRIM]
        self.prim_attr = rom[P(PRIMARIO + 20):P(PRIMARIO + 20) + 4 * N_PRIM]

    def tiles_usados(self, bloques):
        """Tiles del secundario que usan estos bloques."""
        usados = set()
        for b in bloques:
            for k in range(8):
                e = self.entrada(b, k)
                if (e & 0x3FF) >= N_PRIM and (e != 0):
                    usados.add((e & 0x3FF) - N_PRIM)
        return usados

    # ---- colores ----
    def cordobesa(self):
        for p, cambios in CAMBIOS_PALETA.items():
            for i, h in cambios.items():
                self.paletas[p][i] = rgb(h)
        return self

    def paletas_juego(self):
        """Las 16 paletas tal como las ve el juego en este mapa."""
        return self.prim_pal[:7] + self.paletas[7:13] + self.prim_pal[13:]

    # ---- tiles y bloques nuevos ----
    def nuevo_tile(self, pixeles):
        """pixeles: 64 índices (0-15). Devuelve el número de tile (desde 640) con los bits de volteo.
        Si ya existe el mismo dibujo, o volteado en horizontal/vertical, lo reutiliza (ahorra espacio)."""
        empaqueta = lambda px: bytes((px[i] & 15) | ((px[i + 1] & 15) << 4) for i in range(0, 64, 2))
        filas = [pixeles[8 * y:8 * y + 8] for y in range(8)]
        variantes = {
            0x000: empaqueta(pixeles),
            0x400: empaqueta([v for f in filas for v in f[::-1]]),          # volteo horizontal
            0x800: empaqueta([v for f in filas[::-1] for v in f]),          # volteo vertical
            0xC00: empaqueta([v for f in filas[::-1] for v in f[::-1]]),    # los dos
        }
        libres = set(self.libres)
        existentes = {bytes(self.tiles[32 * n:32 * n + 32]): n for n in range(len(self.tiles) // 32 - 1, -1, -1)
                      if n not in libres}
        for volteo, datos in variantes.items():
            if datos in existentes:
                return (N_PRIM + existentes[datos]) | volteo
        datos = variantes[0]
        if self.libres:                                   # reaprovechar un hueco
            n = self.libres.pop(0)
            self.tiles[32 * n:32 * n + 32] = datos
            return N_PRIM + n
        self.tiles += datos
        n = len(self.tiles) // 32 - 1
        assert n < 384, "no caben más tiles en el secundario"
        return N_PRIM + n

    def nuevo_bloque(self, abajo, arriba, atributo=0x00000000):
        """abajo/arriba: 4 entradas (tile | paleta<<12 | volteos). Devuelve el número de bloque."""
        if self.bloques_libres:                           # reaprovechar un bloque que el mapa no usa
            n = self.bloques_libres.pop(0)
            self.meta[16 * n:16 * n + 16] = struct.pack("<8H", *abajo, *arriba)
            self.attr[4 * n:4 * n + 4] = struct.pack("<I", atributo)
            return N_PRIM + n
        self.meta += struct.pack("<8H", *abajo, *arriba)
        self.attr += struct.pack("<I", atributo)
        self.n_bloques += 1
        assert self.n_bloques <= 384
        return N_PRIM + self.n_bloques - 1

    # ---- dibujo (para previsualizar) ----
    def entrada(self, b, k):
        if b < N_PRIM:
            return struct.unpack("<H", self.prim_meta[16 * b + 2 * k:16 * b + 2 * k + 2])[0]
        return struct.unpack("<H", self.meta[16 * (b - N_PRIM) + 2 * k:16 * (b - N_PRIM) + 2 * k + 2])[0]

    def tile_px(self, n):
        src, o = (self.prim_tiles, n * 32) if n < N_PRIM else (self.tiles, (n - N_PRIM) * 32)
        d = src[o:o + 32].ljust(32, b"\0")
        return [(d[i // 2] >> 4) if i & 1 else d[i // 2] & 15 for i in range(64)]

    def dibujar_bloque(self, b):
        from PIL import Image
        pals = self.paletas_juego()
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 255)); px = im.load()
        for capa in range(2):
            for k in range(4):
                e = self.entrada(b, capa * 4 + k)
                pix = self.tile_px(e & 0x3FF); pal = pals[e >> 12]
                hf, vf = (e >> 10) & 1, (e >> 11) & 1
                for y in range(8):
                    for x in range(8):
                        v = pix[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                        if v:
                            px[(k % 2) * 8 + x, (k // 2) * 8 + y] = (*pal[v], 255)
        return im

    def dibujar_mapa(self, celdas, ancho):
        from PIL import Image
        alto = len(celdas) // ancho
        img = Image.new("RGB", (ancho * 16, alto * 16)); cache = {}
        for i, c in enumerate(celdas):
            b = c & 0x3FF
            if b not in cache:
                cache[b] = self.dibujar_bloque(b)
            img.paste(cache[b], ((i % ancho) * 16, (i // ancho) * 16))
        return img


# Suelo de la plaza (capa de abajo de los bloques 0x309 y 0x311, que se alternan en damero)
SUELO_A = (0x9EFB, 0x9AFB, 0x96FB, 0x92FB)     # bloque 0x309
SUELO_B = (0x970B, 0x930B, 0x9F0B, 0x9B0B)     # bloque 0x311


def suelo_damero(bx, by):
    """Qué suelo va debajo en la casilla (bx, by) del mapa para seguir el damero."""
    return SUELO_A if (bx + by) % 2 == 0 else SUELO_B


def anadir_dibujo(ts, matriz, paleta, x0, y0, atributo=0):
    """Corta un dibujo (matriz de índices, múltiplo de 16) en bloques nuevos colocados en (x0, y0) del mapa.
    Devuelve {(bx, by): bloque} con coordenadas del mapa."""
    alto, ancho = len(matriz) // 16, len(matriz[0]) // 16
    bloques = {}
    for by in range(alto):
        for bx in range(ancho):
            arriba = []
            for k in range(4):
                tx, ty = bx * 16 + (k % 2) * 8, by * 16 + (k // 2) * 8
                pix = [matriz[ty + y][tx + x] for y in range(8) for x in range(8)]
                if any(pix):
                    arriba.append(ts.nuevo_tile(pix) | (paleta << 12))
                else:
                    arriba.append(0)
            debajo = suelo_damero(x0 + bx, y0 + by)
            bloques[(x0 + bx, y0 + by)] = ts.nuevo_bloque(debajo, arriba, atributo)
    return bloques


def anadir_suelo(ts, matriz, paleta):
    """Como anadir_dibujo, pero el dibujo va en la capa de ABAJO y es opaco (un suelo nuevo).
    Devuelve una matriz de bloques [fila][columna]."""
    alto, ancho = len(matriz) // 16, len(matriz[0]) // 16
    res = []
    for by in range(alto):
        fila = []
        for bx in range(ancho):
            abajo = []
            for k in range(4):
                tx, ty = bx * 16 + (k % 2) * 8, by * 16 + (k // 2) * 8
                abajo.append(ts.nuevo_tile([matriz[ty + y][tx + x] for y in range(8) for x in range(8)]) | (paleta << 12))
            fila.append(ts.nuevo_bloque(abajo, [0, 0, 0, 0]))
        res.append(fila)
    return res
