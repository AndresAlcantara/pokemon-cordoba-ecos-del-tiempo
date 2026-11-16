"""
musica_a_midi.py
================
Convierte una grabación (m4a, mp3, wav...) en MIDI con Basic Pitch (Spotify,
código abierto), usando su modelo ONNX.

CONCEPTOS (para clase)
----------------------
* Un audio es la ONDA grabada; un MIDI son NOTAS (qué tecla, cuándo, cuánto
  tiempo y con qué fuerza). La GBA no reproduce grabaciones largas: su música
  funciona como un MIDI tocado con sus propios instrumentos.
* Pasar de audio a MIDI es "transcribir": una red neuronal escucha la
  grabación y estima qué notas suenan en cada momento. Con una guitarra sola
  funciona razonablemente bien, pero nunca es perfecto: hay que revisar el
  resultado.

Uso:
  python scripts/musica_a_midi.py descargas/musica/medley_guitarra.m4a
Salida: musica/<nombre>.mid  (y <nombre>.wav intermedio en descargas/musica)
"""
import os
import sys
import wave
from pathlib import Path

import av
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent


def a_wav(entrada: Path, salida: Path, hz=22050):
    """Decodifica cualquier audio a WAV mono de 16 bits."""
    c = av.open(str(entrada))
    rs = av.AudioResampler(format="s16", layout="mono", rate=hz)
    trozos = []
    for frame in c.decode(audio=0):
        for f in rs.resample(frame):
            trozos.append(f.to_ndarray().reshape(-1))
    for f in rs.resample(None):
        trozos.append(f.to_ndarray().reshape(-1))
    datos = np.concatenate(trozos).astype(np.int16)
    with wave.open(str(salida), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(hz); w.writeframes(datos.tobytes())
    return len(datos) / hz


def main():
    entrada = Path(sys.argv[1])
    wav = entrada.with_suffix(".wav")
    dur = a_wav(entrada, wav)
    print(f"Audio decodificado: {dur:.1f} s -> {wav.name}")

    from basic_pitch.inference import predict
    import basic_pitch
    modelo = Path(os.path.dirname(basic_pitch.__file__)) / "saved_models" / "icassp_2022" / "nmp.onnx"
    _, midi, notas = predict(str(wav), str(modelo),
                             onset_threshold=0.55,      # más alto = menos notas falsas
                             frame_threshold=0.35,
                             minimum_note_length=90,    # ms: descarta notas muy cortas (ruido de púa)
                             minimum_frequency=70, maximum_frequency=1400,
                             multiple_pitch_bends=False, melodia_trick=True)
    salida = RAIZ / "musica" / (entrada.stem + ".mid")
    salida.parent.mkdir(exist_ok=True)
    midi.write(str(salida))
    print(f"MIDI: {salida.relative_to(RAIZ)} · {len(notas)} notas detectadas")


if __name__ == "__main__":
    main()
