"""Busca la tabla de nombres de especies en la ROM (solo lectura)."""
import sys, struct
rom = open(sys.argv[1], "rb").read()
# Juego de caracteres de FireRed (parcial)
T = {0x00: " ", 0xAD: ".", 0xAE: "-", 0xB4: "'", 0xB5: "♂", 0xB6: "♀", 0x1B: "é", 0xF0: ":", 0xAC: "?", 0xAB: "!", 0xB8: ",", 0xB0: "…", 0x5C: "(", 0x5D: ")"}
for i in range(26): T[0xBB + i] = chr(65 + i); T[0xD5 + i] = chr(97 + i)
for i in range(10): T[0xA1 + i] = str(i)
E = {v: k for k, v in T.items()}
enc = lambda s: bytes(E[c] for c in s)
dec = lambda b: "".join(T.get(x, "?") for x in b.split(b"\xff")[0])
for nombre in ["BULBASAUR", "Bulbasaur"]:
    pos = rom.find(enc(nombre) + b"\xff")
    while pos != -1:
        # ¿la entrada anterior (11 bytes antes) es "??????????" (especie 0)?
        prev = rom[pos - 11:pos]
        print(f"{nombre} en 0x{pos:X}; entrada anterior: {dec(prev)!r}")
        base = pos - 11
        ptr = struct.pack("<I", 0x08000000 + base)
        refs = [hex(i) for i in range(0, len(rom) - 3, 4) if rom[i:i+4] == ptr]
        print(f"  punteros a 0x{base:X}: {len(refs)} -> {refs[:8]}")
        # contar entradas válidas
        n = 0
        while True:
            e = rom[base + 11 * n: base + 11 * (n + 1)]
            if 0xFF not in e or any(x not in T and x != 0xFF for x in e.split(b'\xff')[0]): break
            n += 1
        print(f"  entradas legibles consecutivas: {n}")
        for k in [1, 4, 25, 151, 251, 386, 387, 493, 494, 649, 650, 721, 722, 809, 810, 898, 899, 905, 906, 1000, 1100, 1200, 1300]:
            if k < n: print(f"   #{k:4}: {dec(rom[base+11*k: base+11*k+11])}")
        pos = rom.find(enc(nombre) + b"\xff", pos + 1)
