"""Lee un estado de mGBA (.ssN, PNG con el estado comprimido) y devuelve sus memorias."""
import struct, zlib
def leer(ruta):
    d = open(ruta, 'rb').read(); p = 8; estado = None
    while p < len(d):
        n = struct.unpack('>I', d[p:p+4])[0]; tipo = d[p+4:p+8]; datos = d[p+8:p+8+n]; p += 12 + n
        if tipo == b'gbAs': estado = zlib.decompress(datos)
    assert estado and len(estado) >= 0x61000, 'no se encontró el estado'
    return {'io': estado[0x400:0x800], 'pal': estado[0x800:0xC00], 'oam': estado[0xC00:0x1000],
            'vram': estado[0x1000:0x19000], 'iwram': estado[0x19000:0x21000], 'ewram': estado[0x21000:0x61000]}
