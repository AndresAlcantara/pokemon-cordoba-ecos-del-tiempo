"""
escucha_gba.py
==============
Escucha de prueba de la música de la portada SIMULANDO la GBA: las notas limpias
de midi_a_gba.py tocadas con las muestras de guitarra_instrumento.py, mezcladas a
13 379 Hz y con muestras de 8 bits, como hace la consola.

Uso: python scripts/escucha_gba.py musica/medley_guitarra.mid --desde 4.03 --hasta 47.6
Salida: musica/escucha_gba.wav
"""
import argparse
import sys
import wave
from pathlib import Path

import numpy as np
import pretty_midi

sys.path.insert(0, str(Path(__file__).parent))
import guitarra_instrumento as gi  # noqa: E402
import midi_a_gba as mg  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("midi", type=Path)
ap.add_argument("--desde", type=float, required=True)
ap.add_argument("--hasta", type=float, required=True)
ap.add_argument("--tal-cual", action="store_true")
ap.add_argument("--salida", default="escucha_gba.wav")
a = ap.parse_args()

HZ = gi.HZ
muestras = [np.round(gi.nylon(k, s, 7 + i) * 118) / 118 for i, (k, s) in enumerate(gi.MUESTRAS)]   # 8 bits
m = pretty_midi.PrettyMIDI(str(a.midi))
crudas = [n for i in m.instruments for n in i.notes]
if a.tal_cual:
    notas = [(round((n.start - a.desde) * mg.TICKS_POR_SEG), max(1, min(96, round((n.end - n.start) * mg.TICKS_POR_SEG))),
              n.pitch, n.velocity) for n in crudas if a.desde <= n.start < a.hasta]
else:
    notas = mg.limpiar(crudas, a.desde, a.hasta, 0.10, 50, 3)
total = int((a.hasta - a.desde) * HZ) + HZ
mezcla = np.zeros(total)
suelta = (gi.ADSR[3] / 256) ** (60 / HZ)            # apagado por muestra tras soltar la nota
for ini, dur, tecla, fuerza in notas:
    idx = sum(1 for c in gi.CORTES if tecla >= c)
    raiz = gi.MUESTRAS[idx][0]; s = muestras[idx]
    paso = 2 ** ((tecla - raiz) / 12)
    pos = np.arange(0, len(s) - 1, paso)
    sonido = np.interp(pos, np.arange(len(s)), s) * (fuerza / 127)
    fin = int(dur / mg.TICKS_POR_SEG * HZ)
    if fin < len(sonido):
        sonido[fin:] *= suelta ** np.arange(len(sonido) - fin)
    o = int(ini / mg.TICKS_POR_SEG * HZ)
    mezcla[o:o + len(sonido)] += sonido[:max(0, total - o)]
mezcla /= np.max(np.abs(mezcla)) + 1e-9
salida = gi.t.RAIZ / "musica" / a.salida
with wave.open(str(salida), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(HZ)
    w.writeframes((mezcla * 28000).astype(np.int16).tobytes())
print(f"{len(notas)} notas -> {salida.relative_to(gi.t.RAIZ)}")
