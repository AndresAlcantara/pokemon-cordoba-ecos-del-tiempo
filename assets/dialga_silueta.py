"""
Silueta de Dialga a partir de la imagen del usuario (descargas/dialga/pose_usuario.png).

Método (para clase): en vez de adivinar los colores de Dialga, se RELLENA EL FONDO
desde los bordes de la imagen. El cielo es gris neutro y oscuro (rojo = verde = azul,
poco brillo); el contorno del sprite de Dialga es azul marino oscuro (más azul que
rojo), así que el relleno se detiene justo en el borde de Dialga. Todo lo que el
relleno no alcanza es Dialga, incluidas sus partes plateadas.
"""
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
im = np.array(Image.open(RAIZ / "descargas/dialga/pose_usuario.png").convert("RGB")).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
H, W = r.shape
ROCAS = 134                     # fila donde empiezan las rocas (Dialga está detrás de ellas)

fondo_posible = (abs(b - r) <= 14) & (abs(g - r) <= 10) & (np.maximum(np.maximum(r, g), b) < 140)   # cielo y nubes grises
fondo_posible[ROCAS:, :] = True          # las rocas cuentan como fondo
fondo = np.zeros((H, W), bool)
q = deque()
for y in range(H):
    for x in range(W):
        if (y in (0, H - 1) or x in (0, W - 1)) and fondo_posible[y, x]:
            fondo[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and not fondo[ny, nx] and fondo_posible[ny, nx]:
            fondo[ny, nx] = True; q.append((ny, nx))

m = ~fondo
m[ROCAS:, :] = False
# quedarse solo con la pieza principal (Dialga) y las piezas grandes pegadas a ella
comps = []
vis = np.zeros_like(m)
for y in range(H):
    for x in range(W):
        if m[y, x] and not vis[y, x]:
            comp, q = [(y, x)], deque([(y, x)]); vis[y, x] = True
            while q:
                cy, cx = q.popleft()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not vis[ny, nx]:
                            vis[ny, nx] = True; q.append((ny, nx)); comp.append((ny, nx))
            comps.append(comp)
comps.sort(key=len, reverse=True)
m[:] = False
for cy, cx in comps[0]: m[cy, cx] = True
Image.fromarray((m * 255).astype(np.uint8)).save(RAIZ / "descargas/dialga/pose_mascara.png")
print("silueta:", int(m.sum()), "píxeles")
