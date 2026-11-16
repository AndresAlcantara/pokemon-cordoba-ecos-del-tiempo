"""
tendillas/mapa.py
=================
El PLANO de la Plaza de las Tendillas (orientada al norte) y la calle de la casa.

    y=0..7    fila norte de edificios. En el centro, el edificio del RELOJ.
              Entre medias, la calle que sale hacia el norte (cortada por un guardia).
    y=8..27   la plaza: pavimento claro en damero, la FUENTE con la estatua de Dialga
              (lado este), los SURTIDORES del suelo (lado oeste), naranjos, farolas,
              terrazas con sombrillas y un quiosco.
    y=28..35  fila sur de edificios, con la fachada mirando a la calle de abajo.
              Un pasaje (calle estrecha) une la plaza con esa calle.
    y=36..38  la calle de la casa del protagonista.

CONCEPTOS (para clase)
----------------------
* Un mapa es una cuadrícula de CELDAS de 16 bits:
    bits 0-9  número de bloque · bits 10-11 colisión (0 se pasa, 1 no) · bits 12-15 elevación.
  En suelo normal la elevación es 3 (0x3000); lo que no se pisa lleva 0x0400.
* Los edificios, toldos y árboles se COPIAN en trozos de un mapa de Unbound
  (la ciudad costera, diseño 486) que usa el mismo tileset: así no se dibuja nada desde cero.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import textos as t  # noqa: E402
from tileset import Tileset, anadir_dibujo, anadir_suelo, suelo_damero, N_PRIM  # noqa: E402
import arte  # noqa: E402

ANCHO, ALTO = 38, 39
PASA, MURO = 0x3000, 0x0400
CAPA_CUBIERTA = 0x20000000   # atributo: las dos capas del bloque se pintan DEBAJO de los personajes
LAYOUT_MODELO = 486                       # ciudad costera de Unbound (de aquí copiamos los trozos)

# Posiciones importantes (las usan también los eventos)
FUENTE = (24, 14)                         # esquina superior izquierda de la fuente (7x5)
ESTATUA = (FUENTE[0] + 3, FUENTE[1] + 3)  # casilla donde se coloca el sprite de la estatua
PUERTA_RELOJ = (20, 6)
PUERTA_LAB = (2, 6)
PUERTA_CASA = (7, 34)
CALLE_NORTE = range(15, 18)               # x de la calle que sale al norte
PASAJE = range(15, 18)                    # x del pasaje plaza -> calle de la casa
RELOJ = (20, 4)
SURTIDORES_X, SURTIDORES_Y = (16, 18, 20), (14, 16, 18)
COPIADOS = set()                          # bloques originales que sirven de base a otros (se rellenan al construir)
ARENA = (11, 12, 13, 14, 15)              # colores de arena de la paleta 11 (se quitan del poste de la sombrilla)


def leer_modelo():
    rom = t.ROM.read_bytes()
    P = lambda o: struct.unpack("<I", rom[o:o + 4])[0] - 0x08000000
    lay = P(0xB6FB20 + 4 * (LAYOUT_MODELO - 1))
    w, h = struct.unpack("<II", rom[lay:lay + 8])
    dat = P(lay + 12)
    return [[struct.unpack("<H", rom[dat + 2 * (y * w + x):dat + 2 * (y * w + x) + 2])[0] for x in range(w)] for y in range(h)]


class Plano:
    def __init__(self, ts):
        self.ts = ts
        self.c = [[0] * ANCHO for _ in range(ALTO)]
        self.modelo = leer_modelo()
        self._sobre = {}

    def poner(self, x, y, bloque, pasa=True):
        if 0 <= x < ANCHO and 0 <= y < ALTO:
            self.c[y][x] = bloque | (PASA if pasa else MURO)

    def suelo(self, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.poner(x, y, 0x309 if (x + y) % 2 == 0 else 0x311)

    def sobre_suelo(self, bloque, x, y):
        """Mismo bloque pero con el pavimento de la plaza debajo (en vez de hierba o arena).
        Solo si la capa de abajo es "fondo" del tileset primario; si lleva dibujo propio, no se toca."""
        COPIADOS.add(bloque)
        abajo = [self.ts.entrada(bloque, k) for k in range(4)]
        if any((e & 0x3FF) >= 640 for e in abajo):
            return bloque
        clave = (bloque, (x + y) % 2)
        if clave not in self._sobre:
            arriba = [self.ts.entrada(bloque, 4 + k) for k in range(4)]
            atributo = 0
            if bloque >= 640:
                atributo = struct.unpack("<I", self.ts.attr[4 * (bloque - 640):4 * (bloque - 640) + 4])[0]
            self._sobre[clave] = self.ts.nuevo_bloque(suelo_damero(x, y), arriba, atributo)
        return self._sobre[clave]

    def trozo(self, mx, my, ancho, alto, x0, y0, cambiar_suelo=False, colision=None):
        """Copia un rectángulo del mapa modelo en (x0, y0)."""
        for dy in range(alto):
            for dx in range(ancho):
                celda = self.modelo[my + dy][mx + dx]
                b = celda & 0x3FF
                if cambiar_suelo:
                    b = self.sobre_suelo(b, x0 + dx, y0 + dy)
                pasa = not (celda >> 10) & 3 if colision is None else colision
                self.poner(x0 + dx, y0 + dy, b, pasa)

    # ---- piezas ----
    def edificio(self, x0, y0, puerta=False, ultimo=False):
        """Edificio de 5x8 (tejado, dos plantas y planta baja). Copiado del modelo."""
        mx = 15 if ultimo else 10
        self.trozo(mx, 11, 5, 7, x0, y0, cambiar_suelo=True, colision=False)   # tejado y plantas: no se pisan
        self.trozo(mx, 18, 5, 1, x0, y0 + 7, cambiar_suelo=True)              # zócalo: se pisa
        if puerta:
            self.trozo(23, 17, 3, 2, x0 + 1, y0 + 6, cambiar_suelo=True)  # puerta con escalón
            self.poner(x0 + 2, y0 + 6, self.c[y0 + 6][x0 + 2] & 0x3FF, True)   # la puerta sí se pisa (para entrar)
        # la fila de arriba (borde del tejado) se apoya en el pavimento
        for dx in range(5):
            celda = self.modelo[11][mx + dx]
            self.poner(x0 + dx, y0, self.sobre_suelo(celda & 0x3FF, x0 + dx, y0), False)

    def naranjo(self, x0, y0):
        """Árbol 2x4 en su alcorque de césped (copiado del modelo). No se puede pisar."""
        self.trozo(20, 15, 2, 4, x0, y0, colision=False)

    def farola(self, x, y):
        """Farola de globo: cabeza (se pasa por detrás) y poste (no se pasa)."""
        self.poner(x, y - 1, self.sobre_suelo(0x306, x, y - 1), True)
        self.poner(x, y, self.sobre_suelo(0x30E, x, y), False)

    def sombrilla(self, x0, y0):
        """Sombrilla de terraza 2x2. El poste estaba en la capa de abajo (sobre la arena):
        lo fundimos con la capa de arriba para poder poner el pavimento debajo."""
        for dx, b in ((0, 0x2C3), (1, 0x2C4)):
            self.poner(x0 + dx, y0, self.sobre_suelo(b, x0 + dx, y0), True)
        for dx, b in ((0, 0x2CB), (1, 0x2CC)):
            clave = ("sombrilla", b, (x0 + dx + y0 + 1) % 2)
            if clave not in self._sobre:
                COPIADOS.add(b)
                arriba = [self.ts.entrada(b, 4 + k) for k in range(4)]
                for k in (2, 3):                                   # mitad de abajo: tela + poste
                    poste = self.ts.entrada(b, k)
                    arriba[k] = self.fundir(arriba[k], poste, quitar=ARENA)
                self._sobre[clave] = self.ts.nuevo_bloque(suelo_damero(x0 + dx, y0 + 1), arriba)
            self.poner(x0 + dx, y0 + 1, self._sobre[clave], False)

    def fundir(self, e1, e2, quitar=()):
        """Superpone el tile e1 sobre el e2 (misma paleta) y crea un tile nuevo.
        Los colores de 'quitar' del tile de abajo se vuelven transparentes (p. ej. la arena)."""
        def px(e):
            v = self.ts.tile_px(e & 0x3FF)
            filas = [v[8 * y:8 * y + 8] for y in range(8)]
            if e & 0x400: filas = [f[::-1] for f in filas]
            if e & 0x800: filas = filas[::-1]
            return [c for f in filas for c in f]
        a, b = px(e1), [0 if v in quitar else v for v in px(e2)]
        return self.ts.nuevo_tile([x if x else y for x, y in zip(a, b)]) | (e1 & 0xF000)

    def quiosco(self, x0, y0):
        """Puesto con toldo amarillo 4x3 (copiado del modelo)."""
        self.trozo(12, 31, 4, 3, x0, y0)

    def maceta(self, x, y, flores=True):
        self.poner(x, y, 0x348 if flores else 0x349, False)         # 0x348 maceta con flores, 0x349 tinaja


def construir(libres=(), bloques_libres=()):
    ts = Tileset(libres=libres, bloques_libres=bloques_libres).cordobesa()
    p = Plano(ts)
    p.suelo(0, 0, ANCHO - 1, ALTO - 1)

    # ---- fila norte: 3 edificios, calle, 4 edificios (el 2.º de este grupo es el del reloj) ----
    for i, x in enumerate((0, 5, 10)):
        p.edificio(x, 0, puerta=(x == 0))                      # el de la esquina: laboratorio
    for i, x in enumerate((18, 23, 28, 33)):
        p.edificio(x, 0, puerta=(x == 18), ultimo=(x == 33))
    # reloj en la fachada del edificio central
    rx, ry = RELOJ
    reloj = anadir_dibujo(ts, arte.reloj(), arte.PAL_RELOJ, rx, ry)
    COPIADOS.add(p.c[ry][rx] & 0x3FF)
    abajo = [ts.entrada(p.c[ry][rx] & 0x3FF, k) for k in range(4, 8)]   # la fachada pasa a la capa de abajo
    arriba = [ts.entrada(reloj[(rx, ry)], 4 + k) for k in range(4)]
    p.poner(rx, ry, ts.nuevo_bloque(abajo, arriba), False)
    # bolardos que cierran la calle del norte (el guardia se pone delante)
    for x in CALLE_NORTE:
        p.poner(x, 2, 0x31D, False)

    # ---- la plaza ----
    # franjas oscuras que dividen el pavimento en grandes cuadros, y dos mosaicos de estrella
    fh = anadir_suelo(ts, arte.franja(True), arte.PAL_SUELO)[0][0]
    fv = anadir_suelo(ts, arte.franja(False), arte.PAL_SUELO)[0][0]
    fc = anadir_suelo(ts, arte.franja(cruce=True), arte.PAL_SUELO)[0][0]
    LINEAS_X, LINEAS_Y = (2, 13, 21, 35), (12, 22)
    for y in range(8, 28):
        for x in LINEAS_X:
            p.poner(x, y, fc if y in LINEAS_Y else fv)
    for y in LINEAS_Y:
        for x in range(0, ANCHO):
            if x not in LINEAS_X:
                p.poner(x, y, fh)
    mos = anadir_suelo(ts, arte.mosaico(), arte.PAL_SUELO)
    for mx0, my0 in ((6, 15),):
        for dy in range(3):
            for dx in range(3):
                p.poner(mx0 + dx, my0 + dy, mos[dy][dx])
    fuente = anadir_dibujo(ts, arte.fuente(), arte.PAL_FUENTE, *FUENTE, atributo=CAPA_CUBIERTA)
    for (x, y), b in fuente.items():
        p.poner(x, y, b, False)
    # surtidores del suelo delante de la estatua: 3 columnas x 3 filas
    sur = anadir_dibujo(ts, arte.surtidor(), arte.PAL_FUENTE, 0, 0, atributo=CAPA_CUBIERTA)[(0, 0)]
    sur2 = anadir_dibujo(ts, arte.surtidor(), arte.PAL_FUENTE, 1, 0, atributo=CAPA_CUBIERTA)[(1, 0)]
    for y in SURTIDORES_Y:
        for x in SURTIDORES_X:
            p.poner(x, y, sur if (x + y) % 2 == 0 else sur2, True)
    # macetas alrededor de la fuente
    for x, y in ((23, 15), (23, 18), (31, 15), (31, 18)):
        p.maceta(x, y)
    # naranjos: fila del sur de la plaza (dejando libre el pasaje) y los dos laterales
    for x in (0, 3, 6, 9, 12, 19, 22, 25, 28, 31, 34):
        p.naranjo(x, 23)
    for y in (9, 15):
        p.naranjo(0, y)
        p.naranjo(36, y)
    # farolas
    for x, y in ((14, 10), (22, 10), (14, 20), (33, 11), (4, 14), (22, 21), (10, 21), (30, 21)):
        p.farola(x, y)
    # terraza de café delante del edificio del noroeste
    for x in (4, 7, 10):
        p.sombrilla(x, 9)
    # quiosco en la esquina sureste
    p.quiosco(32, 19)

    # ---- fila sur (fachadas hacia la calle de la casa) ----
    for x in (0, 5, 10):
        p.edificio(x, 28, puerta=(x == 5))                     # x=5: casa del protagonista
    for x in (18, 23, 28, 33):
        p.edificio(x, 28, ultimo=(x == 33))
    # macetas con flores junto a la puerta de casa (como en los patios)
    for x in (5, 9):
        p.maceta(x, 36)
    for x, y in ((12, 37), (26, 37)):
        p.farola(x, y)
    # extremos de la calle cerrados con bolardos
    for y in (36, 37, 38):
        p.poner(0, y, 0x31D, False)
        p.poner(ANCHO - 1, y, 0x31D, False)
    return ts, p


def construir_optimizado():
    """Dos pasadas: la 1.ª dice qué tiles del original no usa el mapa; la 2.ª los reaprovecha."""
    ts, p = construir()
    bloques = {c & 0x3FF for fila in p.c for c in fila}
    usados = ts.tiles_usados(bloques)
    original = Tileset()
    libres = [n for n in range(len(original.tiles) // 32) if n not in usados]
    # bloques del original que el mapa no pone directamente NI copian los bloques nuevos
    bloques_libres = [n for n in range(original.n_bloques) if N_PRIM + n not in bloques and N_PRIM + n not in COPIADOS]
    return construir(libres, bloques_libres)


if __name__ == "__main__":
    import os
    ts, p = construir_optimizado()
    celdas = [c for fila in p.c for c in fila]
    img = ts.dibujar_mapa(celdas, ANCHO)
    print("tiles", len(ts.tiles) // 32, "bloques", ts.n_bloques)
    salida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("TEMP", "."), "tendillas.png")
    img.save(salida)
    print("Vista previa:", salida)
