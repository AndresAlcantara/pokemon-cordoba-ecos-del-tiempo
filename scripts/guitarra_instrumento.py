"""
guitarra_instrumento.py
=======================
Crea un instrumento de GUITARRA para el motor de sonido de la GBA y lo guarda en
la ROM como un banco de instrumentos (voicegroup) nuevo, de un solo instrumento.

CONCEPTOS (para clase)
----------------------
* (Primera versión: Karplus-Strong, sonaba metálica. Ahora: síntesis aditiva.)
* Karplus-Strong: se llena un "trozo de cuerda" (un búfer tan largo como un
  periodo de la nota) con ruido, y en cada vuelta se promedia cada muestra con la
  siguiente y se atenúa un poco. El ruido se convierte en una nota que se apaga
  poco a poco, como una cuerda pulsada. Un filtro suave imita la caja de la guitarra.
* El motor de la GBA toca MUESTRAS (sonidos grabados de 8 bits) y las acelera o
  frena para cada nota. Si una sola muestra cubre muchas notas, suena artificial;
  por eso hay tres (grave, media, aguda) y una tabla "keysplit" que elige cuál usar
  según la tecla.
* Formato de una muestra (WaveData): tipo(2) estado(2) frecuencia(4) inicio_bucle(4)
  tamaño(4) + datos de 8 bits con signo. "frecuencia" = Hz de muestreo x 1024 para
  que la nota Do central (tecla 60) suene a su altura.
* Instrumento (12 bytes): tipo 0x40 = keysplit, puntero a los sub-instrumentos y
  puntero a la tabla de 128 bytes (una entrada por tecla).

Uso: python scripts/guitarra_instrumento.py   -> imprime la dirección del banco nuevo
Guarda también musica/guitarra_muestras.wav para escucharlas.
"""
import struct
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

HZ = 13379                                       # velocidad de mezcla de la GBA: sin agudos imposibles
MUESTRAS = [(43, 1.3), (50, 1.2), (57, 1.1), (64, 1.0), (71, 0.9)]   # Sol2, Re3, La3, Mi4, Si4
CORTES = [47, 54, 61, 68]                        # qué muestra toca cada tecla (la más cercana)
ADSR = (255, 0, 255, 170)                        # ataque instantáneo; al soltar, se apaga rápido y limpio


def karplus_strong(tecla, segundos, semilla):
    f = 440 * 2 ** ((tecla - 69) / 12)
    n = int(HZ * segundos)
    N = int(round(HZ / f))
    rng = np.random.default_rng(semilla)
    cuerda = rng.uniform(-1, 1, N)
    cuerda = np.convolve(cuerda, [0.25, 0.5, 0.25], mode="same")       # púa suave (nylon)
    out = np.zeros(n)
    atenuacion = 0.996 if tecla < 60 else 0.993
    buf = cuerda.copy()
    for i in range(n):
        j = i % N
        out[i] = buf[j]
        buf[j] = atenuacion * 0.5 * (buf[j] + buf[(j + 1) % N])
    # "caja": refuerzo de graves (~110 Hz) y un poco de brillo, con un filtro sencillo
    caja = np.convolve(out, np.exp(-np.arange(200) / 40) * np.sin(2 * np.pi * 110 * np.arange(200) / HZ) * 0.02, mode="same")
    out = out + caja
    out *= np.minimum(1, np.linspace(30, 0, n))          # apagado final suave (últimos ~3 %)
    out /= np.max(np.abs(out)) + 1e-9
    return out


def nylon(tecla, segundos, semilla):
    """Guitarra ESPAÑOLA (clásica, cuerdas de nylon) por síntesis aditiva:
    - armónicos que se apagan antes cuanto más agudos son (sonido cálido, no metálico);
    - pulsación cerca de la boca, con ataque de uña (el "toque" español);
    - resonancias de la caja de madera: aire (~100 Hz) y tapa (~200 y ~450 Hz)."""
    from scipy.signal import iirpeak, lfilter
    f = 440 * 2 ** ((tecla - 69) / 12)
    n = int(HZ * segundos); tt = np.arange(n) / HZ
    tau = 1.3 if tecla < 55 else (1.0 if tecla < 65 else 0.75)
    out = np.zeros(n)
    for k in range(1, 16):
        fk = k * f * np.sqrt(1 + 0.00006 * k * k)
        if fk > 0.42 * HZ:
            break
        amp = abs(np.sin(np.pi * k * 0.22)) / k ** 1.15
        out += amp * np.exp(-tt * (1 + 0.45 * (k - 1)) / tau) * np.sin(2 * np.pi * fk * tt + 0.3 * k)
    rng = np.random.default_rng(semilla)
    m = int(0.008 * HZ)
    una = rng.uniform(-1, 1, m) * np.linspace(1, 0, m) ** 2 * 0.35       # chasquido de la uña
    out[:m] += una
    caja = np.zeros(n)
    for fc, q, g in ((100, 4, 0.9), (205, 5, 0.7), (450, 6, 0.35)):
        b, a = iirpeak(fc, q, fs=HZ)
        caja += g * lfilter(b, a, out)
    out = out + caja
    out *= np.minimum(1, tt / 0.002)
    out *= np.minimum(1, np.linspace(20, 0, n))
    return out / (np.max(np.abs(out)) + 1e-9)


def wavedata(senal, tecla):
    datos = np.clip(np.round(senal * 118), -127, 127).astype(np.int8)
    freq = int(round(HZ * 1024 * 2 ** ((60 - tecla) / 12)))           # tecla 60 -> HZ (ver docstring)
    cab = struct.pack("<HHIII", 0, 0, freq, 0, len(datos))
    return cab + datos.tobytes() + b"\x00"                            # byte extra para la interpolación


def main():
    senales = [nylon(k, s, 7 + i) for i, (k, s) in enumerate(MUESTRAS)]
    # escucha de prueba: las tres muestras seguidas
    junta = np.concatenate([np.concatenate([s, np.zeros(HZ // 4)]) for s in senales])
    with wave.open(str(t.RAIZ / "musica" / "guitarra_muestras.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(HZ)
        w.writeframes((junta * 30000).astype(np.int16).tobytes())

    rom = bytearray(t.ROM.read_bytes())
    trabajo = bytearray(rom)

    def colocar(b):
        o = t.buscar_libre(bytes(trabajo), len(b), alinear=4)
        trabajo[o:o + len(b)] = b
        return o

    ptr = lambda o: struct.pack("<I", 0x08000000 + o)
    ondas = [colocar(wavedata(s, k)) for s, (k, _) in zip(senales, MUESTRAS)]
    subs = b"".join(bytes([0x00, 60, 0, 0]) + ptr(o) + bytes(ADSR) for o in ondas)   # sub-instrumentos DirectSound
    o_subs = colocar(subs)
    tabla = bytes(sum(1 for c in CORTES if k >= c) for k in range(128))
    o_tabla = colocar(tabla)
    instrumento = bytes([0x40, 0, 0, 0]) + ptr(o_subs) + ptr(o_tabla)
    o_vg = colocar(instrumento)
    t.ROM.write_bytes(trabajo)
    print(f"Muestras en {[hex(o) for o in ondas]}")
    print(f"Banco de instrumentos de guitarra (voicegroup): 0x{o_vg:X}  (instrumento 0)")


if __name__ == "__main__":
    main()
