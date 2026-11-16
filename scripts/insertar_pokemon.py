"""
insertar_pokemon.py
===================
Sustituye el sprite frontal, el trasero, las dos paletas (normal y shiny) y el
nombre de UNA especie de MiHack.gba, sin usar HexManiacAdvance.

Hace a mano lo que HMA hace al pulsar "Import":
  1. Convierte el PNG indexado en TILES de 8x8 a 4 bits por píxel (formato GBA).
  2. Comprime tiles y paletas con LZ77, el formato que entiende la BIOS de la GBA.
  3. Busca ESPACIO LIBRE (zona llena de 0xFF) y escribe ahí los datos nuevos.
  4. REPUNTEA: cambia el puntero de la fila de la especie en cada tabla para
     que apunte a los datos nuevos. Los datos viejos se quedan donde estaban,
     pero ya nadie los usa.
  5. Lo vuelve a leer todo y comprueba que coincide byte a byte.

Uso (desde la carpeta GBA):
  herramientas\\python-venv\\Scripts\\python.exe scripts\\insertar_pokemon.py ^
      --especie 1 --nombre Arquillo --carpeta assets\\arquillo

La carpeta debe tener frontal_gba.png, trasero_gba.png y frontal_shiny.png
(los genera png_a_gba.py). Antes de escribir, crea un respaldo automático.

Las direcciones de las tablas son las de Unbound v2.0.3.2 (ver GUIA.md).
"""
import argparse
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ROM = RAIZ / "MiHack.gba"

TABLA_NOMBRES = 0x1689AE8     # 11 bytes por especie
TABLA_FRONTAL = 0x1A26798     # 8 bytes: puntero, tamaño (0x800), especie
TABLA_TRASERA = 0x19E8A84
TABLA_PAL_NORMAL = 0x1A3B3A0  # 8 bytes: puntero, etiqueta (= especie)
TABLA_PAL_SHINY = 0x1A47BEC   # 8 bytes: puntero, etiqueta (= especie + 1268)
NUM_ESPECIES = 1268
ZONA_LIBRE = (0x15FA500, 0x15FA3E0 + 471 * 1024)  # bloque de 0xFF medido; se deja margen al principio

# Juego de caracteres de FireRed (lo necesario para nombres)
CHARS = {" ": 0x00, ".": 0xAD, "-": 0xAE, "'": 0xB4, "é": 0x1B}
CHARS.update({chr(65 + i): 0xBB + i for i in range(26)})
CHARS.update({chr(97 + i): 0xD5 + i for i in range(26)})
CHARS.update({str(i): 0xA1 + i for i in range(10)})


# ---------------------------------------------------------------- LZ77
def lz77_comprimir(datos: bytes) -> bytes:
    """Compresor LZ77 compatible con la BIOS de GBA (tipo 0x10).
    Distancia mínima 2 para que también sirva al descomprimir en VRAM."""
    # Para ir rápido se guarda, para cada trío de bytes, en qué posiciones apareció
    # (tabla hash). Solo se comparan esas posiciones, no las 4096 anteriores.
    out = bytearray([0x10]) + len(datos).to_bytes(3, "little")
    vistos = {}
    def registrar(pos):
        if pos + 3 <= len(datos):
            vistos.setdefault(datos[pos:pos + 3], []).append(pos)
    i = 0
    while i < len(datos):
        flag_pos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= len(datos):
                break
            mejor_len, mejor_dist = 0, 0
            for j in reversed(vistos.get(datos[i:i + 3], [])):
                dist = i - j
                if dist > 4096:
                    break
                if dist < 2:
                    continue
                n = 0
                while n < 18 and i + n < len(datos) and datos[i + n] == datos[j + n]:
                    n += 1
                if n > mejor_len:
                    mejor_len, mejor_dist = n, dist
                    if n == 18:
                        break
            avance = mejor_len if mejor_len >= 3 else 1
            for k in range(i, i + avance):
                registrar(k)
            if mejor_len >= 3:
                flags |= 0x80 >> bit
                d = mejor_dist - 1
                out += bytes([((mejor_len - 3) << 4) | (d >> 8), d & 0xFF])
                i += mejor_len
            else:
                out.append(datos[i]); i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def lz77_descomprimir(rom: bytes, off: int) -> bytes:
    assert rom[off] == 0x10, f"no hay LZ77 en 0x{off:X}"
    size = int.from_bytes(rom[off + 1:off + 4], "little"); out = bytearray(); p = off + 4
    while len(out) < size:
        flags = rom[p]; p += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                n = (rom[p] >> 4) + 3; d = ((rom[p] & 0xF) << 8 | rom[p + 1]) + 1; p += 2
                for _ in range(n):
                    out.append(out[-d])
            else:
                out.append(rom[p]); p += 1
    return bytes(out)


