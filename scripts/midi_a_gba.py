"""
midi_a_gba.py
=============
Convierte un fragmento de un MIDI en una canción del motor de sonido de la GBA
(formato "M4A"/Sappy) y la pone en lugar de una canción de la ROM.

CONCEPTOS (para clase)
----------------------
* La música de la GBA son PISTAS con órdenes de 1 byte:
    0x80-0xB0  WAIT  (esperar N ticks; N sale de una tabla de 49 duraciones)
    0xD0-0xFF  NOTE  (tocar una nota de N ticks; después van la tecla y la fuerza)
    0xBB TEMPO (bpm/2) · 0xBD VOICE (instrumento) · 0xBE VOL · 0xBF PAN
    0xB2 GOTO dirección (para el bucle) · 0xB1 FINE (fin)
* El tiempo va en ticks: 24 por negra. A 120 bpm, 1 tick = 1/48 de segundo.
* Una NOTA no hace avanzar el tiempo: el tiempo solo avanza con WAIT. Por eso
  cada pista es una sucesión de "nota, espera, nota, espera...".
* La CABECERA de la canción dice cuántas pistas hay, qué banco de instrumentos
  (voicegroup) usa y dónde empieza cada pista. La TABLA DE CANCIONES apunta a
  esa cabecera: cambiando ese puntero, el juego toca nuestra canción.

Uso:
  python scripts/midi_a_gba.py musica/medley_guitarra.mid --desde 4.03 --hasta 47.6 --voicegroup 15FA578 --voz 0 [--simular]
  (el programa 24 del banco de Unbound NO es una guitarra: sonaba a piano. El banco de
   guitarra_instrumento.py tiene una guitarra sintetizada en el instrumento 0.)
"""
import argparse
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

import pretty_midi

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

TABLA_CANCIONES = 0x7FE000
CANCION_PORTADA = 278
VOICEGROUP_PORTADA = 0x104A5EC
GUITARRA_NYLON = 24
BPM = 120
TICKS_POR_SEG = BPM / 60 * 24          # 48
MAX_PISTAS = 8                 # el reproductor de música de fondo admite hasta 10
DURACIONES = list(range(0, 25)) + [28, 30, 32, 36, 40, 42, 44, 48, 52, 54, 56, 60, 64, 66, 68, 72,
                                   76, 78, 80, 84, 88, 90, 92, 96]          # índices 0..48


def wait_bytes(n):
    """Descompone una espera de n ticks en órdenes WAIT de la tabla."""
    out = bytearray()
    while n > 0:
        if n >= 96:
            out.append(0x80 + DURACIONES.index(96)); n -= 96
        else:
            mejor = max(d for d in DURACIONES if d <= n)
            out.append(0x80 + DURACIONES.index(mejor)); n -= mejor
    return out


def nota_bytes(dur, tecla, fuerza):
    dur = max(1, min(96, dur))
    d = min(DURACIONES[1:], key=lambda x: (abs(x - dur), x))     # duración de la tabla más cercana
    return bytes([0xCF + DURACIONES.index(d), tecla & 0x7F, max(1, min(127, fuerza))])


def limpiar(crudas, desde, hasta, min_dur, min_fuerza, max_poli):
    """Limpia una transcripción automática para que se entienda en la GBA:
    1) quita notas muy cortas o muy flojas (suelen ser errores del transcriptor);
    2) une notas repetidas de la misma altura que se solapan;
    3) si suenan más de max_poli a la vez, conserva la más aguda (melodía), la más
       grave (bajo) y las más fuertes;
    4) la melodía (nota más aguda de cada momento) suena más fuerte que el resto.
    Devuelve [(inicio_ticks, duración_ticks, tecla, fuerza)]."""
    sel = [n for n in crudas if desde <= n.start < hasta
           and n.end - n.start >= min_dur and n.velocity >= min_fuerza]
    sel.sort(key=lambda n: (n.pitch, n.start))
    unidas = []
    for n in sel:
        if unidas and unidas[-1].pitch == n.pitch and n.start < unidas[-1].end + 0.03:
            unidas[-1].end = max(unidas[-1].end, n.end); unidas[-1].velocity = max(unidas[-1].velocity, n.velocity)
        else:
            unidas.append(pretty_midi.Note(n.velocity, n.pitch, n.start, n.end))
    unidas.sort(key=lambda n: n.start)
    quedan = []
    for n in unidas:
        sonando = [o for o in quedan if o.end > n.start + 0.02]
        if len(sonando) >= max_poli:
            grupo = sonando + [n]
            aguda = max(grupo, key=lambda o: o.pitch); grave = min(grupo, key=lambda o: o.pitch)
            resto = sorted([o for o in grupo if o not in (aguda, grave)], key=lambda o: -o.velocity)
            fuera = set(map(id, resto[max(0, max_poli - 2):]))
            for o in sonando:
                if id(o) in fuera: o.end = n.start                  # se corta la que sobra
            if id(n) in fuera: continue
        quedan.append(n)
    out = []
    for n in quedan:
        if n.end - n.start < 0.04: continue
        es_melodia = not any(o is not n and o.pitch > n.pitch and o.start < n.end and o.end > n.start for o in quedan)
        fuerza = int(70 + n.velocity * 0.45) + (14 if es_melodia else -12)
        out.append((round((n.start - desde) * TICKS_POR_SEG),
                    max(6, min(72, round((min(n.end, hasta) - n.start) * TICKS_POR_SEG))),
                    n.pitch, max(40, min(127, fuerza))))
    return out


