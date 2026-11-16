"""Dibuja las capas de fondo de un estado de mGBA (modo 0, mapas de 32x32 tiles)."""
import sys, struct
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estado_mgba as e
from PIL import Image
def pal15(c): return ((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)
def capa(s, bg):
    io, vram, pal = s['io'], s['vram'], s['pal']
    cnt = struct.unpack('<H', io[8+2*bg:10+2*bg])[0]
    cb, bpp8, sb = ((cnt >> 2) & 3) * 0x4000, (cnt >> 7) & 1, ((cnt >> 8) & 31) * 0x800
    colores = [pal15(struct.unpack('<H', pal[2*i:2*i+2])[0]) for i in range(256)]
    im = Image.new('RGB', (256, 256))
    px = im.load()
    for ty in range(32):
        for tx in range(32):
            ent = struct.unpack('<H', vram[sb + 2*(ty*32+tx): sb + 2*(ty*32+tx) + 2])[0]
            tile, hf, vf, pb = ent & 0x3FF, (ent >> 10) & 1, (ent >> 11) & 1, ent >> 12
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                    if bpp8:
                        o = cb + tile*64 + sy*8 + sx; idx = vram[o] if o < len(vram) else 0; c = colores[idx]
                    else:
                        o = cb + tile*32 + sy*4 + sx//2; b = vram[o] if o < len(vram) else 0
                        idx = (b >> 4) if sx & 1 else (b & 15); c = colores[pb*16 + idx]
                    px[tx*8+x, ty*8+y] = c if idx else (255, 0, 255)
    return im.crop((0, 0, 240, 160)), dict(charbase=cb, screenbase=sb, bpp8=bpp8)
if __name__ == '__main__':
    s = e.leer(sys.argv[1])
    for bg in map(int, sys.argv[2].split(',')):
        im, info = capa(s, bg); im.save(f'pruebas/capa_{sys.argv[1].split(".")[-1]}_bg{bg}.png'); print(bg, info)
