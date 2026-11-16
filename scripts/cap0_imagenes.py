"""
cap0_imagenes.py
================
Añade imágenes a la intro: el Profesor Acisclo después de la página 1 y Mudbray
después de la página 2, cada uno con un cuadro de diálogo normal.

POR QUÉ ASÍ: la intro de Unbound muestra cada página con una rutina propia
(callasm 0x09EAA7C5) que ocupa toda la pantalla y tapa cualquier imagen.
Probado en mGBA el 14/11/2026: con showpokepic DURANTE la página no se ve nada.
Por eso la imagen aparece al cerrarse la página, como en la intro de FireRed.

CONCEPTOS (para clase)
----------------------
* Un SCRIPT es una lista de órdenes en bytes. Cada orden empieza por un código:
    0x0F 00 ptr  loadpointer (carga un texto)    0x09 04  callstd 4 (cuadro de texto normal)
    0x23 ptr     callasm (llama a código)        0x27     waitstate (espera)
    0x75 esp x y showpokepic (esp = 2 bytes)     0x76     hidepokepic
    0x05 ptr     goto
* No se pueden meter bytes en medio de un script sin desplazar lo que va detrás.
  El truco es un DESVÍO: el principio de la página 1 pasa a ser "goto zona_libre";
  allí va la versión nueva y al final un "goto" de vuelta a la página 3.
* showpokepic solo muestra Pokémon, así que el retrato del Profesor se guardó
  como sprite de la especie 254, que no usa nadie.

Uso: herramientas\\python-venv\\Scripts\\python.exe scripts\\cap0_imagenes.py [--x 10 --y 3]
"""
import argparse
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

PAGINA1 = 0x1E68673          # inicio de la página 1 en el script de la intro
LARGO_PAGINA = 22            # loadpointer(6) + setvar(5) + setvar(5) + callasm(5) + waitstate(1)
VUELTA = PAGINA1 + 2 * LARGO_PAGINA   # donde empieza la página 3
ESPECIE_ACISCLO = 254
ESPECIE_MUDBRAY = 966
TEXTO_ACISCLO = "¡Encantado de conocerte!"
TEXTO_MUDBRAY = "Este es Mudbray. En Córdoba, tierra{n}de caballos, todos lo adoran."


def ptr(off):
    return struct.pack("<I", 0x08000000 + off)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=int, default=10, help="columna (en tiles de 8 px) de la caja de la imagen")
    ap.add_argument("--y", type=int, default=3, help="fila (en tiles de 8 px)")
    a = ap.parse_args()

    rom = bytearray(t.ROM.read_bytes())
    original = (t.RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba").read_bytes()
    # Las páginas 1 y 2 del original. Sus textos se reescribieron EN SU SITIO
    # (cap0_intro.py), así que sus punteros siguen valiendo.
    paginas = original[PAGINA1:VUELTA]
    assert paginas[0] == 0x0F and paginas[LARGO_PAGINA] == 0x0F and paginas[21] == 0x27 and paginas[43] == 0x27

    # Textos de los cuadros normales, en espacio libre
    trabajo = bytearray(rom)
    offs = []
    for txt in (TEXTO_ACISCLO, TEXTO_MUDBRAY):
        datos = t.codificar(txt)
        o = t.buscar_libre(bytes(trabajo), len(datos))
        trabajo[o:o + len(datos)] = datos
        offs.append(o)

    def escena(especie, texto_off):
        return (bytes([0x75]) + struct.pack("<H", especie) + bytes([a.x, a.y])   # showpokepic
                + b"\x0F\x00" + ptr(texto_off) + b"\x09\x04"                    # msgbox normal
                + bytes([0x76]))                                                 # hidepokepic

    nuevo = (paginas[:LARGO_PAGINA] + escena(ESPECIE_ACISCLO, offs[0])
             + paginas[LARGO_PAGINA:] + escena(ESPECIE_MUDBRAY, offs[1])
             + bytes([0x05]) + ptr(VUELTA))
    destino = t.buscar_libre(bytes(trabajo), len(nuevo), alinear=4)
    trabajo[destino:destino + len(nuevo)] = nuevo

    desvio = bytes([0x05]) + ptr(destino)
    trabajo[PAGINA1:VUELTA] = desvio + b"\x00" * (2 * LARGO_PAGINA - len(desvio))   # nop: ya no se ejecuta

    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-imagenes_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp)
    print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(trabajo)
    print(f"Textos en 0x{offs[0]:X} y 0x{offs[1]:X}; bloque de {len(nuevo)} bytes en 0x{destino:X}; "
          f"desvío en 0x{PAGINA1:X}.")


if __name__ == "__main__":
    main()
