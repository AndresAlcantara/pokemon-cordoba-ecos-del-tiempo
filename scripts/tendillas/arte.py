"""
tendillas/arte.py
=================
Piezas NUEVAS de la plaza, dibujadas píxel a píxel con los colores del tileset:

  * la FUENTE redonda donde se levanta la estatua (7x5 bloques), con su pedestal;
  * los SURTIDORES del suelo (como los chorros que salen del pavimento de verdad);
  * el RELOJ de la fachada, marcando las diez;
  * la paleta de BRONCE de la estatua de Dialga (la estatua es un sprite del mapa).

CONCEPTOS (para clase)
----------------------
* Cada dibujo se hace sobre una imagen con ÍNDICES de paleta (0 = transparente),
  y después se corta en tiles de 8x8. Los tiles repetidos se reutilizan.
* Un bloque tiene dos capas: debajo ponemos el suelo de la plaza y encima el
  dibujo con transparencia; así la fuente "se apoya" sobre el pavimento.
"""
import math

# Paleta 12 del tileset (piedra gris y agua azul):
#  3 f0f0f0  4 c8d0c8  5 687888  6 586070  7 304048  8 f0f0f8  9 c0d0c8
# 10 c8e0f8 11 d0e8e8 12 40c0f8 13 38b8f8 14 40a0f8
PAL_FUENTE = 12
CONTORNO, LUZ, PIEDRA, PIEDRA2, SOMBRA, SOMBRA2 = 7, 3, 4, 9, 5, 6
AGUA, AGUA2, AGUA3, ESPUMA, ESPUMA2 = 14, 13, 12, 10, 11

ANCHO_F, ALTO_F = 7, 5          # bloques


def lienzo(w, h):
    return [[0] * w for _ in range(h)]


