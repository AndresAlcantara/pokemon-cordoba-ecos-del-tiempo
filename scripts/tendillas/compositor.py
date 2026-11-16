"""
tendillas/compositor.py
=======================
Un "Photoshop de mapas": recorta piezas de CUALQUIER mapa de Unbound (edificios, fuentes,
bancos, farolas, árboles...), las pega en un lienzo y, al final, convierte el resultado en
un TILESET COMPLETO propio (primario + secundario) y un mapa.

Por qué hace falta (para clase):
* Un mapa solo puede usar 2 tilesets: un primario y un secundario. Las piezas bonitas de
  Unbound están repartidas en muchos tilesets distintos, así que no se pueden mezclar tal cual.
* Solución: trabajamos con IMÁGENES. Pegamos las piezas como dibujos y después el programa:
    1. corta el lienzo en tiles de 8x8 y elimina los repetidos (también volteados);
    2. reparte los colores en 13 paletas de 15 colores (las 0-12 del fondo);
    3. arma los bloques de 16x16 (capa de abajo + capa de arriba) y sus atributos.
  El resultado ocupa las 1024 casillas de tiles de la VRAM (640 del primario + 384 del secundario).

Capas: cada casilla tiene una imagen de ABAJO (suelo, siempre opaca) y otra de ARRIBA
(transparente; se pinta por ENCIMA del jugador: copas de árbol, cabezas de farola...).
"""
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_descomprimir  # noqa: E402

ROM = t.ROM.read_bytes()
P = lambda o: struct.unpack("<I", ROM[o:o + 4])[0] - 0x08000000
H = lambda o: struct.unpack("<H", ROM[o:o + 2])[0]
TABLA_LAYOUTS = 0xB6FB20
N_PRIM = 640
CAPA_NORMAL, CAPA_CUBIERTA, CAPA_PARTIDA = 0, 1, 2


