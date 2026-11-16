"""
png_a_gba.py
============
Convierte un PNG cualquiera en un PNG indexado de 16 colores válido para GBA
y genera su paleta shiny.

CONCEPTOS (para clase)
----------------------
* La GBA dibuja los sprites con PALETAS de 16 colores. Cada píxel no guarda
  un color, guarda un número del 0 al 15 que apunta a la paleta.
* El color 0 de la paleta es SIEMPRE transparente. Por eso solo quedan
  15 colores "de verdad" para el dibujo.
* Cada color de la GBA usa 15 bits: 5 para rojo, 5 para verde, 5 para azul.
  Eso da 32 niveles por canal (0-31), no 256. En un PNG eso equivale a
  valores múltiplos de 8 (0, 8, 16, ..., 248). Este script redondea a eso.
* Los sprites se dibujan en "tiles" de 8x8 píxeles, así que ancho y alto
  tienen que ser múltiplos de 8, y cada tipo de sprite tiene tamaños fijos.
* El shiny NO es otro dibujo: es el MISMO dibujo con OTRA paleta. Por eso
  aquí solo se cambian los colores, nunca los índices de los píxeles.
* El sprite frontal y el trasero de un Pokémon comparten paleta. Convierte
  primero el frontal y luego el trasero con --usar-paleta frontal_gba.png.

USO
---
  python scripts/png_a_gba.py entrada.png --tipo frontal
  python scripts/png_a_gba.py trasero.png --tipo trasero --usar-paleta salida/frontal_gba.png
  python scripts/png_a_gba.py tile.png --tipo libre --shiny-tono 0

Salida (junto a la entrada, o en --carpeta):
  NOMBRE_gba.png         PNG indexado de 16 colores (listo para importar)
  NOMBRE_shiny.png       el mismo sprite con la paleta shiny (para verlo)
  NOMBRE_normal.pal      paleta normal en formato JASC-PAL
  NOMBRE_shiny.pal       paleta shiny en formato JASC-PAL
  NOMBRE_paletas.txt     ambas paletas en hexadecimal GBA (BGR555, little endian)
"""
import argparse
import colorsys
import sys
from pathlib import Path

from PIL import Image

# Tamaños aceptados por tipo: lista de (ancho, alto). None = cualquiera múltiplo de 8.
TAMANOS = {
    "frontal": [(64, 64)],               # sprite de combate frontal
    "trasero": [(64, 64)],               # sprite de combate trasero
    "icono": [(32, 64)],                 # icono del menú: 2 fotogramas de 32x32, uno encima del otro
    "overworld16x16": "hoja:16:16",      # personaje en el mapa (hoja de fotogramas en horizontal)
    "overworld16x32": "hoja:16:32",
    "overworld32x32": "hoja:32:32",
    "entrenador": [(64, 64)],            # sprite de entrenador en combate
    "libre": None,                       # tiles, tilesets, etc.: solo múltiplos de 8
}


def a_15bits(c):
    """Redondea un canal 0-255 al nivel GBA más cercano (0-31) y lo devuelve en escala 0-248."""
    return min(31, round(c / 8)) * 8   # idempotente: un valor ya válido (p. ej. 248) no cambia


def color_15(rgb):
    return tuple(a_15bits(c) for c in rgb[:3])


