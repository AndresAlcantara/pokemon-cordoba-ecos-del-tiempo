"""Descompresor LZ77 de la BIOS de GBA (formato 0x10). Solo lectura."""
def lz77(rom, off):
    assert rom[off] == 0x10, f"no es LZ77 en 0x{off:X}"
    size = int.from_bytes(rom[off+1:off+4], "little"); out = bytearray(); p = off + 4
    while len(out) < size:
        flags = rom[p]; p += 1
        for bit in range(8):
            if len(out) >= size: break
            if flags & (0x80 >> bit):
                b1, b2 = rom[p], rom[p+1]; p += 2
                n = (b1 >> 4) + 3; d = ((b1 & 0xF) << 8 | b2) + 1
                for _ in range(n): out.append(out[-d])
            else:
                out.append(rom[p]); p += 1
    return bytes(out), p - off
