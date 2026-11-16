"""hoja_bloques.py - Dibuja todos los bloques (metatiles) de un par de tilesets, numerados.
Uso: python hoja_bloques.py 0xPRIMARIO 0xSECUNDARIO salida.png [--solo-secundario]
Sirve para elegir qué bloques usar al construir un mapa a mano."""
import struct, sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
import render_mapa as rm

def hoja(t1, t2, solo2=False, cols=16, escala=2):
    R = rm.ROM
    # construimos una "cabecera" falsa en memoria: reutilizamos la lógica de render_mapa
    tiles1, pals1, meta1 = rm.tileset(t1)
    tiles2, pals2, meta2 = rm.tileset(t2)
    pals = pals1[:7] + pals2[7:13] + pals1[13:]
    tiles = tiles1[:rm.PRIMARIOS * 32].ljust(rm.PRIMARIOS * 32, b"\0") + tiles2
    def tile(n, pal, hf, vf):
        im = Image.new("RGBA", (8, 8)); px = im.load()
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                o = n * 32 + sy * 4 + sx // 2
                v = tiles[o] if o < len(tiles) else 0
                v = (v >> 4) if sx & 1 else v & 15
                px[x, y] = (*pals[pal][v], 255) if v else (0, 0, 0, 0)
        return im
    def bloque(n):
        meta = meta1 + 16 * n if n < rm.PRIMARIOS else meta2 + 16 * (n - rm.PRIMARIOS)
        im = Image.new("RGBA", (16, 16), (255, 0, 255, 255))
        for capa in range(2):
            for k in range(4):
                e = rm.H(meta + 2 * (capa * 4 + k))
                im.alpha_composite(tile(e & 0x3FF, e >> 12, (e >> 10) & 1, (e >> 11) & 1), ((k % 2) * 8, (k // 2) * 8))
        return im
    rango = range(rm.PRIMARIOS, rm.PRIMARIOS + 384) if solo2 else range(0, rm.PRIMARIOS + 384)
    rango = list(rango)
    filas = (len(rango) + cols - 1) // cols
    C = 16 * escala + 2
    out = Image.new("RGB", (cols * C + 30, filas * C), (40, 40, 40)); d = ImageDraw.Draw(out)
    for k, n in enumerate(rango):
        x, y = k % cols, k // cols
        out.paste(bloque(n).resize((16 * escala, 16 * escala), Image.NEAREST), (30 + x * C, y * C))
        if x == 0: d.text((0, y * C + 10), f"{n:X}", fill="yellow")
    return out

if __name__ == "__main__":
    hoja(int(sys.argv[1], 16), int(sys.argv[2], 16), "--solo-secundario" in sys.argv).save(sys.argv[3])