def _tileset(o):
    comp = ROM[o]
    tiles = lz77_descomprimir(ROM, P(o + 4)) if comp else ROM[P(o + 4):P(o + 4) + 0x8000]
    pp = P(o + 8)
    pals = [[((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)
             for c in struct.unpack("<16H", ROM[pp + 32 * p:pp + 32 * p + 32])] for p in range(16)]
    return tiles, pals, P(o + 12), P(o + 20)


class Fuente:
    """Un mapa de Unbound del que recortar piezas (por número de diseño)."""
    _cache = {}

    def __init__(self, layout_id):
        lay = P(TABLA_LAYOUTS + 4 * (layout_id - 1))
        self.w, self.h = struct.unpack("<II", ROM[lay:lay + 8])
        dat = P(lay + 12)
        self.celdas = [[H(dat + 2 * (y * self.w + x)) for x in range(self.w)] for y in range(self.h)]
        t1, t2 = P(lay + 16), P(lay + 20)
        self.tiles1, self.pals1, self.meta1, self.attr1 = _tileset(t1)
        self.tiles2, self.pals2, self.meta2, self.attr2 = _tileset(t2)
        self.pals = self.pals1[:7] + self.pals2[7:13] + self.pals1[13:]
        self.cache = {}

    def _tile(self, e):
        n, pal, hf, vf = e & 0x3FF, e >> 12, (e >> 10) & 1, (e >> 11) & 1
        src, o = (self.tiles1, n * 32) if n < N_PRIM else (self.tiles2, (n - N_PRIM) * 32)
        d = src[o:o + 32].ljust(32, b"\0")
        im = Image.new("RGBA", (8, 8), (0, 0, 0, 0)); px = im.load()
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                v = d[sy * 4 + sx // 2]; v = (v >> 4) if sx & 1 else v & 15
                if v:
                    px[x, y] = (*self.pals[pal][v], 255)
        return im

    def bloque(self, b):
        """(imagen de abajo, imagen de arriba, comportamiento, tipo de capa) de un bloque."""
        if b in self.cache:
            return self.cache[b]
        meta = self.meta1 + 16 * b if b < N_PRIM else self.meta2 + 16 * (b - N_PRIM)
        attr = struct.unpack("<I", ROM[(self.attr1 + 4 * b if b < N_PRIM else self.attr2 + 4 * (b - N_PRIM)):][:4])[0]
        capas = []
        for capa in range(2):
            im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            for k in range(4):
                im.alpha_composite(self._tile(H(meta + 2 * (capa * 4 + k))), ((k % 2) * 8, (k // 2) * 8))
            capas.append(im)
        r = (capas[0], capas[1], attr & 0x1FF, (attr >> 29) & 3)
        self.cache[b] = r
        return r


def fuente(layout_id):
    if layout_id not in Fuente._cache:
        Fuente._cache[layout_id] = Fuente(layout_id)
    return Fuente._cache[layout_id]


class Lienzo:
    def __init__(self, ancho, alto, dy=0):
        """dy: filas extra arriba (todas las coordenadas se desplazan dy filas hacia abajo)."""
        self.dy = dy
        alto += dy
        self.ancho, self.alto = ancho, alto
        self.abajo = Image.new("RGBA", (ancho * 16, alto * 16), (0, 0, 0, 255))
        self.arriba = Image.new("RGBA", (ancho * 16, alto * 16), (0, 0, 0, 0))
        self.pasa = [[True] * ancho for _ in range(alto)]
        self.comport = [[0] * ancho for _ in range(alto)]

    # ---- pegar piezas de Unbound ----
    def pegar(self, layout_id, sx, sy, w, h, dx, dy, fondo=None, color=None, colision=None,
              todo_abajo=False, todo_arriba=False, quitar_colores_de=None):
        """Copia el rectángulo (sx, sy, w, h) del mapa de Unbound 'layout_id' en (dx, dy).
        fondo: bloques del mapa de origen que son "suelo" (hierba, arena...): sus píxeles no se copian,
               así la pieza se apoya sobre NUESTRO suelo.
        color: función (r, g, b) -> (r, g, b) para cambiar los colores (p. ej. tejados a terracota).
        colision: None = la del mapa de origen; True/False = forzarla."""
        f = fuente(layout_id)
        dy += self.dy
        fondos = [f.bloque(b)[0] for b in (fondo or [])]
        # quitar_colores_de: casillas (x, y) del mapa de origen con el suelo de alrededor; todos sus
        # colores se vuelven transparentes (para piezas cuyo suelo no es siempre el mismo bloque)
        colores_fondo = set()
        for (qx, qy) in (quitar_colores_de or []):
            for im in f.bloque(f.celdas[qy][qx] & 0x3FF)[:2]:
                colores_fondo |= {c for c in im.getdata() if c[3]}
        for yy in range(h):
            for xx in range(w):
                celda = f.celdas[sy + yy][sx + xx]
                b = celda & 0x3FF
                ab, ar, comp, capa = f.bloque(b)
                ab, ar = ab.copy(), ar.copy()
                if fondos:
                    ab = _quitar_fondo(ab, fondos)
                if colores_fondo:
                    ab = _quitar_colores(ab, colores_fondo); ar = _quitar_colores(ar, colores_fondo)
                    ar_compl = ar
                else:
                    ar_compl = ar
                if capa == CAPA_CUBIERTA or todo_abajo:          # la capa de arriba también va debajo del jugador
                    ab.alpha_composite(ar_compl); ar_compl = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                if todo_arriba:
                    ar2 = ab.copy(); ar2.alpha_composite(ar_compl); ar_compl = ar2; ab = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                if color:
                    ab, ar_compl = _recolor(ab, color), _recolor(ar_compl, color)
                X, Y = dx + xx, dy + yy
                if not (0 <= X < self.ancho and 0 <= Y < self.alto):
                    continue
                self.abajo.alpha_composite(ab, (X * 16, Y * 16))
                self.arriba.alpha_composite(ar_compl, (X * 16, Y * 16))
                p = not (celda >> 10) & 3 if colision is None else colision
                self.pasa[Y][X] = self.pasa[Y][X] and p if colision is None else p
                if comp:
                    self.comport[Y][X] = comp

    def comportamiento(self, x, y, valor):
        self.comport[y + self.dy][x] = valor

    # ---- dibujos propios ----
    def imagen(self, img, px, py, capa="abajo"):
        """Pega una imagen RGBA en píxeles (px, py)."""
        py += self.dy * 16
        if py < 0:                                   # recortar lo que se sale por arriba
            img = img.crop((0, -py, img.width, img.height)); py = 0
        (self.abajo if capa == "abajo" else self.arriba).alpha_composite(img, (px, py))

    # ---- sombras ----
    def fijar_suelo(self):
        """Apunta los colores que son SUELO: las sombras solo oscurecen esos píxeles (nunca un objeto)."""
        self.colores_suelo = {c for c in self.abajo.getdata()}

    def sombra(self, forma, x0, y0, x1, y1, fuerza=1.0):
        """Oscurece el suelo dentro de una forma ('elipse' o 'rect', en píxeles del plano).
        La luz viene de arriba a la izquierda, así que las sombras se ponen abajo y a la derecha."""
        y0 += self.dy * 16; y1 += self.dy * 16
        px = self.abajo.load()
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, max(1, (x1 - x0) / 2), max(1, (y1 - y0) / 2)
        for y in range(max(0, int(y0)), min(self.abajo.height, int(y1) + 1)):
            for x in range(max(0, int(x0)), min(self.abajo.width, int(x1) + 1)):
                if forma == "elipse" and ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 > 1:
                    continue
                c = px[x, y]
                if c in self.colores_suelo:
                    r, g, b, a = c
                    k = 1 - 0.28 * fuerza
                    px[x, y] = (int(r * k), int(g * (k + 0.02)), int(b * (k + 0.08)), 255)

    def sombra_linea(self, x0, y0, x1, y1, grosor=2):
        pasos = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(pasos):
            x = x0 + (x1 - x0) * i / pasos; y = y0 + (y1 - y0) * i / pasos
            self.sombra("rect", x, y, x + grosor, y + grosor)

    def bloquear(self, x0, y0, x1, y1, pasa=False):
        y0 += self.dy; y1 += self.dy
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.ancho and 0 <= y < self.alto:
                    self.pasa[y][x] = pasa

    def vista(self, escala=1):
        im = self.abajo.copy(); im.alpha_composite(self.arriba)
        return im.resize((im.width * escala, im.height * escala), Image.NEAREST)

    # ---- conversión a tileset ----
    def convertir(self, max_paletas=13):
        return Conversor(self, max_paletas).hacer()


def _quitar_fondo(im, fondos):
    out = im.copy(); po = out.load()
    pf = [f.load() for f in fondos]
    for y in range(16):
        for x in range(16):
            if any(po[x, y] == p[x, y] for p in pf):
                po[x, y] = (0, 0, 0, 0)
    return out


def _quitar_colores(im, colores):
    out = im.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y] in colores:
                px[x, y] = (0, 0, 0, 0)
    return out


def _recolor(im, f):
    out = im.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (*f(r, g, b), 255)
    return out


def a5(c):
    """Color de 8 bits por canal -> 5 bits (lo que de verdad guarda la GBA)."""
    return (c[0] >> 3, c[1] >> 3, c[2] >> 3)


class Conversor:
    def __init__(self, lienzo, max_paletas):
        self.L, self.maxp = lienzo, max_paletas

    def _tiles(self, img, opaco):
        px = img.load(); res = []
        for ty in range(img.height // 8):
            fila = []
            for tx in range(img.width // 8):
                t8 = []
                for y in range(8):
                    for x in range(8):
                        r, g, b, a = px[tx * 8 + x, ty * 8 + y]
                        t8.append(a5((r, g, b)) if (a or opaco) else None)
                fila.append(t8)
            res.append(fila)
        return res

    def hacer(self):
        L = self.L
        abajo = self._tiles(L.abajo, True)
        arriba = self._tiles(L.arriba, False)
        todos = [t8 for fila in abajo + arriba for t8 in fila]
        # 0) un tile de 8x8 solo puede tener 15 colores: si alguno tiene más (dibujos con muchos matices),
        #    se le quitan los menos usados, sustituyéndolos por el color más parecido del propio tile
        for t8 in todos:
            _limitar_tile(t8)
        # 1) reducir colores casi iguales hasta que quepan en las paletas
        umbral = 0
        while True:
            mapa_col = _fusionar_colores(todos, umbral)
            conj = [frozenset(mapa_col[c] for c in t8 if c is not None) for t8 in todos]
            paletas = _empaquetar(conj, self.maxp)
            if paletas is not None:
                break
            umbral += 1
            assert umbral < 12, "demasiados colores incluso fusionando"
        self.umbral = umbral
        # 2) indexar tiles (con volteos) y bloques
        tiles = [bytes(32)]                       # tile 0 = vacío (transparente)
        indice = {bytes(32): (0, 0)}

        def tile_id(t8):
            cs = frozenset(mapa_col[c] for c in t8 if c is not None)
            if not cs:
                return 0
            p = next(i for i, pal in enumerate(paletas) if cs <= pal)
            orden = sorted(paletas[p])
            pos = {c: i + 1 for i, c in enumerate(orden)}
            idx = [pos[mapa_col[c]] if c is not None else 0 for c in t8]
            filas = [idx[8 * y:8 * y + 8] for y in range(8)]
            variantes = ((0x000, idx), (0x400, [v for f in filas for v in f[::-1]]),
                         (0x800, [v for f in filas[::-1] for v in f]), (0xC00, [v for f in filas[::-1] for v in f[::-1]]))
            for volteo, v in variantes:
                d = bytes(v[i] | (v[i + 1] << 4) for i in range(0, 64, 2))
                if (d, p) in indice:
                    return indice[(d, p)][0] | volteo | (p << 12)
            d = bytes(idx[i] | (idx[i + 1] << 4) for i in range(0, 64, 2))
            n = len(tiles); tiles.append(d); indice[(d, p)] = (n, p)
            return n | (p << 12)

        bloques, bloque_id, celdas = [], {}, []
        for by in range(L.alto):
            for bx in range(L.ancho):
                ab = [tile_id(abajo[by * 2 + k // 2][bx * 2 + k % 2]) for k in range(4)]
                ar = [tile_id(arriba[by * 2 + k // 2][bx * 2 + k % 2]) for k in range(4)]
                attr = L.comport[by][bx] | (CAPA_NORMAL << 29)
                clave = (tuple(ab), tuple(ar), attr)
                if clave not in bloque_id:
                    bloque_id[clave] = len(bloques); bloques.append(clave)
                celdas.append(bloque_id[clave] | (0x3000 if L.pasa[by][bx] else 0x0400))
        self.tiles, self.bloques, self.celdas = tiles, bloques, celdas
        self.paletas = [sorted(p) for p in paletas]
        return self

    def informe(self):
        return f"{len(self.tiles)} tiles (máx. 1024), {len(self.bloques)} bloques (máx. 1024), " \
               f"{len(self.paletas)} paletas, fusión de colores {self.umbral}"


def _limitar_tile(t8, maximo=15):
    from collections import Counter
    while True:
        cuenta = Counter(c for c in t8 if c is not None)
        if len(cuenta) <= maximo:
            return
        raro = min(cuenta, key=cuenta.get)
        resto = [c for c in cuenta if c != raro]
        cerca = min(resto, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, raro)))
        for i, c in enumerate(t8):
            if c == raro:
                t8[i] = cerca


def _fusionar_colores(tiles, umbral):
    """Agrupa colores que se diferencian en <= umbral (en 5 bits por canal)."""
    from collections import Counter
    cuenta = Counter(c for t8 in tiles for c in t8 if c is not None)
    total = sum(cuenta.values())
    reps, mapa = [], {}
    for c, n in cuenta.most_common():
        # los colores MUY usados (p. ej. los dos tonos del damero del suelo) nunca se fusionan entre sí:
        # solo los colores poco frecuentes se cambian por uno parecido
        if n > total * 0.01:
            reps.append(c); mapa[c] = c
            continue
        for r in reps:
            if max(abs(c[0] - r[0]), abs(c[1] - r[1]), abs(c[2] - r[2])) <= umbral:
                mapa[c] = r; break
        else:
            reps.append(c); mapa[c] = c
    return mapa


def _empaquetar(conjuntos, maxp):
    """Reparte los conjuntos de colores de los tiles en <= maxp paletas de 15 colores.
    Método "aglomerativo": cada conjunto empieza siendo una paleta y se van uniendo, una y otra vez,
    las dos paletas cuya unión añade MENOS colores nuevos, mientras quepan en 15 colores.
    (Los colores se guardan como bits de un número entero para que sea rápido.)"""
    colores = sorted({c for cj in conjuntos for c in cj})
    bit = {c: 1 << i for i, c in enumerate(colores)}
    mascaras = {sum(bit[c] for c in cj) for cj in conjuntos if cj}
    cuenta = lambda m: bin(m).count("1")
    if any(cuenta(m) > 15 for m in mascaras):
        return None
    pal = sorted(mascaras, key=cuenta, reverse=True)
    pal = [m for k, m in enumerate(pal) if not any((m | o) == o for o in pal[:k])]   # quitar subconjuntos
    while len(pal) > maxp:
        mejor = None
        for a in range(len(pal)):
            ca = cuenta(pal[a])
            for b in range(a + 1, len(pal)):
                u = cuenta(pal[a] | pal[b])
                if u <= 15:
                    coste = u - max(ca, cuenta(pal[b]))
                    if mejor is None or coste < mejor[0]:
                        mejor = (coste, a, b)
                        if coste == 0:
                            break
            if mejor and mejor[0] == 0:
                break
        if mejor is None:
            return None
        _, a, b = mejor
        nueva = pal[a] | pal[b]
        pal = [m for k, m in enumerate(pal) if k not in (a, b) and (m | nueva) != nueva] + [nueva]
    return [frozenset(c for c in colores if m & bit[c]) for m in pal]


def dibujar_conversion(conv, ancho):
    """Dibuja el mapa a partir de lo que REALMENTE se escribirá (tiles + paletas + bloques):
    sirve para comprobar que la conversión de colores no ha estropeado nada."""
    pals = [[(0, 0, 0)] + [(r << 3, g << 3, b << 3) for r, g, b in p] for p in conv.paletas]
    cache = {}

    def tile(e):
        n, p, hf, vf = e & 0x3FF, e >> 12, e & 0x400, e & 0x800
        d = conv.tiles[n]
        im = Image.new("RGBA", (8, 8), (0, 0, 0, 0)); px = im.load()
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                v = d[sy * 4 + sx // 2]; v = (v >> 4) if sx & 1 else v & 15
                if v:
                    px[x, y] = (*pals[p][v], 255)
        return im

    alto = len(conv.celdas) // ancho
    img = Image.new("RGBA", (ancho * 16, alto * 16), (0, 0, 0, 255))
    for i, c in enumerate(conv.celdas):
        b = c & 0x3FF
        if b not in cache:
            ab, ar, _ = conv.bloques[b]
            im = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
            for capa in (ab, ar):
                for k in range(4):
                    if capa[k]:
                        im.alpha_composite(tile(capa[k]), ((k % 2) * 8, (k // 2) * 8))
            cache[b] = im
        img.paste(cache[b], ((i % ancho) * 16, (i // ancho) * 16))
    return img
