"""
textos.py
=========
Herramientas para los TEXTOS de la ROM (juego de caracteres de la 3.ª generación).

CONCEPTOS (para clase)
----------------------
* La GBA no guarda letras en ASCII: cada juego usa su propia tabla. En FireRed
  la 'A' es el byte 0xBB, la 'a' es 0xD5, el espacio es 0x00...
* Cada texto termina con el byte 0xFF.
* Hay bytes de CONTROL dentro del texto:
    0xFE = salto de línea          ({n} en este script)
    0xFA = la línea sube (scroll)  ({l})
    0xFB = caja de texto nueva     ({p})
    0xFD 0x01 = nombre del jugador ({JUGADOR})
    0xFD 0x06 = nombre del rival   ({RIVAL})
    0xFC xx ... = órdenes (color, pausa, sonido...) ({FC:xx...} en bruto)
* El código del juego encuentra cada texto mediante un PUNTERO (4 bytes,
  0x08000000 + posición). Si el texto nuevo cabe en el sitio del viejo, se
  escribe encima; si no, va a espacio libre y se REPUNTEAN todos los punteros.

Uso como programa:
  python scripts/textos.py buscar "Welcome"      -> lista textos que contienen eso
  python scripts/textos.py ver 0x123456          -> muestra el texto y quién apunta a él
"""
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ROM = RAIZ / "MiHack.gba"

TABLA = {
    0x00: " ", 0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç", 0x05: "È", 0x06: "É", 0x07: "Ê", 0x08: "Ë",
    0x09: "Ì", 0x0B: "Î", 0x0C: "Ï", 0x0D: "Ò", 0x0E: "Ó", 0x0F: "Ô", 0x10: "Œ", 0x11: "Ù", 0x12: "Ú",
    0x13: "Û", 0x14: "Ñ", 0x15: "ß", 0x16: "à", 0x17: "á", 0x19: "ç", 0x1A: "è", 0x1B: "é", 0x1C: "ê",
    0x1D: "ë", 0x1E: "ì", 0x20: "î", 0x21: "ï", 0x22: "ò", 0x23: "ó", 0x24: "ô", 0x25: "œ", 0x26: "ù",
    0x27: "ú", 0x28: "û", 0x29: "ñ", 0x2A: "º", 0x2B: "ª", 0x2D: "&", 0x2E: "+", 0x35: "=", 0x36: ";",
    0x51: "¿", 0x52: "¡", 0x5A: "Í", 0x5B: "%", 0x5C: "(", 0x5D: ")", 0x68: "â", 0x6F: "í",
    0xA1: "0", 0xA2: "1", 0xA3: "2", 0xA4: "3", 0xA5: "4", 0xA6: "5", 0xA7: "6", 0xA8: "7", 0xA9: "8",
    0xAA: "9", 0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-", 0xAF: "·", 0xB0: "…", 0xB1: "“", 0xB2: "”",
    0xB3: "‘", 0xB4: "'", 0xB5: "♂", 0xB6: "♀", 0xB7: "$", 0xB8: ",", 0xB9: "×", 0xBA: "/",
    0xF0: ":", 0xF1: "Ä", 0xF2: "Ö", 0xF3: "Ü", 0xF4: "ä", 0xF5: "ö", 0xF6: "ü",
}
for i in range(26):
    TABLA[0xBB + i] = chr(65 + i)
    TABLA[0xD5 + i] = chr(97 + i)
INVERSA = {v: k for k, v in TABLA.items()}
CODIGOS = {"{n}": b"\xFE", "{l}": b"\xFA", "{p}": b"\xFB", "{JUGADOR}": b"\xFD\x01", "{RIVAL}": b"\xFD\x06"}


def decodificar(datos: bytes, off: int = 0, maximo: int = 2000) -> str:
    out, i = [], off
    while i < len(datos) and i - off < maximo:
        b = datos[i]
        if b == 0xFF:
            break
        if b == 0xFE: out.append("{n}")
        elif b == 0xFA: out.append("{l}")
        elif b == 0xFB: out.append("{p}")
        elif b == 0xFD:
            i += 1; out.append({1: "{JUGADOR}", 6: "{RIVAL}"}.get(datos[i], f"{{FD:{datos[i]:02X}}}"))
        elif b == 0xFC:
            # longitud de argumentos según el código (simplificado)
            cod = datos[i + 1]
            nargs = {0x01: 1, 0x02: 1, 0x03: 1, 0x04: 3, 0x05: 1, 0x06: 1, 0x07: 0, 0x08: 1, 0x09: 0,
                     0x0A: 0, 0x0B: 2, 0x0C: 1, 0x0D: 0, 0x0E: 1, 0x0F: 0, 0x10: 2, 0x11: 1, 0x12: 1,
                     0x13: 1, 0x14: 1, 0x15: 0, 0x16: 0, 0x17: 0, 0x18: 0}.get(cod, 0)
            out.append("{FC:" + datos[i + 1:i + 2 + nargs].hex().upper() + "}"); i += 1 + nargs
        else:
            out.append(TABLA.get(b, f"[{b:02X}]"))
        i += 1
    return "".join(out)