def hex_gba(rgb):
    """Color RGB (0-248) -> 2 bytes BGR555 en little endian, como se guarda en la ROM."""
    r, g, b = (c // 8 for c in rgb)
    valor = r | (g << 5) | (b << 10)
    return f"{valor & 0xFF:02X} {valor >> 8:02X}"


def comprobar_tamano(tipo, w, h):
    regla = TAMANOS[tipo]
    if w % 8 or h % 8:
        return f"{w}x{h} no es múltiplo de 8 (la GBA dibuja en tiles de 8x8)."
    if regla is None:
        return None
    if isinstance(regla, str):  # hoja de overworld
        _, fw, fh = regla.split(":")
        fw, fh = int(fw), int(fh)
        if h != fh or w % fw:
            return (f"Una hoja '{tipo}' debe medir {fh} de alto y un múltiplo de {fw} de ancho "
                    f"(cada fotograma {fw}x{fh}); la tuya mide {w}x{h}.")
        return None
    if (w, h) not in regla:
        esperado = " o ".join(f"{a}x{b}" for a, b in regla)
        return f"Un sprite '{tipo}' debe medir {esperado}; el tuyo mide {w}x{h}."
    return None


def pixeles(img):
    """Lista de píxeles (compatible con Pillow antiguo y nuevo)."""
    f = getattr(img, "get_flattened_data", None)
    return list(f() if f else img.getdata())


def detectar_fondo(img, fondo_hex, usados):
    """Elige el color que hará de transparente (índice 0).

    - Si lo indicas con --fondo, se usa ese.
    - Si el PNG tiene transparencia real, se elige un color que NO aparezca en el
      dibujo (si no, un contorno negro desaparecería al coincidir con el fondo).
    - Si no tiene transparencia, por convención el píxel superior izquierdo es fondo.
    """
    if fondo_hex:
        fondo_hex = fondo_hex.lstrip("#")
        return tuple(int(fondo_hex[i:i + 2], 16) for i in (0, 2, 4)), False
    if any(p[3] < 128 for p in pixeles(img)):
        for candidato in [(248, 0, 248), (0, 248, 248), (0, 248, 0), (248, 248, 0)]:
            if color_15(candidato) not in usados:
                return candidato, True
    return img.getpixel((0, 0))[:3], False


def cargar_paleta_ref(ruta):
    ref = Image.open(ruta)
    if ref.mode != "P":
        sys.exit(f"ERROR: {ruta} no es un PNG indexado (conviértelo primero con este script).")
    pal = ref.getpalette()[:48]
    return [tuple(pal[i:i + 3]) for i in range(0, 48, 3)]


def mas_cercano(rgb, paleta):
    return min(range(1, 16), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, paleta[i])))


def paleta_shiny(paleta, tono, saturacion, brillo):
    """Gira el tono (en grados) de los colores 1-15. El 0 (transparente) no se toca."""
    nueva = [paleta[0]]
    for rgb in paleta[1:]:
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
        if s < 0.12:            # grises, blanco y negro: se dejan, si no el contorno cambiaría de color
            nueva.append(rgb)
            continue
        h = (h + tono / 360) % 1.0
        s = max(0.0, min(1.0, s * saturacion))
        v = max(0.0, min(1.0, v * brillo))
        nueva.append(color_15(tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))))
    return nueva


def guardar_jasc(ruta, paleta):
    lineas = ["JASC-PAL", "0100", "16"] + [f"{r} {g} {b}" for r, g, b in paleta]
    ruta.write_text("\r\n".join(lineas) + "\r\n", encoding="ascii")


