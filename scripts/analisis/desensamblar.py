"""Desensambla código THUMB de la ROM (solo lectura). Uso: desensamblar.py 0xDIRECCION [n_bytes]"""
import sys, struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
rom = open(sys.argv[3] if len(sys.argv) > 3 else 'MiHack.gba', 'rb').read()
off = int(sys.argv[1], 16) & ~1
n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
for ins in md.disasm(rom[off:off + n], 0x08000000 + off):
    extra = ''
    if ins.mnemonic == 'ldr' and 'pc' in ins.op_str:
        # literal pool
        imm = int(ins.op_str.split('#')[-1].rstrip(']'), 16)
        lit = ((ins.address + 4) & ~3) + imm
        val = struct.unpack('<I', rom[lit - 0x08000000:lit - 0x08000000 + 4])[0]
        extra = f'   ; =0x{val:08X}'
    print(f'{ins.address:08X}: {ins.mnemonic:6} {ins.op_str}{extra}')