def repartir(notas):
    """Reparte las notas en pistas sin solapes (cada pista toca una nota cada vez)."""
    pistas = []
    for n in sorted(notas, key=lambda n: (n[0], -n[2])):
        for p in pistas:
            if p[-1][0] + p[-1][1] <= n[0]:
                p.append(n); break
        else:
            if len(pistas) < MAX_PISTAS:
                pistas.append([n])
            # si ya hay MAX_PISTAS sonando a la vez, la nota se descarta (pasa muy pocas veces)
    return pistas


def compilar_pista(notas, total, primera, voz, vol):
    """Devuelve (bytes, posición del inicio del bucle, posición del puntero del GOTO)."""
    b = bytearray()
    if primera:
        b += bytes([0xBB, BPM // 2])
    b += bytes([0xBD, voz, 0xBE, vol, 0xBF, 64])
    bucle = len(b)
    tick = 0
    for ini, dur, tecla, fuerza in notas:
        b += wait_bytes(ini - tick); tick = ini
        b += nota_bytes(dur, tecla, fuerza)
    b += wait_bytes(total - tick)
    goto = len(b) + 1
    b += bytes([0xB2, 0, 0, 0, 0, 0xB1])
    return b, bucle, goto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("midi", type=Path)
    ap.add_argument("--desde", type=float, required=True)
    ap.add_argument("--hasta", type=float, required=True)
    ap.add_argument("--voz", type=int, default=GUITARRA_NYLON)
    ap.add_argument("--voicegroup", type=lambda x: int(x, 16), default=VOICEGROUP_PORTADA,
                    help="banco de instrumentos en hex (p. ej. el de guitarra_instrumento.py)")
    ap.add_argument("--vol", type=int, default=100)
    ap.add_argument("--min-dur", type=float, default=0.10, help="descarta notas más cortas (s): suelen ser falsas")
    ap.add_argument("--min-fuerza", type=int, default=50, help="descarta notas muy flojas (ecos, roces)")
    ap.add_argument("--max-poli", type=int, default=3, help="máximo de notas a la vez (melodía + acompañamiento)")
    ap.add_argument("--tal-cual", action="store_true",
                    help="usar las notas del MIDI sin limpiar (para MIDIs escritos a mano desde una partitura)")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()

    m = pretty_midi.PrettyMIDI(str(a.midi))
    crudas = [n for ins in m.instruments for n in ins.notes]
    if a.tal_cual:
        notas = [(round((n.start - a.desde) * TICKS_POR_SEG),
                  max(1, min(96, round((min(n.end, a.hasta) - n.start) * TICKS_POR_SEG))), n.pitch, n.velocity)
                 for n in crudas if a.desde <= n.start < a.hasta]
    else:
        notas = limpiar(crudas, a.desde, a.hasta, a.min_dur, a.min_fuerza, a.max_poli)
    total = round((a.hasta - a.desde) * TICKS_POR_SEG)
    pistas = repartir(notas)
    usadas = sum(len(p) for p in pistas)
    print(f"Fragmento {a.desde}-{a.hasta} s: {len(notas)} notas, {len(pistas)} pistas, "
          f"{len(notas) - usadas} descartadas, {total} ticks")

    rom = bytearray(t.ROM.read_bytes())
    entrada = TABLA_CANCIONES + 8 * CANCION_PORTADA
    vieja = struct.unpack("<I", rom[entrada:entrada + 4])[0] - 0x08000000
    cab_vieja = rom[vieja:vieja + 4]
    compiladas = [compilar_pista(p, total, i == 0, a.voz, a.vol) for i, p in enumerate(pistas)]
    tam = sum(len(c[0]) for c in compiladas) + 8 + 4 * len(pistas)
    print(f"Tamaño de la canción: {tam} bytes")
    if a.simular:
        return

    trabajo = bytearray(rom)
    punteros = []
    for b, bucle, goto in compiladas:
        o = t.buscar_libre(bytes(trabajo), len(b), alinear=4)
        b = bytearray(b)
        b[goto:goto + 4] = struct.pack("<I", 0x08000000 + o + bucle)       # GOTO al inicio del bucle
        trabajo[o:o + len(b)] = b
        punteros.append(o)
    cab = bytes([len(pistas), 0, cab_vieja[2], cab_vieja[3]]) + struct.pack("<I", 0x08000000 + a.voicegroup)
    cab += b"".join(struct.pack("<I", 0x08000000 + o) for o in punteros)
    oc = t.buscar_libre(bytes(trabajo), len(cab), alinear=4)
    trabajo[oc:oc + len(cab)] = cab
    trabajo[entrada:entrada + 4] = struct.pack("<I", 0x08000000 + oc)

    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-musica_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(trabajo)
    print(f"Canción nueva: cabecera 0x{oc:X} (antes 0x{vieja:X}); tabla de canciones, entrada {CANCION_PORTADA}")


if __name__ == "__main__":
    main()
