"""Decodificador sencillo de scripts de eventos de FireRed/CFRU (solo lectura).
Uso: python script_dec.py 0xDIRECCION [n_bytes]"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import textos as t  # noqa: E402

# código: (nombre, formato de argumentos)  b=byte h=halfword w=word p=puntero
CMDS = {
    0x00: ("nop", ""), 0x01: ("nop1", ""), 0x02: ("end", ""), 0x03: ("return", ""),
    0x04: ("call", "p"), 0x05: ("goto", "p"), 0x06: ("goto_if", "bp"), 0x07: ("call_if", "bp"),
    0x08: ("gotostd", "b"), 0x09: ("callstd", "b"), 0x0F: ("loadpointer", "bp"), 0x11: ("writebytetooffset", "bp"),
    0x16: ("setvar", "hh"), 0x17: ("addvar", "hh"), 0x18: ("subvar", "hh"), 0x19: ("copyvar", "hh"),
    0x1A: ("copyvarifnotzero", "hh"), 0x21: ("compare", "hh"), 0x22: ("compare_vars", "hh"),
    0x23: ("callasm", "p"), 0x25: ("special", "h"), 0x26: ("special2", "hh"), 0x27: ("waitstate", ""),
    0x28: ("delay", "h"), 0x29: ("setflag", "h"), 0x2A: ("clearflag", "h"), 0x2B: ("checkflag", "h"),
    0x2F: ("playse", "h"), 0x30: ("waitse", ""), 0x31: ("playfanfare", "h"), 0x32: ("waitfanfare", ""),
    0x33: ("playbgm", "hb"), 0x34: ("savebgm", "h"), 0x35: ("fadedefaultbgm", ""), 0x36: ("fadenewbgm", "h"),
    0x37: ("fadeoutbgm", "b"), 0x38: ("fadeinbgm", "b"), 0x39: ("warp", "bbbhh"), 0x3A: ("warpsilent", "bbbhh"),
    0x3B: ("warpdoor", "bbbhh"), 0x3C: ("warphole", "bb"), 0x3D: ("warpteleport", "bbbhh"),
    0x3F: ("setwarp", "bbbhh"), 0x44: ("additem", "hh"), 0x4F: ("applymovement", "hp"), 0x51: ("waitmovement", "h"),
    0x53: ("removeobject", "h"), 0x55: ("addobject", "h"), 0x5A: ("faceplayer", ""), 0x5C: ("trainerbattle", ""),
    0x63: ("setobjectxyperm", "hhh"), 0x65: ("setobjectmovementtype", "hb"), 0x66: ("waitmessage", ""),
    0x67: ("message", "p"), 0x68: ("closemessage", ""), 0x69: ("lockall", ""), 0x6A: ("lock", ""),
    0x6B: ("releaseall", ""), 0x6C: ("release", ""), 0x6D: ("waitbuttonpress", ""), 0x6E: ("yesnobox", "bb"),
    0x6F: ("multichoice", "bbbb"), 0x75: ("showmonpic", "hbb"), 0x76: ("hidemonpic", ""),
    0x97: ("fadescreen", "b"), 0x98: ("fadescreenspeed", "bb"), 0x9C: ("dofieldeffect", "h"),
    0xA1: ("playmoncry", "hh"), 0xC5: ("waitmoncry", ""), 0x80: ("bufferspeciesname?", ""),
}


def decodificar(rom, off, n):
    fin = off + n
    while off < fin:
        c = rom[off]
        nombre, fmt = CMDS.get(c, (f"?? 0x{c:02X}", ""))
        p = off + 1; args = []
        for f in fmt:
            if f == "b": args.append(f"{rom[p]}"); p += 1
            elif f == "h": args.append(f"0x{struct.unpack('<H', rom[p:p+2])[0]:X}"); p += 2
            elif f in "wp":
                v = struct.unpack("<I", rom[p:p+4])[0]; p += 4
                if f == "p" and nombre in ("loadpointer", "message") and 0x08000000 <= v < 0x0A000000:
                    args.append(f"0x{v-0x08000000:X} «{t.decodificar(rom, v-0x08000000)[:60]}»")
                else:
                    args.append(f"0x{v:X}")
        print(f"0x{off:X}: {nombre} {' '.join(args)}")
        off = p
        if nombre in ("end", "return", "goto") or nombre.startswith("??"):
            if nombre.startswith("??"):
                break


if __name__ == "__main__":
    rom = t.ROM.read_bytes()
    decodificar(rom, int(sys.argv[1], 16), int(sys.argv[2]) if len(sys.argv) > 2 else 120)
