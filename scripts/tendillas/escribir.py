"""
tendillas/escribir.py
=====================
Mete la Plaza de las Tendillas (versión 2, hecha con el compositor) en la ROM de trabajo.

Qué escribe (para clase):
  1. Un TILESET COMPLETO propio: primario (tiles 0-639, paletas 0-6) y secundario (640-1023,
     paletas 7-12), generado por el compositor a partir del dibujo de la plaza.
  2. El DISEÑO del mapa (hueco 22 de la tabla de diseños 0xB6FB20).
  3. Sprites del mapa nuevos: la ESTATUA de Dialga en bronce (64x64, gráfico 0xFC) y una
     PALOMA (16x16, gráfico 0xFD) que pasea por la plaza.
  4. EVENTOS: vecinos (algunos pasean), palomas, relojero, Chalo, guardia, estatua, puertas,
     trigger del guardia y carteles; con sus scripts y textos.
  5. La CABECERA del mapa 3.0 (en la lista real de Unbound, banco 3 en 0xB6D550).

Todo va a una zona propia al final de la ROM que se borra y reescribe en cada ejecución.
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(AQUI.parent))
import textos as t  # noqa: E402
from insertar_pokemon import lz77_comprimir, lz77_descomprimir, TABLA_FRONTAL, TABLA_PAL_NORMAL  # noqa: E402
from cap0_sueno import Script, comprobar  # noqa: E402
import plaza as M  # noqa: E402

TABLA_LAYOUTS, HUECO_LAYOUT = 0xB6FB20, 22
BANCO3_UNBOUND, MAPA = 0xB6D550, 0
BANCO3_FR = 0x3522F4
CABECERA_MODELO = 0x350714
TABLA_OW, TABLA_PAL_OW = 0x8110E0, 0xEB994C
OW_ESTATUA, PAL_ESTATUA, ETIQ_ESTATUA = 252, 361, 0x1269
OW_PALOMA, PAL_PALOMA, ETIQ_PALOMA = 253, 362, 0x126A
FICHA_64, FICHA_16 = 0x3A4B04, 0x3A49C0      # fichas modelo: 64x64 y 16x16 con 9 fotogramas de andar
DIALGA = 536
VAR = 0x5011
FLAG_CHALO = 0x10
ZONA = (0x1FE2B10, 0x1FF8000)                 # zona propia al final de la ROM (la de la casa va después)
DY = M.DY

GFX = {"chalo": 194, "nino": 16, "abuelo": 33, "senora": 35, "turista": 56, "guardia": 60, "relojero": 71,
       "guitarrista": 25, "clienta": 27, "cliente": 52, "paseante1": 19, "paseante2": 29, "paseante3": 47}
CARA_ABAJO, MIRAR, PASEAR = 9, 1, 2

TEXTOS = {
    "estatua": "Una estatua de bronce sobre un alto{n}pedestal: un Pokémon legendario.{p}"
               "La placa dice: “Al guardián del{n}tiempo de Córdoba”.{p}......{p}"
               "Por un momento, parece que te mira.",
    "chalo": "¡{JUGADOR}! ¡Por fin! ¡Llevo aquí{n}desde las ocho!{p}"
             "¿Sabes qué día es hoy? ¡Nuestro{n}primer Pokémon!{p}"
             "Yo ya lo tengo decidido. Bueno,{n}más o menos. Bueno, no.{p}"
             "¡Venga, vamos al lago, que el{n}Profesor nos espera!",
    "chalo_se_va": "(Chalo se ha ido corriendo hacia{n}la puerta del laboratorio.)",
    "senora": "¡Estamos montando la Cruz de Mayo{n}en la calle de al lado!{p}"
              "Este año la vamos a llenar de{n}claveles.",
    "turista": "¿Ese reloj toca guitarra flamenca?{p}¡En mi ciudad solo hacen “dong”!",
    "abuelo": "Dicen que debajo de esta plaza hay{n}un lago.{p}"
              "Mi padre decía que lo oía correr{n}por las noches...",
    "nino": "¡Esa estatua es de un Pokémon{n}legendario!{p}"
            "Mi abuela dice que vigila el reloj{n}para que nunca se pare.",
    "relojero": "Buenos días. ¿Te gusta el reloj?{p}"
                "Llevo media vida cuidándolo. Cada{n}pieza, cada engranaje...{p}"
                "El tiempo es lo más valioso que{n}tenemos. Y lo más cruel.{p}"
                "Bah, no me hagas caso. ¡Que tengas{n}un buen día!",
    "guitarrista": "(Rasguea una bulería.){p}"
                   "Toco aquí todas las mañanas. Cuando{n}el reloj da la hora, me callo...{p}"
                   "...porque ese sí que toca bien.",
    "clienta": "Un café con leche y una tostada con{n}aceite. ¡El mejor desayuno{l}del mundo!",
    "cliente": "En mayo Córdoba huele a azahar.{p}Y a churros. Sobre todo a churros.",
    "paseante1": "Voy a ver los Patios. ¡Este año hay{n}colas de una hora!",
    "paseante2": "Qué raro... Dicen que el reloj se{n}atrasa un segundo cada día.{p}"
                 "El relojero no quiere ni hablar{n}del tema.",
    "paseante3": "¡Cuidado con las palomas, que se{n}comen hasta los tejeringos!",
    "paloma": "¡Currucucú! ¡Currucucú!",
    "guardia": "¡Eh, eh! Sin Pokémon no se sale del{n}centro, ¿eh?{p}"
               "Que hay mucho Pokémon salvaje por{n}ahí fuera.",
    "guardia_hablar": "La calle está cortada. Órdenes{n}del Ayuntamiento.",
    "reloj": "El reloj de las Tendillas.{p}A cada hora no suena una campana:{n}suena una guitarra flamenca.",
    "puerta_reloj": "Una puertecita en el edificio del{n}reloj. Está cerrada con llave.",
    "lab": "Una puerta de madera antigua con{n}una placa:{p}“Laboratorio de Investigación{n}Pokémon. Prof. Acisclo”.",
    "lab_cerrado": "(El laboratorio todavía no está{n}construido. ¡Es lo siguiente!)",
    "quiosco": "Quiosco de prensa: “¡Especial{n}Cruces de Mayo!”.",
    "flores": "Puesto de flores: claveles rojos{n}para la Cruz de Mayo.",
    "chorro": "Una fuentecilla. El agua salta y{n}salpica. ¡Qué fresquito!",
}

# ---- paloma 16x16 (dibujada a mano: 1 contorno, 2-4 grises, 5-6 cuello tornasolado, 7 patas, 8 ojo) ----
PAL_PALOMA_RGB = [(0, 0, 0), (40, 40, 56), (152, 160, 176), (200, 204, 216), (104, 112, 128), (72, 152, 120),
                  (136, 96, 168), (232, 128, 64), (24, 24, 24)] + [(0, 0, 0)] * 7
PALOMA_LADO = ["................", "................", "................", "................",
               "................", ".....111........", "....12221.......", "...7182221......",
               "....1556211111..", "....1566222441..", ".....162224441..", ".....12223444411",
               "......12233441..", ".......111111...", "........7..7....", "................"]
PALOMA_LADO2 = PALOMA_LADO[:14] + [".......7....7...", "................"]
PALOMA_FRENTE = ["................", "................", "................", "................",
                 "................", "......1111......", ".....122221.....", ".....182281.....",
                 ".....127721.....", "....15566551....", "...1422222241...", "...1422332241...",
                 "....14233241....", ".....122221.....", "......1111......", "......7..7......"]
PALOMA_FRENTE2 = PALOMA_FRENTE[:15] + [".....7....7....."]
PALOMA_ESPALDA = ["................", "................", "................", "................",
                  "................", "......1111......", ".....122221.....", ".....122221.....",
                  ".....155551.....", "....14566541....", "...1444224441...", "...1444224441...",
                  "....14422441....", ".....144441.....", "......1111......", "......7..7......"]
PALOMA_ESPALDA2 = PALOMA_ESPALDA[:15] + [".....7....7....."]


def P(rom, o):
    return struct.unpack("<I", rom[o:o + 4])[0]


def ptr(o):
    return struct.pack("<I", 0x08000000 + o)


def bgr(c):
    r, g, b = c
    return struct.pack("<H", (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10))


def tiles_16(dibujo):
    """16x16 en orden de sprite: 4 tiles de 8x8 (arriba-izq, arriba-der, abajo-izq, abajo-der)."""
    v = [[0 if ch == "." else int(ch) for ch in fila] for fila in dibujo]
    out = b""
    for ty in range(2):
        for tx in range(2):
            for y in range(8):
                fila = v[ty * 8 + y][tx * 8:tx * 8 + 8]
                out += bytes(fila[i] | (fila[i + 1] << 4) for i in range(0, 8, 2))
    return out


def scripts_y_eventos():
    s = Script()

    def mensaje(etq, callstd=6):
        s.b(0x0F, 0x00); s.ptr(etq); s.b(0x09, callstd)

    def hablar(etq):
        s.etq(f"sc_{etq}"); s.b(0x6A, 0x5A); mensaje(etq); s.b(0x6C); s.end()

    for etq in ("senora", "turista", "abuelo", "nino", "relojero", "guardia_hablar", "guitarrista",
                "clienta", "cliente", "paseante1", "paseante2", "paseante3", "paloma"):
        hablar(etq)
    s.etq("sc_estatua"); s.b(0x69); mensaje("estatua"); s.b(0x6B); s.end()

    s.etq("sc_chalo"); s.b(0x6A, 0x5A); mensaje("chalo")
    s.fadescreen(1); s.removeobject(2); s.b(0x29); s.h(FLAG_CHALO)
    s.delay(20); s.fadescreen(0); mensaje("chalo_se_va")
    s.setvar(VAR, 4); s.b(0x6C); s.end()

    s.etq("sc_guardia"); s.b(0x69); mensaje("guardia")
    s.b(0x4F); s.h(0xFF); s.ptr("mov_atras"); s.b(0x51); s.h(0); s.b(0x6B); s.end()
    s.etq("mov_atras"); s.b(0x10, 0xFE)

    s.etq("sc_puerta_reloj"); mensaje("reloj", 3); mensaje("puerta_reloj", 3); s.end()
    s.etq("sc_lab"); mensaje("lab", 3); mensaje("lab_cerrado", 3); s.end()
    s.etq("sc_quiosco"); mensaje("quiosco", 3); s.end()
    s.etq("sc_flores"); mensaje("flores", 3); s.end()
    s.etq("sc_chorro"); mensaje("chorro", 3); s.end()

    s.etq("sc_al_entrar"); s.compare(VAR, 4); s.goto_if(4, "sc_ocultar_chalo"); s.end()
    s.etq("sc_ocultar_chalo"); s.b(0x29); s.h(FLAG_CHALO); s.end()

    # ---- eventos (coordenadas del plano + DY) ----
    def persona(n, gfx, x, y, mov, etq, flag=0, rango=0):
        s.b(n, gfx, 0, 0); s.h(x); s.h(y + DY); s.b(3, mov, rango, 0); s.h(0); s.h(0); s.ptr(etq); s.h(flag); s.h(0)

    ex, ey = M.ESTATUA
    personas = [
        (OW_ESTATUA, ex, ey, CARA_ABAJO, "sc_estatua", 0, 0),
        (GFX["chalo"], M.EJE - 6, 18, MIRAR, "sc_chalo", FLAG_CHALO, 0),
        (GFX["guardia"], M.EJE, 5, CARA_ABAJO, "sc_guardia_hablar", 0, 0),
        (GFX["relojero"], 4, 20, CARA_ABAJO, "sc_relojero", 0, 0),
        (GFX["turista"], 5, 23, MIRAR, "sc_turista", 0, 0),
        (GFX["nino"], M.EJE + 6, 18, MIRAR, "sc_nino", 0, 0),
        (GFX["abuelo"], M.EJE - 6, 24, CARA_ABAJO, "sc_abuelo", 0, 0),
        (GFX["senora"], 8, 14, MIRAR, "sc_senora", 0, 0),
        (GFX["guitarrista"], 16, 12, CARA_ABAJO, "sc_guitarrista", 0, 0),
        (GFX["clienta"], 25, 14, CARA_ABAJO, "sc_clienta", 0, 0),
        (GFX["cliente"], 21, 12, CARA_ABAJO, "sc_cliente", 0, 0),
        (GFX["paseante1"], 9, 25, PASEAR, "sc_paseante1", 0, 0x32),
        (GFX["paseante2"], 27, 25, PASEAR, "sc_paseante2", 0, 0x32),
        (GFX["paseante3"], M.EJE, 24, PASEAR, "sc_paseante3", 0, 0x21),
        (OW_PALOMA, 15, 12, PASEAR, "sc_paloma", 0, 0x22),
        (OW_PALOMA, 22, 13, PASEAR, "sc_paloma", 0, 0x22),
        (OW_PALOMA, 15, 25, PASEAR, "sc_paloma", 0, 0x21),
        (OW_PALOMA, 31, 23, PASEAR, "sc_paloma", 0, 0x12),
    ]
    s.alinear(4); s.etq("personas")
    for i, (g, x, y, mov, etq, flag, rango) in enumerate(personas, start=1):
        persona(i, g, x, y, mov, etq, flag, rango)

    s.alinear(4); s.etq("warps")
    px, py = M.PUERTA_CASA
    s.h(px); s.h(py + DY); s.b(0, 1, 0, 4)

    s.alinear(4); s.etq("triggers")
    n_triggers = 0
    for valor in (3, 4):                     # (un trigger con variable 0 sería de clima)
        for x in M.CALLE_NORTE:
            s.h(x); s.h(M.FILA_GUARDIA + DY); s.b(3, 0); s.h(VAR); s.h(valor); s.h(0); s.ptr("sc_guardia")
            n_triggers += 1

    s.alinear(4); s.etq("carteles")
    carteles = [(M.PUERTA_RELOJ, "sc_puerta_reloj"), (M.PUERTA_LAB, "sc_lab"),
                ((ex - 1, ey + 6), "sc_estatua"), ((ex, ey + 6), "sc_estatua"), ((ex + 1, ey + 6), "sc_estatua"),
                ((M.EJE + 8, 13), "sc_quiosco"), ((M.EJE - 8, 13), "sc_flores")]
    carteles += [((x, y), "sc_chorro") for x, y in M.CHORROS_IZQ + M.CHORROS_DER]
    for (x, y), etq in carteles:
        s.h(x); s.h(y + DY); s.b(0, 0, 0, 0); s.ptr(etq)

    s.alinear(4); s.etq("eventos")
    s.b(len(personas), 1, n_triggers, len(carteles))
    s.ptr("personas"); s.ptr("warps"); s.ptr("triggers"); s.ptr("carteles")
    s.alinear(4); s.etq("mapscripts"); s.b(3); s.ptr("sc_al_entrar"); s.b(0)
    s.alinear(4); s.etq("conexiones"); s.w(0); s.w(0)
    return s


def main():
    for v in TEXTOS.values():
        comprobar(v, pagina=False)
    L = M.construir()
    conv = L.convertir()
    print("Compositor:", conv.informe())
    assert len(conv.tiles) <= 1024 and len(conv.bloques) <= 1024

    rom = bytearray(t.ROM.read_bytes())
    original = bytes(rom)
    ini, fin = ZONA
    rom[ini:fin] = bytes([0xFF] * (fin - ini))
    cursor = [ini]

    def colocar(datos, alinear=4):
        o = (cursor[0] + alinear - 1) // alinear * alinear
        assert o + len(datos) <= fin, "la zona de la plaza se ha llenado"
        rom[o:o + len(datos)] = datos
        cursor[0] = o + len(datos) + 1
        return o

    # ---- 1. tilesets (primario + secundario) ----
    pal = [p + [(0, 0, 0)] * (15 - len(p)) for p in conv.paletas]
    pal_bytes = []
    for i in range(16):
        cols = [(0, 0, 0)] + [(r << 3, g << 3, b << 3) for (r, g, b) in pal[i]] if i < len(pal) else [(0, 0, 0)] * 16
        pal_bytes.append(b"".join(bgr(c) for c in cols))
    bloque_bytes = [struct.pack("<8H", *ab, *ar) for ab, ar, _ in conv.bloques]
    attr_bytes = [struct.pack("<I", a) for _, _, a in conv.bloques]
    tiles = conv.tiles + [bytes(32)] * max(0, 641 - len(conv.tiles))

    def escribir_ts(es_secundario, rango_tiles, rango_bloques, paletas):
        o_t = colocar(lz77_comprimir(b"".join(tiles[rango_tiles[0]:rango_tiles[1]])))
        o_p = colocar(b"".join(pal_bytes[i] if i in paletas else bytes(32) for i in range(16)))
        bl = bloque_bytes[rango_bloques[0]:rango_bloques[1]] or [bytes(16)]
        at = attr_bytes[rango_bloques[0]:rango_bloques[1]] or [bytes(4)]
        if not es_secundario:
            bl = bl + [bytes(16)] * (640 - len(bl)); at = at + [bytes(4)] * (640 - len(at))
        o_m = colocar(b"".join(bl)); o_a = colocar(b"".join(at))
        return colocar(bytes([1, 1 if es_secundario else 0, 0, 0]) + ptr(o_t) + ptr(o_p) + ptr(o_m)
                       + struct.pack("<I", 0) + ptr(o_a))           # sin animaciones (callback 0)

    o_prim = escribir_ts(False, (0, 640), (0, 640), range(0, 7))
    o_sec = escribir_ts(True, (640, len(tiles)), (640, len(conv.bloques)), range(7, 13))

    # ---- 2. diseño ----
    celdas = conv.celdas
    o_celdas = colocar(b"".join(struct.pack("<H", c) for c in celdas))
    borde = (celdas[0] & 0x3FF) | 0x0400                              # tejas: fuera del mapa se ven tejados
    o_borde = colocar(struct.pack("<4H", *([borde] * 4)))
    o_layout = colocar(struct.pack("<II", M.ANCHO, M.ALTO + DY) + ptr(o_borde) + ptr(o_celdas)
                       + ptr(o_prim) + ptr(o_sec) + bytes([2, 2, 0, 0]))
    rom[TABLA_LAYOUTS + 4 * (HUECO_LAYOUT - 1):TABLA_LAYOUTS + 4 * HUECO_LAYOUT] = ptr(o_layout)

    # ---- 3. sprites del mapa: estatua y paloma ----
    Pq = lambda o: P(rom, o) - 0x08000000

    def registrar(hueco_ow, hueco_pal, etiqueta, ficha_modelo, imagenes, paleta, tam):
        o_pal = colocar(b"".join(bgr(c) for c in paleta))
        o_imgs = [colocar(img) for img in imagenes]
        o_tabla = colocar(b"".join(ptr(o) + struct.pack("<HH", tam, 0) for o in o_imgs))
        ficha = bytearray(rom[ficha_modelo:ficha_modelo + 0x24])
        ficha[2:4] = struct.pack("<H", etiqueta)
        ficha[0x1C:0x20] = ptr(o_tabla)
        o_ficha = colocar(bytes(ficha))
        rom[TABLA_OW + 4 * hueco_ow:TABLA_OW + 4 * hueco_ow + 4] = ptr(o_ficha)
        e = TABLA_PAL_OW + 8 * hueco_pal
        rom[e:e + 8] = ptr(o_pal) + struct.pack("<HH", etiqueta, 0)

    tiles_dialga = lz77_descomprimir(rom, Pq(TABLA_FRONTAL + 8 * DIALGA))
    pal_d = lz77_descomprimir(rom, Pq(TABLA_PAL_NORMAL + 8 * DIALGA))[:32]
    cols = [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in struct.unpack("<16H", pal_d)]
    import arte
    registrar(OW_ESTATUA, PAL_ESTATUA, ETIQ_ESTATUA, FICHA_64, [tiles_dialga] * 9, arte.bronce(cols), 0x800)
    frames = [PALOMA_FRENTE, PALOMA_ESPALDA, PALOMA_LADO, PALOMA_FRENTE, PALOMA_FRENTE2,
              PALOMA_ESPALDA, PALOMA_ESPALDA2, PALOMA_LADO, PALOMA_LADO2]
    registrar(OW_PALOMA, PAL_PALOMA, ETIQ_PALOMA, FICHA_16, [tiles_16(f) for f in frames], PAL_PALOMA_RGB, 0x80)

    # ---- 4. textos, scripts y eventos ----
    dirs = {k: colocar(t.codificar(v), alinear=1) for k, v in TEXTOS.items()}
    s = scripts_y_eventos()
    base = colocar(bytes(s.tam()))
    codigo = s.ensamblar(base, dirs)
    rom[base:base + len(codigo)] = codigo
    etq = s.direcciones(base)

    # ---- 5. cabecera ----
    cab = bytearray(original[CABECERA_MODELO:CABECERA_MODELO + 0x1C])
    cab[0:4] = ptr(o_layout); cab[4:8] = ptr(etq["eventos"]); cab[8:12] = ptr(etq["mapscripts"])
    cab[12:16] = ptr(etq["conexiones"])
    cab[0x12:0x14] = struct.pack("<H", HUECO_LAYOUT)
    o_cab = P(original, BANCO3_UNBOUND + 4 * MAPA) - 0x08000000
    rom[o_cab:o_cab + 0x1C] = cab
    rom[BANCO3_FR:BANCO3_FR + 4] = bytes([0xF7] * 4)

    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-tendillas_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(rom)
    print(f"Zona de la plaza: 0x{ini:X}-0x{cursor[0]:X} ({(cursor[0] - ini) // 1024} KB de {(fin - ini) // 1024} KB)")
    print(f"Mapa 3.0: {M.ANCHO}x{M.ALTO + DY}, eventos 0x{etq['eventos']:X}, {len(TEXTOS)} textos")


if __name__ == "__main__":
    main()
