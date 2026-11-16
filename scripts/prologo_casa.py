"""
prologo_casa.py
===============
Prólogo, escena 1 (HISTORIA.md): el despertar en el cuarto y la madre en la planta baja.

Mapas: los interiores de la casa del protagonista de FireRed, que siguen en la ROM
(banco 4): 4.1 = cuarto, 4.0 = planta baja. Unbound los había reutilizado para su
historia; aquí se les ponen EVENTOS y SCRIPTS NUEVOS, escritos desde cero:

  4.1 cuarto      - al llegar (var 0x5011 == 1): "......... ...Qué sueño más raro..."
                    y el grito de Mamá desde abajo. Carteles: póster, ventana, PC,
                    libro, consola, tele. Escalera a la planta baja.
  4.0 planta baja - al llegar (var 0x5011 == 2): escena de Mamá (tejeringos,
                    zapatillas). Mamá en la mesa. Tele y cocina. La puerta sale a la
                    calle de la casa, junto a la Plaza de las Tendillas (mapa 3.0).

La variable 0x5011 hace de "en qué punto del prólogo vamos":
  0 = intro (sueño) · 1 = acabas de despertar · 2 = has bajado · 3 = puedes salir.

CONCEPTOS (para clase)
----------------------
* EVENTOS de un mapa: personas, warps (puertas y escaleras), triggers (casillas
  que lanzan un script al pisarlas) y carteles (objetos que se pueden mirar).
* SCRIPTS del mapa: lista de (tipo, puntero). El tipo 2 es una "tabla de
  fotogramas": en cuanto el mapa está cargado, si una variable vale X, lanza un script.
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402
from cap0_sueno import Script, comprobar  # noqa: E402

ZONA = (0x1FF8000, 0x1FFFF00)                 # zona propia al final de la ROM (la de la plaza va antes)
CUARTO, PLANTA = 0x350D6C, 0x350D50          # cabeceras de los mapas 4.1 y 4.0
VAR = 0x5011
ASM_NOMBRE_HABLANTE = 0x09EACEA9              # Unbound: muestra el nombre de quien habla
GFX_MAMA = 88
FLAG_CORRER = 0x82F                           # zapatillas de deporte (FireRed)
CAMINAR_ARRIBA, FIN_MOV = 0x11, 0xFE

TEXTOS = {
    "nombre_mama": "Mamá",
    "despertar": ".........{p}...Qué sueño más raro...",
    "grito": "¡{JUGADOR}!{n}¡Que son las diez y media!{p}"
             "¡Ojú, qué criatura!{n}¡Ni el día de su cumpleaños se{l}levanta temprano!",
    "mama_1": "¡Mira quién baja! ¡La persona más{n}dormilona de toda Córdoba!{p}"
              "Anda, ven aquí, que te dé un beso.{n}¡Feliz cumpleaños!{p}"
              "He ido a por tejeringos a la{n}plaza...{p}...pero ya están fríos. Eso te pasa{n}por dormir tanto.{p}"
              "El Profesor Acisclo ha llamado tres{n}veces. ¡Tres! Ese hombre no tiene{l}paciencia ninguna.{p}"
              "Y Chalo ha salido de su casa a las{n}ocho. Lo he visto desde el balcón,{l}dando saltitos como un saltamontes.{p}"
              "Toma, mi regalo: unas zapatillas{n}nuevas. Para que corras detrás de{l}los Pokémon y no del autobús.",
    "zapatillas": "{JUGADOR} recibe las{n}ZAPATILLAS DE DEPORTE.{p}(Mantén pulsado B para correr.)",
    "mama_2": "¡Y llévate una chaqueta, que en{n}mayo por la mañana refresca!{p}"
              "...Bueno, haz lo que quieras,{n}que ya eres mayor.{p}¡Ea, a la calle!",
    "mama_despues": "¿Todavía aquí? ¡Que el Profesor{n}te está esperando!",
    "poster": "Un cartel de la Fiesta de los{n}Patios: macetas azules en paredes{l}blancas.",
    "ventana": "Por la ventana se ve el reloj de{n}las Tendillas.{p}Ya han dado las diez y media.",
    "pc": "Es tu PC. De fondo de pantalla,{n}el Puente Romano al atardecer.",
    "libro": "Un libro: “Leyendas de Córdoba”.{p}Hay una página doblada:{n}“El lago bajo la plaza”.",
    "consola": "Tu videoconsola. Hoy no hay tiempo{n}para jugar.",
    "tele_cuarto": "La tele está apagada.",
    "tele_planta": "En la tele: “La Fiesta de los{n}Patios bate este año récord{l}de visitantes”.",
    "cocina": "Huele a tejeringos...{n}...ya fríos.",
    "puerta": "(La plaza de las Tendillas todavía{n}no está construida.{p}¡Es lo siguiente!)",
}


def habla_mama(s, etq, callstd=6):
    s.b(0x0F, 0x00); s.ptr("nombre_mama"); s.callasm(ASM_NOMBRE_HABLANTE)
    s.b(0x0F, 0x00); s.ptr(etq); s.b(0x09, callstd)
    s.b(0xC1, 0x01, 0x0B)       # oculta el recuadro del nombre (Unbound reutiliza la ventana de monedas)


def mensaje(s, etq, callstd=6):
    s.b(0x0F, 0x00); s.ptr(etq); s.b(0x09, callstd)


def construir():
    s = Script()
    # ---------------- scripts ----------------
    s.etq("sc_despertar")
    s.b(0x69); s.delay(30)                                     # lockall, un silencio
    mensaje(s, "despertar")
    habla_mama(s, "grito")
    s.setvar(VAR, 2); s.b(0x6B); s.end()                       # releaseall

    s.etq("sc_mama_escena")
    s.b(0x69); s.delay(16)
    habla_mama(s, "mama_1")
    s.b(0x29); s.h(FLAG_CORRER)                                # setflag zapatillas
    s.playse(0x01); mensaje(s, "zapatillas")
    habla_mama(s, "mama_2")
    s.setvar(VAR, 3); s.b(0x6B); s.end()

    s.etq("sc_mama_hablar")
    s.b(0x6A, 0x5A)                                            # lock, faceplayer
    habla_mama(s, "mama_despues")
    s.b(0x6C); s.end()                                         # release

    s.etq("sc_puerta")
    s.b(0x69); mensaje(s, "puerta")
    s.b(0x4F); s.h(0xFF); s.ptr("mov_arriba")                  # applymovement jugador
    s.b(0x51); s.h(0)                                          # waitmovement
    s.b(0x6B); s.end()
    s.etq("mov_arriba"); s.b(CAMINAR_ARRIBA, FIN_MOV)

    for etq in ("poster", "ventana", "pc", "libro", "consola", "tele_cuarto", "tele_planta", "cocina"):
        s.etq(f"sc_{etq}"); mensaje(s, etq, callstd=3); s.end()   # callstd 3 = cartel

    # ---------------- tablas de scripts de los mapas ----------------
    s.alinear(4); s.etq("tabla_cuarto"); s.h(VAR); s.h(1); s.ptr("sc_despertar"); s.h(0)
    s.alinear(4); s.etq("mapscripts_cuarto"); s.b(2); s.ptr("tabla_cuarto"); s.b(0)
    s.alinear(4); s.etq("tabla_planta"); s.h(VAR); s.h(2); s.ptr("sc_mama_escena"); s.h(0)
    s.alinear(4); s.etq("mapscripts_planta"); s.b(2); s.ptr("tabla_planta"); s.b(0)

    # ---------------- eventos ----------------
    def warp(x, y, id_, mapa, banco):
        s.h(x); s.h(y); s.b(3, id_, mapa, banco)

    def cartel(x, y, etq):
        s.h(x); s.h(y); s.b(0, 0, 0, 0); s.ptr(etq)

    def trigger(x, y, valor, etq):
        s.h(x); s.h(y); s.b(3, 0); s.h(VAR); s.h(valor); s.h(0); s.ptr(etq)

    # cuarto 4.1
    s.alinear(4); s.etq("warps_cuarto"); warp(2, 4, 0, 0, 4)                 # escalera -> planta baja, warp 0
    s.alinear(4); s.etq("carteles_cuarto")
    cartel(3, 3, "sc_poster"); cartel(4, 3, "sc_ventana"); cartel(5, 4, "sc_pc")
    cartel(6, 4, "sc_libro"); cartel(7, 4, "sc_consola"); cartel(8, 4, "sc_tele_cuarto")
    s.alinear(4); s.etq("eventos_cuarto"); s.b(0, 1, 0, 6); s.w(0); s.ptr("warps_cuarto"); s.w(0); s.ptr("carteles_cuarto")

    # planta baja 4.0
    s.alinear(4); s.etq("personas_planta")
    s.b(1, GFX_MAMA, 0, 0); s.h(7); s.h(6); s.b(3, 9, 0, 0); s.h(0); s.h(0); s.ptr("sc_mama_hablar"); s.h(0); s.h(0)
    s.alinear(4); s.etq("warps_planta")
    warp(1, 2, 0, 1, 4)                                        # escalera -> cuarto, warp 0
    for x in (7, 8, 9):
        warp(x, 9, 0, 0, 3)                                    # puerta -> calle de la casa (mapa 3.0, warp 0)
    s.alinear(4); s.etq("carteles_planta")
    for x in (4, 5):
        for y in (3, 4):                                       # la tele ocupa 2x2: se puede mirar de lado o de frente
            cartel(x, y, "sc_tele_planta")
    cartel(7, 2, "sc_cocina"); cartel(8, 2, "sc_cocina")
    s.alinear(4); s.etq("eventos_planta"); s.b(1, 4, 0, 6)
    s.ptr("personas_planta"); s.ptr("warps_planta"); s.w(0); s.ptr("carteles_planta")
    return s


def main():
    for k, v in TEXTOS.items():
        if k != "nombre_mama":
            comprobar(v, pagina=False)
    s = construir()
    rom = bytearray(t.ROM.read_bytes())
    trabajo = bytearray(rom); dirs = {}
    # Zona propia al final de la ROM: se borra y se reescribe en cada ejecución (no gasta espacio)
    ini, fin = ZONA
    trabajo[ini:fin] = bytes([0xFF] * (fin - ini))
    cursor = [ini]

    def colocar(d, alinear=1):
        o = (cursor[0] + alinear - 1) // alinear * alinear
        assert o + len(d) <= fin, "la zona de la casa se ha llenado"
        trabajo[o:o + len(d)] = d
        cursor[0] = o + len(d) + 1
        return o

    for k, v in TEXTOS.items():
        dirs[k] = colocar(t.codificar(v))
    base = colocar(bytes(s.tam()), alinear=4)
    codigo = s.ensamblar(base, dirs)
    trabajo[base:base + len(codigo)] = codigo
    etq = s.direcciones(base)
    for cab, ev, ms in ((CUARTO, "eventos_cuarto", "mapscripts_cuarto"), (PLANTA, "eventos_planta", "mapscripts_planta")):
        trabajo[cab + 4:cab + 8] = struct.pack("<I", 0x08000000 + etq[ev])
        trabajo[cab + 8:cab + 12] = struct.pack("<I", 0x08000000 + etq[ms])
    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-casa_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(trabajo)
    print(f"Casa: {len(codigo)} bytes de scripts y eventos en 0x{base:X}; {len(TEXTOS)} textos.")
    print("Cabeceras 4.1 (cuarto) y 4.0 (planta baja) apuntan ahora a los eventos y scripts nuevos.")


if __name__ == "__main__":
    main()