# ---------------------------------------------------------------- formatos GBA
def png_a_tiles(ruta: Path) -> bytes:
    """PNG indexado 64x64 -> 2048 bytes de tiles 8x8 a 4bpp (2 píxeles por byte, el izquierdo en los 4 bits bajos)."""
    im = Image.open(ruta)
    if im.mode != "P" or im.size != (64, 64):
        sys.exit(f"ERROR: {ruta.name} debe ser PNG indexado de 64x64 (pásalo por png_a_gba.py)")
    px = im.load(); out = bytearray()
    for ty in range(0, 64, 8):
        for tx in range(0, 64, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    a, b = px[tx + x, ty + y], px[tx + x + 1, ty + y]
                    if a > 15 or b > 15:
                        sys.exit(f"ERROR: {ruta.name} usa índices de color > 15")
                    out.append(a | (b << 4))
    return bytes(out)


def png_a_paleta(ruta: Path) -> bytes:
    """Paleta del PNG -> 16 colores BGR555 (32 bytes)."""
    pal = Image.open(ruta).getpalette()[:48]
    pal += [0] * (48 - len(pal))
    out = bytearray()
    for i in range(16):
        r, g, b = (c >> 3 for c in pal[i * 3:i * 3 + 3])
        out += struct.pack("<H", r | (g << 5) | (b << 10))
    return bytes(out)


def codificar_nombre(nombre: str) -> bytes:
    if len(nombre) > 10:
        sys.exit("ERROR: el nombre puede tener como máximo 10 letras")
    try:
        datos = bytes(CHARS[c] for c in nombre)
    except KeyError as e:
        sys.exit(f"ERROR: carácter no admitido en el nombre: {e}")
    return datos + b"\xFF" * (11 - len(datos))


# ---------------------------------------------------------------- ROM
def leer_ptr(rom, off):
    v = struct.unpack("<I", rom[off:off + 4])[0]
    assert 0x08000000 <= v < 0x0A000000, f"puntero no válido en 0x{off:X}: {v:08X}"
    return v - 0x08000000


def buscar_libre(rom, tam, desde):
    """Primer hueco de 'tam' bytes a 0xFF dentro de la zona libre, alineado a 4."""
    ini, fin = ZONA_LIBRE
    p = max(ini, desde)
    p += (-p) % 4
    while p + tam <= fin:
        if rom[p:p + tam] == b"\xFF" * tam:
            return p
        p += 4
    sys.exit("ERROR: no queda espacio libre suficiente en la zona elegida")


def main():
    ap = argparse.ArgumentParser(description="Sustituye sprites, paletas y nombre de una especie")
    ap.add_argument("--especie", type=int, required=True, help="número interno de especie (1-1267)")
    ap.add_argument("--nombre", help="nuevo nombre (si se omite, no se cambia)")
    ap.add_argument("--carpeta", type=Path, required=True)
    ap.add_argument("--solo-frontal", action="store_true",
                    help="solo sprite frontal y paleta normal (p. ej. un retrato para showpokepic)")
    ap.add_argument("--simular", action="store_true", help="no escribe nada, solo muestra qué haría")
    a = ap.parse_args()
    if not 1 <= a.especie < NUM_ESPECIES:
        sys.exit("ERROR: especie fuera de rango")

    rom = bytearray(ROM.read_bytes())
    e = a.especie
    nombre_viejo = rom[TABLA_NOMBRES + 11 * e:TABLA_NOMBRES + 11 * e + 11]
    # Comprobaciones de que las tablas están donde creemos
    assert struct.unpack("<HH", rom[TABLA_FRONTAL + 8 * e + 4:TABLA_FRONTAL + 8 * e + 8]) == (0x800, e)
    assert struct.unpack("<HH", rom[TABLA_TRASERA + 8 * e + 4:TABLA_TRASERA + 8 * e + 8]) == (0x800, e)
    assert struct.unpack("<H", rom[TABLA_PAL_NORMAL + 8 * e + 4:TABLA_PAL_NORMAL + 8 * e + 6])[0] == e
    assert struct.unpack("<H", rom[TABLA_PAL_SHINY + 8 * e + 4:TABLA_PAL_SHINY + 8 * e + 6])[0] == e + NUM_ESPECIES
    print(f"Especie {e}: tablas verificadas.")

    # (tabla, archivo PNG, función que lo convierte)
    fuentes = {
        "sprite frontal": (TABLA_FRONTAL, "frontal_gba.png", png_a_tiles),
        "sprite trasero": (TABLA_TRASERA, "trasero_gba.png", png_a_tiles),
        "paleta normal": (TABLA_PAL_NORMAL, "frontal_gba.png", png_a_paleta),
        "paleta shiny": (TABLA_PAL_SHINY, "frontal_shiny.png", png_a_paleta),
    }
    if a.solo_frontal:
        fuentes = {k: v for k, v in fuentes.items() if k in ("sprite frontal", "paleta normal")}
    piezas = {k: (tab, lz77_comprimir(f(a.carpeta / png))) for k, (tab, png, f) in fuentes.items()}

    # Espacio libre compartido con textos.py: deja un 0xFF de separación con
    # cualquier dato insertado antes y alinea a 4, como exige la BIOS para LZ77.
    sys.path.insert(0, str(Path(__file__).parent))
    import textos
    plan, trabajo = [], bytearray(rom)
    for nombre, (tabla, datos) in piezas.items():
        off = textos.buscar_libre(bytes(trabajo), len(datos), alinear=4)
        trabajo[off:off + len(datos)] = datos   # reservar para que la siguiente pieza no se solape
        plan.append((nombre, tabla, datos, off, leer_ptr(rom, tabla + 8 * e)))
    for nombre, tabla, datos, off, viejo in plan:
        print(f"  {nombre:15}: {len(datos):5} bytes comprimidos -> 0x{off:X} (antes en 0x{viejo:X})")
    if a.nombre:
        print(f"  nombre: se cambia por '{a.nombre}'")
    if a.simular:
        print("Simulación: no se ha escrito nada."); return

    # Respaldo automático
    resp = RAIZ / "respaldos" / f"MiHack_antes-de-insertar_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    resp.parent.mkdir(exist_ok=True); shutil.copy2(ROM, resp)
    print(f"Respaldo: {resp.relative_to(RAIZ)}")

    for nombre, tabla, datos, off, viejo in plan:
        rom[off:off + len(datos)] = datos                                    # datos nuevos
        rom[tabla + 8 * e:tabla + 8 * e + 4] = struct.pack("<I", 0x08000000 + off)  # repunteo
    if a.nombre:
        rom[TABLA_NOMBRES + 11 * e:TABLA_NOMBRES + 11 * e + 11] = codificar_nombre(a.nombre)
    ROM.write_bytes(rom)

    # Verificación: releer desde disco y comparar cada pieza con su PNG
    rom2 = ROM.read_bytes()
    ok = all(lz77_descomprimir(rom2, leer_ptr(rom2, tab + 8 * e)) == f(a.carpeta / png)
             for tab, png, f in fuentes.values())
    if a.nombre:
        ok &= rom2[TABLA_NOMBRES + 11 * e:TABLA_NOMBRES + 11 * e + 11] == codificar_nombre(a.nombre)
    print("Verificación:", "TODO CORRECTO" if ok else "FALLO - restaura el respaldo")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