def dentro(x, y, cx, cy, rx, ry):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def fuente():
    """Devuelve una matriz 112x80 de índices de la paleta 12."""
    W, H = ANCHO_F * 16, ALTO_F * 16
    c = lienzo(W, H)
    cx, cy = W / 2, 37
    RX, RY = 54, 32            # borde exterior del pretil
    rx, ry = 47, 26            # agua
    MURO = 6                   # altura del muro delantero del pilón
    for y in range(H):
        for x in range(W):
            ext = dentro(x, y, cx, cy, RX, RY)
            muro = dentro(x, y - MURO, cx, cy, RX, RY) and y >= cy
            agua = dentro(x, y, cx, cy, rx, ry)
            if agua:
                c[y][x] = AGUA
            elif ext:
                # parte de arriba del pretil: luz arriba, más oscuro abajo (simétrico: ahorra tiles)
                c[y][x] = LUZ if y < cy - RY * 0.55 else (PIEDRA if y < cy + RY * 0.35 else PIEDRA2)
            elif muro:
                c[y][x] = SOMBRA if y < cy + RY + MURO - 2 else SOMBRA2
    # contornos: cualquier píxel pintado que toque un transparente
    copia = [fila[:] for fila in c]
    for y in range(H):
        for x in range(W):
            if copia[y][x] and any(not (0 <= x + dx < W and 0 <= y + dy < H) or copia[y + dy][x + dx] == 0
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c[y][x] = CONTORNO
    # borde interior del pretil (línea oscura donde empieza el agua) y sombra del agua arriba
    for y in range(H):
        for x in range(W):
            if copia[y][x] == AGUA:
                if not dentro(x, y - 1, cx, cy, rx, ry) or not dentro(x - 1, y, cx, cy, rx, ry) \
                        or not dentro(x + 1, y, cx, cy, rx, ry):
                    c[y][x] = SOMBRA
                elif not dentro(x, y - 3, cx, cy, rx, ry):
                    c[y][x] = AGUA2
    # brillos y ondas del agua
    ondas = ((-34, -8, 6), (-24, 10, 5), (-14, 18, 5))
    ondas += tuple((-ox - l, oy, l) for ox, oy, l in ondas)        # la misma onda reflejada
    for (ox, oy, l) in ondas:
        for k in range(l):
            x, y = int(cx + ox + k), int(cy + oy)
            if 0 <= y < H and 0 <= x < W and copia[y][x] == AGUA:
                c[y][x] = ESPUMA if k in (0, l - 1) else ESPUMA2
    # pedestal (el sprite de la estatua se apoya en su cara de arriba)
    px0, px1 = int(cx) - 20, int(cx) + 20          # 40 px de ancho
    top0, top1, frente1 = 44, 54, 70
    for y in range(top0 - 1, frente1 + 1):
        for x in range(px0 - 1, px1 + 1):
            borde = x in (px0 - 1, px1) or y in (top0 - 1, frente1)
            # esquinas achaflanadas (planta octogonal)
            if (x - px0 < 2 or px1 - 1 - x < 2) and (y < top0 + 1 or y > frente1 - 2):
                if x - px0 < 1 or px1 - 1 - x < 1:
                    continue
            if borde:
                c[y][x] = CONTORNO
            elif y < top1:
                c[y][x] = LUZ if y < top0 + 2 else PIEDRA
            elif y == top1:
                c[y][x] = CONTORNO
            else:
                c[y][x] = PIEDRA2 if y < frente1 - 3 else SOMBRA
    # placa del pedestal
    for x in range(int(cx) - 9, int(cx) + 9):
        c[59][x] = SOMBRA
        c[63][x] = SOMBRA
    for y in range(59, 64):
        c[y][int(cx) - 9] = SOMBRA; c[y][int(cx) + 8] = SOMBRA
    for x in range(int(cx) - 6, int(cx) + 6, 2):        # letras de la placa (sugeridas)
        c[61][x] = SOMBRA2
    # chorritos de agua alrededor del pedestal
    for (ox, oy) in ((-26, 0), (26, 0), (-14, -14), (14, -14)):
        x, y = int(cx + ox), int(cy + oy)
        for k, col in enumerate((ESPUMA, ESPUMA2, ESPUMA, ESPUMA2)):
            if 0 <= y - k < H:
                c[y - k][x] = col
        c[y + 1][x - 1] = ESPUMA2; c[y + 1][x + 1] = ESPUMA2
    return c


def surtidor():
    """Rejilla metálica en el suelo con un chorrito de agua (un bloque, capa de arriba)."""
    c = lienzo(16, 16)
    for y in range(5, 12):
        for x in range(4, 12):
            borde = y in (5, 11) or x in (4, 11)
            c[y][x] = CONTORNO if borde else (SOMBRA if (x + y) % 2 else SOMBRA2)
    for y, x, col in ((3, 7, ESPUMA2), (3, 8, ESPUMA2), (4, 7, ESPUMA), (4, 8, ESPUMA), (2, 7, ESPUMA),
                      (1, 8, ESPUMA2), (6, 7, ESPUMA), (6, 8, ESPUMA2), (7, 7, ESPUMA2), (2, 6, ESPUMA2), (2, 9, ESPUMA2)):
        c[y][x] = col
    return c


# Paleta 8 (fachadas): 0 202020  10 e0e0f0  11 c0c0d0  12 b0b0b0  13 909090  15 383028
PAL_RELOJ = 8
NEGRO, BLANCO, GRIS1, GRIS2, GRIS3, MARCO = 0, 10, 11, 12, 13, 15


def reloj():
    """Esfera de 16x16 marcando las diez en punto (capa de arriba de un bloque)."""
    c = lienzo(16, 16)
    cx = cy = 7.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            if d <= 7.6:
                c[y][x] = MARCO if d > 6.4 else (GRIS3 if d > 5.6 else BLANCO)
    # marcas de las horas 12, 3, 6, 9
    for x, y in ((7, 2), (8, 2), (13, 7), (13, 8), (7, 13), (8, 13), (2, 7), (2, 8)):
        c[y][x] = GRIS3
    # el índice 0 es transparente, así que las agujas van en el color más oscuro (MARCO)
    for y in range(3, 8):
        c[y][8] = MARCO           # minutero: hacia las 12
    for (x, y) in ((7, 7), (6, 6), (5, 6), (4, 5)):
        c[y][x] = MARCO           # horario: hacia las 10
    c[8][8] = GRIS3
    return c


def bronce(paleta_rgb):
    """Convierte la paleta de Dialga en bronce envejecido según el brillo de cada color."""
    rampa = [(24, 28, 24), (40, 48, 38), (58, 68, 52), (80, 92, 68), (104, 116, 86), (136, 146, 108), (176, 182, 140)]
    salida = [paleta_rgb[0]]
    for r, g, b in paleta_rgb[1:]:
        lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        salida.append(rampa[min(len(rampa) - 1, int(lum * len(rampa) * 1.05))])
    return salida


# Paleta 9 (pavimento de la plaza): 2 c0d0f0 (claro) 3 b8c8e0 4 a8c0d8 5 a0b0d0 (junta) 6 98a8c0 7 98a0a8
PAL_SUELO = 9
CLARO, MEDIO, BASE_S, JUNTA, OSCURO, OSCURO2 = 2, 3, 4, 5, 6, 7


def mosaico():
    """Mosaico de 3x3 bloques con una estrella de ocho puntas, como los del pavimento real.
    Es simétrico en horizontal y vertical, así que casi todos sus tiles se reutilizan volteados."""
    N = 48
    c = lienzo(N, N)
    m = (N - 1) / 2
    for y in range(N):
        for x in range(N):
            dx, dy = abs(x - m), abs(y - m)
            cuadrado = max(dx, dy) <= 16
            rombo = dx + dy <= 22
            if max(dx, dy) >= 22.5:
                col = OSCURO2                                   # marco del panel
            elif cuadrado or rombo:
                borde = (cuadrado and max(dx, dy) > 15) or (rombo and dx + dy > 21) 
                col = OSCURO if borde and not (cuadrado and rombo and max(dx, dy) <= 15 and dx + dy <= 21) else CLARO
                if max(dx, dy) <= 5 and dx + dy <= 7:
                    col = OSCURO2 if (max(dx, dy) > 4 or dx + dy > 6) else MEDIO     # octógono central
            else:
                col = BASE_S
            c[y][x] = col
    return c


def franja(horizontal=True, cruce=False):
    """Bloque de pavimento cruzado por una línea de losas más oscuras."""
    c = lienzo(16, 16)
    for y in range(16):
        for x in range(16):
            en_h = 6 <= y <= 9
            en_v = 6 <= x <= 9
            linea = (en_h and (horizontal or cruce)) or (en_v and (not horizontal or cruce))
            if linea:
                col = OSCURO2 if (y in (6, 9) and (horizontal or cruce) and en_h) or (x in (6, 9) and en_v and (not horizontal or cruce)) else OSCURO
            else:
                col = JUNTA if (x % 8 == 7 or y % 8 == 7) else (CLARO if (x // 8 + y // 8) % 2 else BASE_S)
            c[y][x] = col
    return c
