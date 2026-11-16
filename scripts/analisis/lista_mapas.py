"""lista_mapas.py - Recorre la tabla de bancos de mapas y lista cada mapa (solo lectura).
gMapGroups (0x3526A8): lista de punteros a bancos; cada banco es una lista de punteros a cabeceras.
Cabecera: layout, eventos, scripts, conexiones, música(2), id layout(2), sección(1), cueva(1),
clima(1), tipo(1)...   Tipo de mapa: 1 pueblo, 2 ciudad, 3 ruta, 4 subterráneo, 5 bajo agua, 8 interior."""
import struct, sys
from pathlib import Path
ROM = (Path(__file__).resolve().parents[2] / "MiHack.gba").read_bytes()
P = lambda o: struct.unpack("<I", ROM[o:o + 4])[0]
ok = lambda v: 0x08000000 <= v < 0x0A000000
TABLA = 0x3526A8   # gMapGroups (0xB6FB20 es la tabla de layouts)

def mapas():
    bancos = []
    o = TABLA
    while ok(P(o)) and len(bancos) < 64:
        bancos.append(P(o) - 0x08000000); o += 4
    for b, bo in enumerate(bancos):
        sig = bancos[b + 1] if b + 1 < len(bancos) else None
        m = 0; o = bo
        while (sig is None or o < sig) and m < 256:
            v = P(o)
            if ok(v) and ok(P(v - 0x08000000)):
                yield b, m, v - 0x08000000
            elif v != 0xF7F7F7F7:          # Unbound marca algunos huecos con F7F7F7F7
                break
            m += 1; o += 4

if __name__ == "__main__":
    for b, m, cab in mapas():
        lay = P(cab) - 0x08000000
        w, h = struct.unpack("<II", ROM[lay:lay + 8])
        ts1, ts2 = P(lay + 16), P(lay + 20)
        tipo = ROM[cab + 0x17]; musica = struct.unpack("<H", ROM[cab + 0x10:cab + 0x12])[0]
        print(f"{b}.{m}\tcab 0x{cab:X}\t{w}x{h}\ttipo {tipo}\tts {ts1:X}/{ts2:X}\tmús {musica}")
