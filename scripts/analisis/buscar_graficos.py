"""Busca en la ROM los bloques LZ77 cuyo contenido aparece en la VRAM o la paleta de un estado de mGBA."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estado_mgba as e
rom = open('MiHack.gba', 'rb').read()
def lz_parcial(off, n):
    size = int.from_bytes(rom[off+1:off+4], 'little'); out = bytearray(); p = off + 4
    try:
        while len(out) < min(n, size):
            fl = rom[p]; p += 1
            for bit in range(8):
                if len(out) >= min(n, size): break
                if fl & (0x80 >> bit):
                    l = (rom[p] >> 4) + 3; d = ((rom[p] & 0xF) << 8 | rom[p+1]) + 1; p += 2
                    if d > len(out): return None
                    for _ in range(l): out.append(out[-d])
                else: out.append(rom[p]); p += 1
    except IndexError: return None
    return bytes(out), size
def buscar(estado, regiones):
    s = e.leer(estado); res = []
    for o in range(0, len(rom) - 8, 4):
        if rom[o] != 0x10: continue
        size = int.from_bytes(rom[o+1:o+4], 'little')
        if not (0x20 <= size <= 0x10000): continue
        r = lz_parcial(o, 64)
        if not r: continue
        cab = r[0]
        if len(set(cab)) < 4: continue          # demasiado uniforme (vacío), daría falsos positivos
        for nombre, (mem, ini, fin) in regiones.items():
            pos = s[mem].find(cab, ini, fin)
            if pos != -1: res.append((hex(o), size, nombre, hex(pos)))
    return res
if __name__ == '__main__':
    est = sys.argv[1]
    s = e.leer(est)
    regiones = {'vram': ('vram', 0, 0x18000), 'pal': ('pal', 0, 0x400)}
    for r in buscar(est, regiones): print(r)
