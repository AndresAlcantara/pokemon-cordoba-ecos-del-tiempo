"""
tendillas/plaza.py
==================
La Plaza de las Tendillas, versión 2, montada con el COMPOSITOR (piezas de muchos mapas de Unbound).

Plano (norte arriba):
    y=0..10   fila norte de edificios clásicos de 3-4 plantas. A la IZQUIERDA, el edificio del
              RELOJ con su torre; en la esquina derecha, el edificio con CÚPULA (como el de la Unión
              y el Fénix). En medio, la calle que sale al norte (cortada por el guardia).
    y=11..30  la plaza: la FUENTE con la estatua de Dialga sobre un PEDESTAL alto y un parterre de
              flores; a izquierda y derecha, las MINIFUENTES de chorros; mosaicos, terraza de café,
              quioscos, bancos, farolas negras, naranjos y palmeras.
    y=31..38  fila sur de edificios (la fachada mira a la calle de la casa). Pasaje en el centro.
    y=39..41  la calle de la casa del protagonista.

Piezas de Unbound usadas (diseño n.º: mapa):
    87  ciudad del puerto  -> edificios de piedra con ventanas en arco
    81  plaza del mercado  -> puestos con toldo de rayas
    155 plaza moderna      -> farolas negras
    486 ciudad costera     -> pavimento, sombrillas y tumbonas, macetas
    510 ciudad del desierto-> palmeras, bancos de madera, árboles redondos
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compositor as C  # noqa: E402

ANCHO, ALTO = 37, 45                       # 37 de ancho: el eje (calle norte, fuente, pasaje) queda en el centro
DY = 3                                     # filas extra arriba para la torre del reloj y la cúpula
PUERTO, MERCADO, MODERNA, COSTA, DESIERTO = 87, 81, 155, 486, 510
HIERBA_DESIERTO = [0xBE, 0xC6, 0x24C, 0x1]      # bloques de "suelo" de cada mapa: no se copian
SUELO_MODERNA = [0x281]
BOLARDO = (12, 30)                         # casilla del mapa 486 con un bolardo blanco (bloque 0x31D)
SUELO_FAROLA = [(13, 12), (15, 12), (13, 13), (15, 13), (13, 14), (15, 14), (16, 13), (12, 13)]

# ---- posiciones que usan también los eventos ----
EJE = 18                                   # columna central: calle norte (17-19), fuente y pasaje sur
FUENTE = (EJE - 5, 14)                     # esquina sup. izq. de la fuente (11x9 bloques)
ESTATUA = (EJE, FUENTE[1] + 2)             # casilla del sprite de la estatua (sobre la cornisa del pedestal, en el centro del pilón)
CHORROS_IZQ = [(x, y) for y in (18, 21) for x in (8, 10)]
CHORROS_DER = [(2 * EJE - x, y) for x, y in CHORROS_IZQ]          # simétricos respecto al eje
PUERTA_RELOJ = (3, 19)                     # el edificio del reloj está en el lateral OESTE
PUERTA_LAB = (14, 9)
MARCO_X, MARCO_Y = (EJE - 11, EJE + 11), (12, 26)   # marco de franjas del pavimento
PUERTA_CASA = (7, 37)
CALLE_NORTE = range(17, 20)
GUARDIA = (18, 6)
FILA_GUARDIA = 8                           # fila del trigger del guardia

# ---- colores (RGB) ----
def rampa(cols, guardar_azul=True):
    def f(r, g, b):
        if guardar_azul and b > r + 24 and b > g:
            return (r, g, b)
        L = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        return cols[min(len(cols) - 1, int(L * len(cols)))]
    return f


CREMA = [(56, 40, 32), (104, 80, 56), (168, 136, 96), (208, 180, 132), (232, 212, 168), (244, 232, 200), (252, 248, 236)]
OCRE = [(56, 40, 32), (128, 72, 32), (192, 120, 56), (224, 160, 80), (240, 188, 112), (248, 212, 152), (252, 248, 236)]
BLANCO = [(56, 40, 32), (96, 96, 104), (160, 160, 160), (200, 200, 196), (224, 224, 216), (240, 240, 232), (252, 248, 236)]
ROSA = [(56, 40, 32), (144, 64, 72), (208, 120, 120), (232, 160, 156), (240, 184, 180), (248, 208, 204), (252, 248, 236)]   # todas las gamas comparten contorno y blanco
TEJA = [(64, 32, 24), (112, 48, 32), (160, 72, 48), (192, 100, 64), (216, 136, 96), (232, 168, 128), (244, 200, 168)]
PIZARRA = [(32, 36, 48), (56, 64, 80), (80, 92, 112), (104, 120, 140), (136, 152, 168), (168, 184, 196), (208, 216, 224)]
HIERRO = (36, 36, 44)

PIEDRA = [(48, 64, 72), (104, 120, 136), (160, 168, 168), (200, 208, 200), (232, 232, 224), (248, 248, 240)]
AGUA = [(48, 128, 216), (64, 160, 248), (56, 184, 248), (120, 200, 248), (200, 224, 248), (240, 248, 248)]
FLOR = [(200, 40, 40), (240, 96, 48), (248, 160, 48), (248, 216, 96)]
HOJA = [(32, 80, 40), (56, 120, 56), (88, 160, 72)]
SUELO = [(0xC0, 0xD0, 0xF0), (0xB8, 0xC8, 0xE0), (0xA8, 0xC0, 0xD8), (0xA0, 0xB0, 0xD0), (0x98, 0xA8, 0xC0), (0x98, 0xA0, 0xA8)]


def dentro(x, y, cx, cy, rx, ry):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def contorno(img, color):
    """Pone contorno oscuro a todo lo opaco que toque un transparente (estilo Pokémon)."""
    px = img.load(); w, h = img.size
    base = [[px[x, y][3] for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if base[y][x] and any(not (0 <= x + dx < w and 0 <= y + dy < h) or not base[y + dy][x + dx]
                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (*color, 255)
    return img


# ===================== dibujos propios =====================
def fuente_img():
    """Fuente de 11x9 bloques vista en perspectiva 3/4 (como todo en Pokémon): se ven la cara de
    ARRIBA y la cara de DELANTE de cada pieza. El volumen sale de tres cosas:
      * caras de arriba más claras y caras delanteras más oscuras (luz desde arriba a la izquierda);
      * el muro del pilón y del parterre, que asoma por delante;
      * sombras: la del pedestal sobre el agua y las flores, y la línea bajo la cornisa."""
    W, H = 176, 144
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = im.load()
    cx, cy = 88, 78
    RX, RY, MURO = 86, 54, 10              # pretil exterior
    rx, ry = 77, 47                        # borde interior (agua)

    def pon(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = (*c, 255)

    # --- pilón: muro delantero, pretil y agua ---
    for y in range(H):
        for x in range(W):
            ext = dentro(x, y, cx, cy, RX, RY)
            if y >= cy and not ext and dentro(x, y - MURO, cx, cy, RX, RY):
                t = (x - (cx - RX)) / (2 * RX)                       # izquierda clara, derecha oscura
                c = PIEDRA[3] if t < 0.35 else PIEDRA[2] if t < 0.75 else PIEDRA[1]
                if y >= cy + RY + MURO - 2:
                    c = PIEDRA[1]
                pon(x, y, c)
            elif ext and not dentro(x, y, cx, cy, rx, ry):
                ang = math.atan2(y - cy, x - cx)                      # pretil: luz arriba-izquierda
                c = PIEDRA[5] if -2.6 < ang < -0.9 else PIEDRA[4] if -2.9 < ang < 0.6 else PIEDRA[3]
                pon(x, y, c)
            elif dentro(x, y, cx, cy, rx, ry):
                # pared interior del pilón (se ve en el lado de atrás) y agua con profundidad
                if not dentro(x, y - 6, cx, cy, rx, ry):
                    pon(x, y, PIEDRA[2] if not dentro(x, y - 3, cx, cy, rx, ry) else PIEDRA[1])
                elif not dentro(x, y - 12, cx, cy, rx, ry):
                    pon(x, y, AGUA[0])
                else:
                    pon(x, y, AGUA[1])
    contorno(im, PIEDRA[0])
    # ondas y brillos del agua
    for ox, oy, l in ((-60, 0, 7), (-48, 22, 8), (-30, 34, 6), (46, 4, 6), (36, 26, 8), (58, 16, 5),
                      (-14, -24, 6), (20, -26, 7)):
        for k in range(l):
            pon(cx + ox + k, cy + oy, AGUA[4] if k in (0, l - 1) else AGUA[5])
            if k % 3 == 1:
                pon(cx + ox + k, cy + oy + 1, AGUA[3])

    # --- parterre elevado de flores (con su murete) ---
    bx, by, brx, bry, bm = cx, 90, 46, 16, 6

    def en_parterre(x, y):
        return dentro(x, y, bx, by, brx, bry) or (y >= by and dentro(x, y - bm, bx, by, brx, bry))

    for y in range(H):
        for x in range(W):
            top = dentro(x, y, bx, by, brx, bry)
            if not top and y >= by and dentro(x, y - bm, bx, by, brx, bry):
                t = (x - (bx - brx)) / (2 * brx)
                pon(x, y, PIEDRA[3] if t < 0.35 else PIEDRA[2] if t < 0.75 else PIEDRA[1])
            elif top and not dentro(x, y, bx, by, brx - 3, bry - 2):
                pon(x, y, PIEDRA[4])
            elif top:
                n = (x * 7 + y * 13) % 9
                pon(x, y, FLOR[(x * 3 + y * 5) % 4] if n < 3 else HOJA[(x + 2 * y) % 3])
    for y in range(H):
        for x in range(W):
            if en_parterre(x, y) and any(not en_parterre(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                pon(x, y, PIEDRA[0])

    # --- sombra del pedestal (hacia abajo a la derecha) sobre el agua y las flores ---
    for y in range(40, 112):
        for x in range(cx - 14, cx + 40):
            r, g, b, a = px[x, y]
            if a and (x - 12 - cx) ** 2 / 28 ** 2 + (y - 92) ** 2 / 13 ** 2 <= 1:
                if (r, g, b) in (AGUA[1], AGUA[3], AGUA[4], AGUA[5]):
                    pon(x, y, AGUA[0])
                elif (r, g, b) == AGUA[0]:
                    pon(x, y, (40, 104, 184))
                elif (r, g, b) in FLOR or (r, g, b) in HOJA:
                    pon(x, y, HOJA[0])

    # --- pedestal: 4 cuerpos (de abajo arriba) ---
    def cuerpo(hw, top0, top1, frente1, cara_sup=True):
        x0, x1 = cx - hw, cx + hw
        y_ini = top0 if cara_sup else top1
        for y in range(y_ini, frente1 + 1):
            for x in range(x0, x1 + 1):
                if y < top1:
                    c = PIEDRA[5] if y < top0 + 2 else PIEDRA[4]          # cara de arriba
                else:
                    t = (x - x0) / (x1 - x0)                                # cara de delante
                    c = PIEDRA[4] if y == top1 else (PIEDRA[3] if t < 0.3 else PIEDRA[2] if t < 0.8 else PIEDRA[1])
                if x in (x0, x1) or y in (y_ini, frente1):
                    c = PIEDRA[0]
                pon(x, y, c)

    cuerpo(31, 86, 92, 100)           # escalón grande
    cuerpo(26, 80, 86, 89)            # escalón pequeño
    cuerpo(19, 60, 60, 81, False)     # dado (cuerpo central)
    for x in range(cx - 18, cx + 19):  # sombra bajo la cornisa
        pon(x, 61, PIEDRA[1]); pon(x, 62, PIEDRA[2])
    cuerpo(25, 46, 54, 60)            # cornisa (aquí se apoya Dialga)
    # placa de bronce
    for x in range(cx - 11, cx + 11):
        for y in range(66, 75):
            borde = x in (cx - 11, cx + 10) or y in (66, 74)
            pon(x, y, (88, 72, 40) if borde else (184, 152, 80) if y < 69 else (160, 128, 64))
    for x in range(cx - 8, cx + 8, 2):
        pon(x, 70, (96, 76, 40)); pon(x + 1, 72, (96, 76, 40))
    # peana de bronce bajo las patas de la estatua
    for y in range(46, 55):
        for x in range(cx - 23, cx + 24):
            if ((x - cx) / 22) ** 2 + ((y - 50) / 4) ** 2 <= 1:
                pon(x, y, (56, 64, 44) if y > 50 else (88, 96, 68))
    # surtidores dentro del pilón
    for ox, oy in ((-64, -4), (64, -4), (-40, -30), (40, -30), (-58, 24), (58, 24)):
        x, y = cx + ox, cy + oy
        for k in range(7):
            pon(x, y - k, AGUA[5] if k % 2 else AGUA[4])
        pon(x - 1, y - 7, AGUA[4]); pon(x + 1, y - 7, AGUA[4])
        for dx in (-3, -2, 2, 3):
            pon(x + dx, y + 1, AGUA[3])
    return im


def chorro_img():
    """Minifuente de suelo: pila redonda (bloque de abajo) y columna de agua (bloque de arriba)."""
    im = Image.new("RGBA", (16, 32), (0, 0, 0, 0)); px = im.load()
    for y in range(32):
        for x in range(16):
            if dentro(x, y, 8, 25, 7, 5):
                px[x, y] = (*(AGUA[1] if dentro(x, y, 8, 25, 5, 3) else PIEDRA[4]), 255)
    contorno(im, PIEDRA[0])
    for y in range(4, 26):                     # columna de agua
        w = 1 if y < 10 else 2
        for x in range(8 - w, 8 + w):
            px[x, y] = (*AGUA[5 if (y + x) % 3 else 3], 255)
    for x, y in ((6, 4), (9, 4), (5, 6), (10, 6), (4, 9), (11, 9), (7, 2), (8, 2), (5, 22), (11, 22)):
        px[x, y] = (*AGUA[4], 255)
    return im


def reloj_torre():
    """Torre del reloj (64x64 px) que corona el edificio de la izquierda: esfera grande marcando las diez."""
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    R = ROSA
    d.rectangle([8, 18, 55, 63], fill=R[5], outline=R[0])                       # cuerpo de la torre
    d.rectangle([5, 14, 58, 19], fill=R[3], outline=R[0])                       # cornisa
    d.rectangle([8, 56, 55, 63], fill=R[4], outline=R[0])
    for x in (12, 49):                                                           # pilastras
        d.rectangle([x - 2, 20, x + 2, 55], fill=R[4], outline=R[2])
    d.polygon([(6, 14), (32, 2), (57, 14)], fill=TEJA[3], outline=TEJA[0])     # frontón
    d.rectangle([29, 0, 34, 6], fill=(216, 176, 64), outline=HIERRO)           # campana
    d.ellipse([16, 22, 47, 53], fill=(248, 248, 240), outline=HIERRO)          # esfera
    d.ellipse([18, 24, 45, 51], outline=(150, 150, 150))
    for a in range(12):
        x = 31.5 + 11.5 * math.sin(a * math.pi / 6); y = 37.5 - 11.5 * math.cos(a * math.pi / 6)
        d.rectangle([round(x) - (a % 3 == 0), round(y) - (a % 3 == 0), round(x), round(y)], fill=HIERRO)
    d.line([(32, 38), (32, 27)], fill=HIERRO, width=1)                  # minutero: las 12
    d.line([(32, 38), (24, 33)], fill=HIERRO, width=2)                  # horario: las 10
    return im


def cupula():
    """Cúpula de pizarra con linterna y figura alada (como la del edificio de la Unión y el Fénix)."""
    im = Image.new("RGBA", (64, 48), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([12, 34, 51, 47], fill=CREMA[5], outline=CREMA[0])                 # tambor
    for x in range(16, 50, 7):
        d.rectangle([x, 37, x + 3, 45], fill=(96, 128, 168), outline=CREMA[1])     # ventanitas
    d.pieslice([10, 12, 53, 56], 180, 360, fill=PIZARRA[3], outline=PIZARRA[0])   # cúpula
    for x in (20, 31, 42):
        d.line([(x, 34), (31, 14)], fill=PIZARRA[1])
    d.rectangle([28, 8, 35, 14], fill=CREMA[4], outline=CREMA[0])                  # linterna
    # figura alada (silueta de bronce)
    d.polygon([(31, 0), (33, 0), (34, 7), (30, 7)], fill=(72, 80, 56))
    d.polygon([(30, 2), (22, 0), (26, 5)], fill=(72, 80, 56))
    d.polygon([(34, 2), (42, 0), (38, 5)], fill=(72, 80, 56))
    return im


def balcon(ancho_px):
    """Barandilla de hierro forjado (capa de abajo, sobre la fachada)."""
    im = Image.new("RGBA", (ancho_px, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([(1, 9), (ancho_px - 2, 9)], fill=HIERRO)
    d.line([(0, 15), (ancho_px - 1, 15)], fill=HIERRO)
    for x in range(1, ancho_px - 1, 3):
        d.line([(x, 10), (x, 14)], fill=HIERRO)
    return im


def toldo(ancho_px, c1, c2):
    """Toldo de rayas de un comercio (capa de arriba: el jugador pasa por debajo)."""
    im = Image.new("RGBA", (ancho_px, 16), (0, 0, 0, 0)); px = im.load()
    for y in range(12):
        for x in range(ancho_px):
            px[x, y] = (*(c1 if (x // 4) % 2 == 0 else c2), 255)
    for x in range(ancho_px):
        for y in range(12, 15):
            if (x % 8) in range(1, 7) and y - 12 < 3 - abs((x % 8) - 3.5) / 1.5:
                px[x, y] = (*(c1 if (x // 4) % 2 == 0 else c2), 255)
    for x in range(ancho_px):
        px[x, 0] = (60, 40, 40, 255)
    return im


def mosaico_img():
    N = 48
    im = Image.new("RGBA", (N, N)); px = im.load(); m = (N - 1) / 2
    for y in range(N):
        for x in range(N):
            dx, dy = abs(x - m), abs(y - m)
            cua, rom = max(dx, dy) <= 16, dx + dy <= 22
            if max(dx, dy) >= 22.5:
                c = SUELO[5]
            elif cua or rom:
                borde = (cua and max(dx, dy) > 15 and not rom) or (rom and dx + dy > 21 and not cua)
                c = SUELO[4] if borde else SUELO[0]
                if max(dx, dy) <= 5 and dx + dy <= 7:
                    c = SUELO[5] if (max(dx, dy) > 4 or dx + dy > 6) else SUELO[1]
            else:
                c = SUELO[2]
            px[x, y] = (*c, 255)
    return im


def luz_calida(r, g, b):
    """Las farolas modernas tienen luz rosa: la pasamos a luz cálida, como las fernandinas."""
    if r > 150 and b > 80 and g < 150:
        return (248, 216, 120) if r > 200 else (216, 160, 64)
    return (r, g, b)


def con_naranjas(semilla):
    """Recolor: en algunos píxeles verdes claros de la copa aparece una naranja."""
    contador = [semilla * 7]

    def f(r, g, b):
        contador[0] += 1
        if g > r + 30 and g > 110 and contador[0] % 23 == 0:
            return (248, 144, 32)
        return (r, g, b)
    return f


# ===================== construcción =====================
def farola(L, x, y):
    """Farola negra de 1x3: la cabeza va en la capa de arriba (tapa al jugador si pasa por detrás)
    y solo el pie bloquea el paso."""
    L.pegar(MODERNA, 14, 12, 1, 2, x, y - 2, quitar_colores_de=SUELO_FAROLA, colision=True,
            color=luz_calida, todo_arriba=True)
    L.pegar(MODERNA, 14, 14, 1, 1, x, y, quitar_colores_de=SUELO_FAROLA, colision=False, color=luz_calida)
    L.sombra("elipse", x * 16 + 4, y * 16 + 11, x * 16 + 15, y * 16 + 16)          # sombra del pie
    L.sombra_linea(x * 16 + 10, y * 16 + 13, x * 16 + 26, y * 16 + 20)             # sombra del poste


def suelo(L, x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1, 2):
            L.pegar(COSTA, 18, 35, 2, 1, x, y)


def edificio(L, x0, y0, pisos=2, color=CREMA, ancho=5, puerta=False, balcones=False, toldo_cols=None):
    """Edificio clásico: tejado de teja, cornisa, 'pisos' plantas de ventanas en arco y planta baja.
    Devuelve la fila de la planta baja."""
    fac, tej = rampa(color), rampa(TEJA)
    cols = [0, 1] + [2] * (ancho - 4) + [3, 4]             # columnas del modelo (se repite la del centro)
    y = y0
    filas = [(3, tej), (4, tej), (5, tej), (6, fac)] + [(7, fac)] * pisos + [(8, fac), (9, fac)]
    for sy, f in filas:
        for i, c in enumerate(cols):
            L.pegar(PUERTO, 28 + c, sy, 1, 1, x0 + i, y, color=f, colision=False, todo_abajo=True,
                    fondo=[0x1C, 0x1D, 0x15, 0x14] if sy == 3 else None)
        y += 1
    baja = y - 1
    if not puerta:                                          # tapiar la puerta del modelo: ventana en su lugar
        for i in range(ancho):
            if cols[i] == 2:
                L.pegar(PUERTO, 29, 9, 1, 1, x0 + i, baja, color=fac, colision=False, todo_abajo=True)
    else:
        pc = x0 + ancho // 2
        for i in range(ancho):
            if cols[i] == 2 and x0 + i != pc:
                L.pegar(PUERTO, 29, 9, 1, 1, x0 + i, baja, color=fac, colision=False, todo_abajo=True)
        L.pegar(PUERTO, 30, 9, 1, 1, pc, baja, color=fac, colision=True, todo_abajo=True)
        L.comportamiento(pc, baja, 0x69)                     # comportamiento "puerta"
    if balcones:
        for k in range(pisos):
            L.imagen(balcon(ancho * 16 - 8), x0 * 16 + 4, (y0 + 4 + k) * 16)
    if toldo_cols:
        L.imagen(toldo(ancho * 16 - 8, *toldo_cols), x0 * 16 + 4, (baja) * 16 - 2, capa="arriba")
    return baja


def tejas():
    """Textura de tejado de tejas árabes (16x16) para las filas de arriba, detrás de la torre y la cúpula."""
    im = Image.new("RGBA", (16, 16)); px = im.load()
    for y in range(16):
        for x in range(16):
            canal = (x % 4)
            c = TEJA[4] if canal == 1 else TEJA[3] if canal in (0, 2) else TEJA[2]
            if y % 8 in (6, 7) and canal != 3:
                c = TEJA[2] if y % 8 == 6 else TEJA[1]          # borde de cada hilada
            px[x, y] = (*c, 255)
    return im


def alcorque():
    """Rejilla de hierro cuadrada alrededor del tronco (como los alcorques de los naranjos)."""
    im = Image.new("RGBA", (32, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([2, 6, 29, 15], fill=(72, 72, 80), outline=HIERRO)
    for x in range(5, 28, 3):
        d.line([(x, 7), (x, 14)], fill=(48, 48, 56))
    return im


def naranjo_en_alcorque(L, x, y, semilla):
    """Árbol redondo (2x2) de la ciudad del desierto, con naranjas, sobre su alcorque."""
    L.sombra("elipse", x * 16 + 4, (y + 1) * 16 + 4, (x + 2) * 16 + 8, (y + 2) * 16 + 2)   # sombra de la copa
    L.imagen(alcorque(), x * 16, (y + 1) * 16)
    L.pegar(DESIERTO, 18, 25, 2, 2, x, y, fondo=HIERBA_DESIERTO, colision=None, color=con_naranjas(semilla))
    L.bloquear(x, y + 1, x + 1, y + 1)


def reloj_fachada():
    """El reloj de las Tendillas en la FACHADA (40x44 px): esfera blanca con marco de piedra y
    remate curvo, marcando las diez. Va sobre las plantas altas del edificio del oeste."""
    im = Image.new("RGBA", (40, 44), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    R = ROSA
    d.pieslice([4, 0, 35, 20], 180, 360, fill=R[4], outline=R[0])          # remate curvo
    d.rectangle([2, 8, 37, 43], fill=R[4], outline=R[0])                    # marco de piedra
    d.rectangle([4, 10, 35, 41], fill=R[3], outline=R[2])
    d.ellipse([6, 12, 33, 39], fill=(248, 248, 240), outline=HIERRO)        # esfera
    d.ellipse([8, 14, 31, 37], outline=(150, 150, 150))
    for a in range(12):
        x = 19.5 + 10 * math.sin(a * math.pi / 6); y = 25.5 - 10 * math.cos(a * math.pi / 6)
        g = 1 if a % 3 == 0 else 0
        d.rectangle([round(x) - g, round(y) - g, round(x), round(y)], fill=HIERRO)
    d.line([(20, 26), (20, 16)], fill=HIERRO, width=1)                      # minutero: las 12
    d.line([(20, 26), (13, 22)], fill=HIERRO, width=2)                      # horario: las 10
    d.rectangle([18, 1, 21, 5], fill=(216, 176, 64), outline=HIERRO)        # campanita
    return im


def sombra_edificio(L, x0, ancho, baja):
    """Sombra al pie de la fachada, sobre el suelo, un poco más larga hacia la derecha."""
    y = (baja + 1) * 16
    L.sombra("rect", x0 * 16 + 2, y, (x0 + ancho) * 16 + 4, y + 5)
    L.sombra("rect", (x0 + ancho) * 16, y - 10, (x0 + ancho) * 16 + 4, y + 5)


def construir():
    L = C.Lienzo(ANCHO, ALTO, dy=DY)
    suelo(L, 0, -DY, ANCHO - 1, ALTO - 1)
    t = tejas()
    for y in range(-DY, 3):
        for x in range(ANCHO):
            if x not in CALLE_NORTE:
                L.imagen(t, x * 16, y * 16)
    L.bloquear(0, -DY, ANCHO - 1, 0)            # tejados: no se pisan

    # ---------- pavimento: marco de franjas centrado en el eje y dos mosaicos ----------
    franja = Image.new("RGBA", (16, 16)); dfr = ImageDraw.Draw(franja)
    dfr.rectangle([0, 6, 15, 9], fill=SUELO[4]); dfr.line([(0, 6), (15, 6)], fill=SUELO[5]); dfr.line([(0, 9), (15, 9)], fill=SUELO[5])
    franja_v = franja.rotate(90)
    for x in range(MARCO_X[0], MARCO_X[1] + 1):
        for y in MARCO_Y:
            L.imagen(franja, x * 16, y * 16)
    for y in range(MARCO_Y[0], MARCO_Y[1] + 1):
        for x in MARCO_X:
            L.imagen(franja_v, x * 16, y * 16)
    for mx in (EJE - 9, EJE + 7):
        L.imagen(mosaico_img(), mx * 16, 23 * 16)
    L.fijar_suelo()                         # a partir de aquí, las sombras solo tocan estos colores

    # ---------- fila norte (planta baja en la fila 10) ----------
    sombra_edificio(L, 0, 7, edificio(L, 0, 1, pisos=3, color=CREMA, ancho=7, balcones=True))
    sombra_edificio(L, 7, 5, edificio(L, 7, 2, pisos=2, color=OCRE, toldo_cols=((176, 48, 40), (240, 232, 216))))
    sombra_edificio(L, 12, 5, edificio(L, 12, 1, pisos=3, color=BLANCO, puerta=True, balcones=True))     # laboratorio
    sombra_edificio(L, 20, 5, edificio(L, 20, 1, pisos=3, color=CREMA, balcones=True, toldo_cols=((40, 104, 64), (232, 232, 216))))
    sombra_edificio(L, 25, 5, edificio(L, 25, 2, pisos=2, color=OCRE, toldo_cols=((40, 72, 128), (232, 232, 216))))
    sombra_edificio(L, 30, 7, edificio(L, 30, 1, pisos=3, color=BLANCO, ancho=7, balcones=True))
    L.imagen(cupula(), 33 * 16 + 8 - 32, 1 * 16 + 8 - 48)
    for x in CALLE_NORTE:
        L.pegar(COSTA, BOLARDO[0], BOLARDO[1], 1, 1, x, 4, colision=False)

    # ---------- laterales: edificio del RELOJ al oeste y su pareja al este ----------
    baja = edificio(L, 0, 10, pisos=4, color=ROSA, ancho=7, puerta=True, balcones=True)
    sombra_edificio(L, 0, 7, baja)
    L.imagen(reloj_fachada(), 3 * 16 + 8 - 20, (10 + 3) * 16 - 6)
    baja = edificio(L, ANCHO - 7, 10, pisos=4, color=OCRE, ancho=7, balcones=True,
                    toldo_cols=((40, 104, 64), (232, 232, 216)))
    sombra_edificio(L, ANCHO - 7, 7, baja)
    # debajo, una hilera continua de naranjos cierra cada lateral (límite visible)
    for y in (20, 22, 24, 26, 28):
        naranjo_en_alcorque(L, 0, y, y)
        naranjo_en_alcorque(L, ANCHO - 2, y, y + 7)
    for x in (0, 1, ANCHO - 2, ANCHO - 1):      # bolardos al final de cada hilera
        L.pegar(COSTA, BOLARDO[0], BOLARDO[1], 1, 1, x, 30, colision=False)
    L.bloquear(0, 20, 1, 30)                    # el lateral queda cerrado del todo (sin huecos entre árboles)
    L.bloquear(ANCHO - 2, 20, ANCHO - 1, 30)

    # ---------- la fuente, en el centro ----------
    fx, fy = FUENTE
    L.sombra("elipse", fx * 16 + 88 + 10 - 87, fy * 16 + 78 + 12 - 60, fx * 16 + 88 + 10 + 87, fy * 16 + 78 + 12 + 60)
    L.imagen(fuente_img(), fx * 16, fy * 16)
    L.bloquear(fx, fy + 1, fx + 10, fy + 8)
    L.bloquear(fx + 1, fy, fx + 9, fy)
    for x, y in ((fx - 1, fy + 2), (fx + 11, fy + 2), (fx - 1, fy + 7), (fx + 11, fy + 7)):
        L.sombra("elipse", x * 16 + 4, y * 16 + 11, x * 16 + 18, y * 16 + 16)
        L.pegar(COSTA, 16, 33, 1, 1, x, y, colision=False)

    # ---------- minifuentes ----------
    ch = chorro_img()
    for x, y in CHORROS_IZQ + CHORROS_DER:
        L.sombra("elipse", x * 16 + 3, y * 16 + 10, x * 16 + 19, y * 16 + 17)
        L.imagen(ch.crop((0, 16, 16, 32)), x * 16, y * 16)
        L.imagen(ch.crop((0, 0, 16, 16)), x * 16, (y - 1) * 16, capa="arriba")
        L.bloquear(x, y, x, y)

    # ---------- farolas, bancos y quioscos ----------
    for x in MARCO_X:
        farola(L, x, 13)
        farola(L, x, 25)
    for x in (EJE - 6, EJE + 5):
        L.sombra("rect", x * 16 + 3, 24 * 16 + 12, (x + 2) * 16 + 4, 25 * 16 + 3)
        L.pegar(DESIERTO, 18, 28, 2, 1, x, 24, fondo=HIERBA_DESIERTO, colision=False)
    for qx in (EJE - 9, EJE + 7):             # flores (oeste) y prensa (este), simétricos
        L.sombra("rect", qx * 16 + 4, 13 * 16 + 10, (qx + 3) * 16 + 5, 14 * 16 + 4)
        L.pegar(MERCADO, 13, 10, 3, 3, qx, 11, fondo=[0x1], colision=False)

    # ---------- naranjos de la fila sur ----------
    for a in (8, 11, 14):
        naranjo_en_alcorque(L, a, 27, a)
        naranjo_en_alcorque(L, 2 * EJE - 1 - a, 27, a + 50)

    # ---------- fila sur (fachadas hacia la calle de la casa) ----------
    for x0, ancho, color, kw in ((0, 5, OCRE, {}), (5, 5, BLANCO, {"puerta": True, "balcones": True}),
                                  (10, 7, ROSA, {}), (20, 7, CREMA, {}), (27, 5, OCRE, {}), (32, 5, CREMA, {})):
        sombra_edificio(L, x0, ancho, edificio(L, x0, 31, pisos=1, color=color, ancho=ancho, **kw))
    for x in (5, 9):
        L.sombra("elipse", x * 16 + 4, 39 * 16 + 11, x * 16 + 18, 39 * 16 + 16)
        L.pegar(COSTA, 16, 33, 1, 1, x, 39, colision=False)
    for x in (3, 14, 22, 33):
        farola(L, x, 40)
    # al otro lado de la calle: los tejados de los edificios de enfrente (límite visible por el sur)
    for x in range(ANCHO):
        L.pegar(PUERTO, 28 + (1 if x % 5 else 0) + (2 if x % 5 == 4 else 0), 3, 1, 3, x, 42, color=rampa(TEJA),
                colision=False, todo_abajo=True, fondo=[0x1C, 0x1D, 0x15, 0x14])
    L.sombra("rect", 0, 42 * 16 - 4, ANCHO * 16, 42 * 16)
    for y in (38, 39, 40, 41):
        L.pegar(COSTA, BOLARDO[0], BOLARDO[1], 1, 1, 0, y, colision=False)
        L.pegar(COSTA, BOLARDO[0], BOLARDO[1], 1, 1, ANCHO - 1, y, colision=False)
    return L


if __name__ == "__main__":
    import os
    L = construir()
    salida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("TEMP", "."), "plaza2.png")
    L.vista(1).save(salida)
    print("Vista previa:", salida)
    if "--convertir" in sys.argv:
        print(L.convertir().informe())
