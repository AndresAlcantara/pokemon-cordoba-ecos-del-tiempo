"""vista_previa.py - Imagen de la plaza con la estatua de Dialga colocada como en el juego.
Uso: python vista_previa.py salida.png [escala]"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import plaza as M, arte
import textos as t
from insertar_pokemon import lz77_descomprimir, TABLA_FRONTAL, TABLA_PAL_NORMAL
from PIL import Image


def estatua():
    r = t.ROM.read_bytes(); P = lambda o: struct.unpack("<I", r[o:o + 4])[0] - 0x8000000
    tiles = lz77_descomprimir(r, P(TABLA_FRONTAL + 8 * 536)); pal = lz77_descomprimir(r, P(TABLA_PAL_NORMAL + 8 * 536))
    cols = arte.bronce([((c & 31) * 8, ((c >> 5) & 31) * 8, ((c >> 10) & 31) * 8) for c in struct.unpack("<16H", pal[:32])])
    sp = Image.new("RGBA", (64, 64)); px = sp.load()
    for ti in range(64):
        for y in range(8):
            for x in range(8):
                v = tiles[ti * 32 + y * 4 + x // 2]; v = (v >> 4) if x & 1 else v & 15
                if v:
                    px[(ti % 8) * 8 + x, (ti // 8) * 8 + y] = (*cols[v], 255)
    return sp


def vista(L=None):
    L = L or M.construir()
    img = L.vista(1)
    ex, ey = M.ESTATUA; ey += M.DY
    img.alpha_composite(estatua(), (ex * 16 + 8 - 32, ey * 16 + 16 - 64))   # sprite 64x64: centrado y apoyado en su casilla
    return img


if __name__ == "__main__":
    esc = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    im = vista(); im.resize((im.width * esc, im.height * esc), Image.NEAREST).save(sys.argv[1])