def main():
    p = argparse.ArgumentParser(description="PNG -> PNG indexado de 16 colores para GBA + paleta shiny")
    p.add_argument("entrada", type=Path)
    p.add_argument("--tipo", choices=TAMANOS, default="libre", help="tipo de sprite (comprueba el tamaño)")
    p.add_argument("--fondo", help="color de fondo/transparente en hex (por defecto: píxel superior izquierdo)")
    p.add_argument("--usar-paleta", type=Path, help="reutilizar la paleta de otro PNG ya convertido")
    p.add_argument("--shiny-tono", type=float, default=150, help="grados de giro de tono para el shiny (0-360)")
    p.add_argument("--shiny-saturacion", type=float, default=1.0, help="multiplicador de saturación del shiny")
    p.add_argument("--shiny-brillo", type=float, default=1.0, help="multiplicador de brillo del shiny")
    p.add_argument("--carpeta", type=Path, help="carpeta de salida (por defecto, la de la entrada)")
    a = p.parse_args()

    img = Image.open(a.entrada).convert("RGBA")
    w, h = img.size
    print(f"Entrada: {a.entrada.name}  {w}x{h}")

    # 1) Tamaño
    error = comprobar_tamano(a.tipo, w, h)
    if error:
        sys.exit("ERROR de tamaño: " + error)
    print(f"  [ok] tamaño válido para '{a.tipo}'")

    # 2) Transparencia -> color de fondo; todos los colores a 15 bits
    pix = [None if al < 128 else color_15((r, g, b)) for r, g, b, al in pixeles(img)]
    fondo, por_alfa = detectar_fondo(img, a.fondo, set(pix))
    fondo = color_15(fondo)
    if not por_alfa:
        pix = [None if c == fondo else c for c in pix]
    origen = "elegido porque el PNG ya trae transparencia" if por_alfa else "tomado del fondo del dibujo"
    print(f"  [ok] color transparente (índice 0): #{fondo[0]:02X}{fondo[1]:02X}{fondo[2]:02X} ({origen})")

    # 3) Paleta
    if a.usar_paleta:
        paleta = cargar_paleta_ref(a.usar_paleta)
        print(f"  [ok] usando la paleta de {a.usar_paleta.name}")
        indices = [0 if c is None else mas_cercano(c, paleta) for c in pix]
    else:
        unicos = sorted({c for c in pix if c is not None})
        if len(unicos) > 15:
            print(f"  [aviso] el dibujo tiene {len(unicos)} colores; la GBA solo admite 15 + transparente.")
            print("          Reduzco a 15 automáticamente. Para controlarlo tú, reduce colores en tu editor.")
            # Se cuantiza solo la parte visible, sin difuminado (el tramado queda mal en pixel art).
            visibles = [c for c in pix if c is not None]
            solo = Image.new("RGB", (len(visibles), 1))
            solo.putdata(visibles)
            q = solo.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            qpal = q.getpalette()
            unicos = sorted({color_15(tuple(qpal[i * 3:i * 3 + 3])) for i in set(pixeles(q))} - {fondo})
        paleta = [fondo] + unicos
        while len(paleta) < 16:
            paleta.append((0, 0, 0))   # huecos sin usar
        indices = [0 if c is None else (paleta.index(c, 1) if c in paleta[1:] else mas_cercano(c, paleta))
                   for c in pix]
        print(f"  [ok] {len(set(indices) - {0})} colores usados de 15 posibles")

    # 4) Guardar PNG indexado
    salida_dir = a.carpeta or a.entrada.parent
    salida_dir.mkdir(parents=True, exist_ok=True)
    base = a.entrada.stem
    out = Image.new("P", (w, h))
    out.putpalette([v for c in paleta for v in c])
    out.putdata(indices)
    ruta_gba = salida_dir / f"{base}_gba.png"
    out.save(ruta_gba, transparency=0)

    # 5) Shiny
    shiny = paleta_shiny(paleta, a.shiny_tono, a.shiny_saturacion, a.shiny_brillo)
    out_s = out.copy()
    out_s.putpalette([v for c in shiny for v in c])
    out_s.save(salida_dir / f"{base}_shiny.png", transparency=0)

    guardar_jasc(salida_dir / f"{base}_normal.pal", paleta)
    guardar_jasc(salida_dir / f"{base}_shiny.pal", shiny)
    (salida_dir / f"{base}_paletas.txt").write_text(
        "Paleta normal (hex GBA, 32 bytes):\n" + " ".join(hex_gba(c) for c in paleta) +
        "\n\nPaleta shiny (hex GBA, 32 bytes):\n" + " ".join(hex_gba(c) for c in shiny) + "\n",
        encoding="utf-8")

    # 6) Comprobación final: releer y validar
    chk = Image.open(ruta_gba)
    assert chk.mode == "P" and len(chk.getpalette()) // 3 >= 16 and max(pixeles(chk)) <= 15
    print(f"  [ok] guardado {ruta_gba.name} (+ _shiny.png, .pal, _paletas.txt)")
    if a.tipo == "icono":
        print("  [nota] los iconos de FireRed usan paletas compartidas fijas: el shiny no se aplica a iconos.")


if __name__ == "__main__":
    main()