def codificar(texto: str) -> bytes:
    out, i = bytearray(), 0
    while i < len(texto):
        if texto[i] == "{":
            fin = texto.index("}", i) + 1
            tok = texto[i:fin]
            if tok in CODIGOS:
                out += CODIGOS[tok]
            elif tok.startswith("{FC:"):
                out += b"\xFC" + bytes.fromhex(tok[4:-1])
            elif tok.startswith("{FD:"):
                out += b"\xFD" + bytes.fromhex(tok[4:-1])
            else:
                raise ValueError(f"código desconocido: {tok}")
            i = fin
            continue
        c = texto[i]
        if c not in INVERSA:
            raise ValueError(f"carácter no admitido: {c!r}")
        out.append(INVERSA[c]); i += 1
    return bytes(out) + b"\xFF"


def punteros_a(rom: bytes, off: int) -> list:
    p = struct.pack("<I", 0x08000000 + off)
    res, i = [], rom.find(p)
    while i != -1:
        res.append(i)   # en los scripts los punteros NO están alineados a 4
        i = rom.find(p, i + 1)
    return res


ZONA_LIBRE = (0x15FA500, 0x15FA3E0 + 471 * 1024)


def buscar_libre(rom: bytes, tam: int, alinear: int = 1, desde: int = 0) -> int:
    """Hueco de 'tam' bytes a 0xFF, con un 0xFF de separación antes y después
    (así nunca se pisa el 0xFF final de un texto insertado antes).
    'alinear=4' para datos comprimidos y scripts largos (la BIOS exige
    que los datos LZ77 empiecen en una dirección múltiplo de 4)."""
    ini, fin = ZONA_LIBRE
    p = max(ini, desde)
    while p + tam + 1 <= fin:
        if p % alinear == 0 and rom[p - 1:p + tam + 1] == b"\xFF" * (tam + 2):
            return p
        p += 1
    raise RuntimeError("no queda espacio libre en la zona")


def sustituir(rom: bytearray, off: int, texto_nuevo: str) -> str:
    """Cambia el texto que empieza en 'off'. Devuelve una línea de informe."""
    viejo_fin = rom.index(0xFF, off)
    hueco = viejo_fin - off + 1
    nuevo = codificar(texto_nuevo)
    if len(nuevo) <= hueco:
        rom[off:off + hueco] = nuevo + b"\xFF" * (hueco - len(nuevo))
        return f"0x{off:X}: escrito en su sitio ({len(nuevo)}/{hueco} bytes)"
    refs = punteros_a(bytes(rom), off)
    if not refs:
        raise RuntimeError(f"0x{off:X}: no cabe y no hay punteros para repuntear")
    destino = buscar_libre(bytes(rom), len(nuevo))
    rom[destino:destino + len(nuevo)] = nuevo
    for r in refs:
        rom[r:r + 4] = struct.pack("<I", 0x08000000 + destino)
    return (f"0x{off:X}: no cabía ({len(nuevo)} > {hueco} bytes) -> movido a 0x{destino:X}, "
            f"{len(refs)} puntero(s) repunteado(s)")


def inicio_texto(rom: bytes, off: int) -> int:
    """Retrocede hasta el byte siguiente al 0xFF anterior (inicio probable del texto)."""
    while off > 0 and rom[off - 1] != 0xFF:
        off -= 1
    return off


def buscar(rom: bytes, frase: str):
    patron = codificar(frase)[:-1]
    i = rom.find(patron)
    while i != -1:
        ini = inicio_texto(rom, i)
        yield ini, decodificar(rom, ini), punteros_a(rom, ini)
        i = rom.find(patron, i + 1)


if __name__ == "__main__":
    rom = ROM.read_bytes()
    if len(sys.argv) >= 3 and sys.argv[1] == "buscar":
        for ini, txt, ptrs in buscar(rom, sys.argv[2]):
            print(f"0x{ini:X}  punteros={[hex(p) for p in ptrs]}\n   {txt[:300]}\n")
    elif len(sys.argv) >= 3 and sys.argv[1] == "ver":
        off = int(sys.argv[2], 16)
        print(decodificar(rom, off)); print("punteros:", [hex(p) for p in punteros_a(rom, off)])
    else:
        print(__doc__)
