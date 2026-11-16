"""
cap0_profesor_mapa.py
=====================
Muestra al Profesor Acisclo en la intro como Unbound muestra al jugador en la
creación de personaje: un sprite GRANDE (64x64) sobre el mapa negro de la intro,
sin recuadros.

Pasos (para clase):
  1. Imagen y paleta del Profesor (assets/acisclo/acisclo_gba.png, sacado del
     entrenador 107 de Unbound con otra paleta).
  2. Registrar la PALETA en la tabla de paletas de sprites del mapa
     (0xEB994C), en un hueco libre (entrada 360), con la etiqueta 0x1268.
  3. Crear la FICHA del sprite (0x24 bytes) copiando la de un sprite de 64x64
     que ya existe (0x3A4B04) y cambiando su paleta y sus imágenes.
  4. Apuntar a esa ficha desde un hueco libre de la tabla de sprites nº 0
     (0x8110E0, posición 251): su número de gráfico es 0xFB.
  5. Añadir una 3.ª persona al mapa de la intro (cabecera 0xB55F58), oculta
     al cargar (flag 0x2D, como las otras dos).
  6. Desvío en el script: tras la página 1, showsprite 3 + mensaje + hidesprite 3.

Todos los huecos se comprueban antes de escribir. Crea un respaldo.
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from insertar_pokemon import png_a_tiles, png_a_paleta  # noqa: E402
from cap0_imagenes import PAGINA1, LARGO_PAGINA, VUELTA  # noqa: E402

IMAGEN = t.RAIZ / "assets" / "acisclo" / "acisclo_gba.png"
TABLA_PALETAS_OW = 0xEB994C
HUECO_PALETA = 360
ETIQUETA_PALETA = 0x1268
FICHA_MODELO = 0x3A4B04          # sprite de mapa de 64x64 que copiamos
TABLA_OW_0 = 0x8110E0
HUECO_OW = 251                   # 251-255 son relleno sin uso (apuntan a 0x3A3BB0); ningún mapa usa 0xFB-0xFF
RELLENO_OW = 0x083A3BB0
GRAFICO = HUECO_OW               # 0xFB (un solo byte: probado que el byte alto no se lee del mapa)
MAPA_INTRO = 0xB55F58
PERSONA = 3
FLAG_OCULTO = 0x2D
TEXTO = "¡Encantado de conocerte!"


def P(rom, o):
    return struct.unpack("<I", rom[o:o + 4])[0]


def ptr(o):
    return struct.pack("<I", 0x08000000 + o)


def main():
    rom = bytearray(t.ROM.read_bytes())
    original = (t.RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba").read_bytes()

    # --- comprobaciones previas ---
    if rom[PAGINA1] != original[PAGINA1]:
        sys.exit("El script de la intro ya está modificado. Ejecuta antes cap0_quitar_imagenes.py.")
    ent_pal = TABLA_PALETAS_OW + 8 * HUECO_PALETA
    if rom[ent_pal:ent_pal + 8] != b"\x00" * 8:
        sys.exit(f"El hueco de paleta {HUECO_PALETA} no está libre")
    tags = {struct.unpack("<H", rom[TABLA_PALETAS_OW + 8 * k + 4:TABLA_PALETAS_OW + 8 * k + 6])[0] for k in range(366)}
    if ETIQUETA_PALETA in tags:
        sys.exit("La etiqueta de paleta ya está en uso")
    ent_ow = TABLA_OW_0 + 4 * HUECO_OW
    if P(rom, ent_ow) != RELLENO_OW:
        sys.exit(f"El hueco {HUECO_OW} de la tabla de sprites 0 no está libre")
    eventos = P(rom, MAPA_INTRO + 4) - 0x08000000
    n_personas = rom[eventos]
    if n_personas != 2:
        sys.exit(f"El mapa de la intro tiene {n_personas} personas (se esperaban 2)")

    # --- datos nuevos ---
    tiles = png_a_tiles(IMAGEN)                      # 2048 bytes, 4bpp, sin comprimir (los sprites del mapa van así)
    paleta = png_a_paleta(IMAGEN)                    # 32 bytes
    ficha = bytearray(rom[FICHA_MODELO:FICHA_MODELO + 0x24])
    imgs_modelo = P(rom, FICHA_MODELO + 0x1C) - 0x08000000
    n_frames = 0
    while struct.unpack("<H", rom[imgs_modelo + 8 * n_frames + 4:imgs_modelo + 8 * n_frames + 6])[0] == 0x800 \
            and 0x08000000 <= P(rom, imgs_modelo + 8 * n_frames) < 0x0A000000:
        n_frames += 1
    n_frames = max(n_frames, 1)

    trabajo = bytearray(rom)

    def colocar(datos, alinear=4):
        o = t.buscar_libre(bytes(trabajo), len(datos), alinear=alinear)
        trabajo[o:o + len(datos)] = datos
        return o

    o_tiles = colocar(tiles)
    o_pal = colocar(paleta)
    # tabla de imágenes: todos los fotogramas son el mismo dibujo (el Profesor no camina)
    tabla_imgs = b"".join(ptr(o_tiles) + struct.pack("<HH", 0x800, 0) for _ in range(n_frames))
    o_imgs = colocar(tabla_imgs)
    ficha[2:4] = struct.pack("<H", ETIQUETA_PALETA)
    ficha[0x1C:0x20] = ptr(o_imgs)
    o_ficha = colocar(bytes(ficha))

    # persona nueva: copia de la persona 1 con otro id, gráfico y flag
    personas_viejas = P(rom, eventos + 4) - 0x08000000
    p1 = bytearray(rom[personas_viejas:personas_viejas + 24])
    nueva = bytearray(p1)
    nueva[0] = PERSONA
    nueva[1] = GRAFICO
    nueva[2] = 0
    nueva[20:22] = struct.pack("<H", FLAG_OCULTO)
    lista = bytes(rom[personas_viejas:personas_viejas + 48]) + bytes(nueva)
    o_lista = colocar(lista)

    # texto y bloque del desvío
    o_txt = colocar(t.codificar(TEXTO), alinear=1)
    paginas = original[PAGINA1:VUELTA]
    bloque = (paginas[:LARGO_PAGINA]
              + bytes([0x55, PERSONA, 0x00])                 # showsprite 3
              + b"\x0F\x00" + ptr(o_txt) + b"\x09\x04"       # mensaje normal
              + bytes([0x53, PERSONA, 0x00])                 # hidesprite 3
              + paginas[LARGO_PAGINA:]
              + bytes([0x05]) + ptr(VUELTA))                 # goto página 3
    o_bloque = colocar(bloque)

    # --- conectar todo ---
    trabajo[ent_pal:ent_pal + 8] = ptr(o_pal) + struct.pack("<HH", ETIQUETA_PALETA, 0)
    trabajo[ent_ow:ent_ow + 4] = ptr(o_ficha)
    trabajo[eventos] = 3
    trabajo[eventos + 4:eventos + 8] = ptr(o_lista)
    desvio = bytes([0x05]) + ptr(o_bloque)
    trabajo[PAGINA1:VUELTA] = desvio + b"\x00" * (2 * LARGO_PAGINA - len(desvio))

    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-profesor-mapa_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp)
    print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(trabajo)
    print(f"Imagen 0x{o_tiles:X} · paleta 0x{o_pal:X} (etiqueta 0x{ETIQUETA_PALETA:X}) · "
          f"{n_frames} fotogramas en 0x{o_imgs:X} · ficha 0x{o_ficha:X} (gráfico 0x{GRAFICO:04X})")
    print(f"Personas del mapa de la intro: 3 (lista en 0x{o_lista:X}) · desvío -> 0x{o_bloque:X}")


if __name__ == "__main__":
    main()
