"""
cap0_sueno.py
=============
Intro NUEVA del juego, escrita desde cero: el sueño (HISTORIA.md, sección 4.2).

  1. Páginas de texto a pantalla completa (blanco sobre negro): el agua, el reflejo.
  2. Elección de CHICO / CHICA (primer paso del editor de personaje de Unbound;
     se salta piel, pelo y ropa).
  3. La voz sin nombre... pantalla de NOMBRE... la voz continúa.
  4. Destello blanco y el grito de Dialga.
  5. Salto a la habitación (banco 4, mapa 10), como hace Unbound cuando se salta
     su apertura: sin test de dificultad ni historia de Borrius.

El script se escribe en espacio libre y el mapa de la intro pasa a apuntar a él
(puntero en 0x1E6865A). El script antiguo de Unbound se queda en la ROM, sin usar.

CONCEPTOS (para clase): un script es una lista de órdenes. Aquí cada orden se
escribe con una función de Python que devuelve sus bytes; las ETIQUETAS (nombres
de puntos del script) se resuelven al final, cuando ya se sabe en qué dirección
de la ROM va cada orden.
"""
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

PUNTERO_SCRIPT_INTRO = 0x1E6865A          # la tabla del mapa de la intro apunta aquí al script que se ejecuta
DIALGA = 536
MAX_LINEA = 35

# ---- rutinas del motor de Unbound que se reutilizan (direcciones ROM + 0x08000000) ----
ASM_PAGINA = 0x09EAA7C5           # muestra una página de texto a pantalla completa
ASM_INICIO_A, ASM_INICIO_B = 0x09EC78F5, 0x09EC7C39
ASM_EDITOR_PREP1, ASM_EDITOR_PREP2 = 0x09EB5265, 0x09EB52D5
SUB_EDITOR_RESET = 0x09E686E1     # subrutina original: prepara el personaje grande
ASM_EDITOR_PASO = 0x09EB53B9      # un paso del editor (0x8001 = qué paso; 0 = personaje)
SUB_CAMBIA_A_CHICO, SUB_CAMBIA_A_CHICA = 0x09E68EE1, 0x09E68EE7
ASM_FIN_EDITOR = (0x09EB52BD, 0x09EB54F1, 0x09EBE641)   # guardan el aspecto elegido
ASM_NOMBRE = 0x09EBE495           # pantalla de nombre
ASM_FIN_NOMBRE = (0x09EB5529, 0x09EAF389)
SUB_NUEVA_PARTIDA_NG = 0x09E68EED # Nueva Partida + (si el flag 0x16DA está activo)
SUB_PREPARA_PARTIDA = 0x09E68FAF  # lo que Unbound hace antes de dejarte en casa

# ---- textos ----
PAGINAS_1 = [
    "...{n}{n}......",
    "(Agua...){n}{n}(Oyes agua corriendo{n}bajo tus pies.)",
    "(Te asomas.){n}{n}(En la superficie, tu reflejo{n}te devuelve la mirada.)",
]
TEXTO_REFLEJO = "(¿Quién se refleja en el agua?)"
PAGINAS_2 = [
    "......",
    "...¿Me oyes?",
    "...Por fin...{n}{n}...alguien responde.",
    "He llamado a través{n}de los siglos...{n}{n}...y nadie había contestado.",
    "...¿Cómo te llamas?",
]
PAGINAS_3 = [
    "...{JUGADOR}.",
    "Escúchame bien, {JUGADOR}...{n}{n}...no queda mucho tiempo.",
    "Hay quien quiere borrar el pasado{n}de tu ciudad...{n}{n}...piedra a piedra...{n}...recuerdo a recuerdo.",
    "Y cuando el pasado desaparece...{n}{n}...el presente lo sigue.",
    "......",
    "Ha llegado el momento de que sepas{n}por qué estás aquí.",
    "...Tú puedes ir...{n}{n}...donde yo no puedo.",
    "......",
    "Cuando el reloj cante al revés...{n}{n}...sigue el agua.",
    "......Despierta.",
]


class Script:
    def __init__(self):
        self.partes = []      # bytes, o ("ptr", etiqueta), o ("etq", nombre)

    def b(self, *bs): self.partes.append(bytes(bs))
    def h(self, v): self.partes.append(struct.pack("<H", v))
    def w(self, v): self.partes.append(struct.pack("<I", v))
    def ptr(self, etq): self.partes.append(("ptr", etq))
    def etq(self, nombre): self.partes.append(("etq", nombre))
    def alinear(self, n=4): self.partes.append(("alin", n))   # relleno hasta múltiplo de n (estructuras con punteros)

    # órdenes
    def callasm(self, a): self.b(0x23); self.w(a)
    def call(self, a): self.b(0x04); self.w(a) if isinstance(a, int) else self.ptr(a)
    def goto(self, a): self.b(0x05); self.w(a) if isinstance(a, int) else self.ptr(a)
    def goto_if(self, c, a): self.b(0x06, c); self.w(a) if isinstance(a, int) else self.ptr(a)
    def call_if(self, c, a): self.b(0x07, c); self.w(a) if isinstance(a, int) else self.ptr(a)
    def setvar(self, v, x): self.b(0x16); self.h(v); self.h(x)
    def copyvar(self, a, b_): self.b(0x19); self.h(a); self.h(b_)
    def compare(self, v, x): self.b(0x21); self.h(v); self.h(x)
    def checkflag(self, f): self.b(0x2B); self.h(f)
    def waitstate(self): self.b(0x27)
    def delay(self, n): self.b(0x28); self.h(n)
    def fadescreen(self, m): self.b(0x97, m)
    def removeobject(self, n): self.b(0x53); self.h(n)
    def addobject(self, n): self.b(0x55); self.h(n)
    def setobjectxyperm(self, n, x, y): self.b(0x63); self.h(n); self.h(x); self.h(y)
    def setobjectmovementtype(self, n, m): self.b(0x65); self.h(n); self.b(m)
    def message(self, etq): self.b(0x67); self.ptr(etq)
    def waitmessage(self): self.b(0x66)
    def closemessage(self): self.b(0x68)
    def waitbuttonpress(self): self.b(0x6D)
    def waitse(self): self.b(0x30)
    def playse(self, n): self.b(0x2F); self.h(n)
    def playmoncry(self, sp, ef): self.b(0xA1); self.h(sp); self.h(ef)
    def waitmoncry(self): self.b(0xC5)
    def warpsilent(self, banco, mapa, x, y): self.b(0x3A, banco, mapa, 0xFF); self.h(x); self.h(y)
    def end(self): self.b(0x02)

    def pagina(self, etq_texto):
        self.b(0x0F, 0x00); self.ptr(etq_texto)          # loadpointer 0
        self.setvar(0x8000, 0); self.setvar(0x8001, 0)
        self.callasm(ASM_PAGINA); self.waitstate()

    def _medidas(self, base):
        """Recorre las partes y devuelve (etiquetas, tamaño de cada parte) para una dirección base."""
        etiquetas, tams, pos = {}, [], base
        for p in self.partes:
            if isinstance(p, tuple) and p[0] == "etq":
                etiquetas[p[1]] = pos; tams.append(0)
            elif isinstance(p, tuple) and p[0] == "alin":
                r = (-pos) % p[1]; tams.append(r); pos += r
            elif isinstance(p, tuple):
                tams.append(4); pos += 4
            else:
                tams.append(len(p)); pos += len(p)
        return etiquetas, tams

    def tam(self):
        return sum(self._medidas(0)[1]) + 4          # margen por si la base cambia el relleno

    def ensamblar(self, base, direcciones):
        etiquetas, tams = self._medidas(base)
        etiquetas.update(direcciones)
        out = bytearray()
        for p, n in zip(self.partes, tams):
            if isinstance(p, tuple) and p[0] == "etq":
                continue
            if isinstance(p, tuple) and p[0] == "alin":
                out += bytes(1) * n
            elif isinstance(p, tuple):
                out += struct.pack("<I", 0x08000000 + etiquetas[p[1]])
            else:
                out += p
        return bytes(out)

    def direcciones(self, base):
        return self._medidas(base)[0]


def comprobar(txt, pagina=True):
    import re
    vis = re.sub(r"\{(FC|FD):[0-9A-F]+\}", "", txt).replace("{JUGADOR}", "X" * 7)
    for caja in vis.split("{p}"):
        lineas = re.split(r"{n}|{l}", caja)
        for ln in lineas:
            if len(ln) > MAX_LINEA:
                sys.exit(f"Línea demasiado larga ({len(ln)}): «{ln}»")
        if pagina and len(lineas) > 7:
            sys.exit(f"Página con más de 7 líneas: «{txt}»")
    t.codificar(txt)


def main():
    textos = {}
    for i, p in enumerate(PAGINAS_1): textos[f"p1_{i}"] = p
    for i, p in enumerate(PAGINAS_2): textos[f"p2_{i}"] = p
    for i, p in enumerate(PAGINAS_3): textos[f"p3_{i}"] = p
    textos["reflejo"] = TEXTO_REFLEJO
    for k, v in textos.items():
        comprobar(v, pagina=(k != "reflejo"))

    s = Script()
    # --- arranque (igual que el de Unbound, incluida Nueva Partida +) ---
    s.callasm(ASM_INICIO_A); s.callasm(ASM_INICIO_B)
    s.checkflag(0x16DA); s.call_if(1, SUB_NUEVA_PARTIDA_NG)
    # --- 1. el agua y el reflejo ---
    for i in range(len(PAGINAS_1)): s.pagina(f"p1_{i}")
    # --- 2. chico o chica: primer paso del editor de Unbound ---
    s.callasm(ASM_EDITOR_PREP1); s.callasm(ASM_EDITOR_PREP2); s.call(SUB_EDITOR_RESET); s.fadescreen(0)
    s.etq("reflejo_msg"); s.message("reflejo"); s.waitmessage(); s.setvar(0x8003, 0)
    s.etq("reflejo_espera"); s.waitbuttonpress(); s.setvar(0x8001, 0); s.callasm(ASM_EDITOR_PASO)
    s.copyvar(0x8000, 0x800D)
    s.compare(0x8000, 0); s.goto_if(1, "reflejo_reinicio")
    s.compare(0x8000, 2); s.goto_if(1, "reflejo_cambio")
    s.goto("reflejo_ok")
    s.etq("reflejo_reinicio"); s.callasm(ASM_EDITOR_PREP2); s.call(SUB_EDITOR_RESET); s.goto("reflejo_msg")
    s.etq("reflejo_cambio"); s.removeobject(1)
    s.compare(0x8004, 0); s.call_if(1, SUB_CAMBIA_A_CHICO)
    s.compare(0x8004, 0); s.call_if(5, SUB_CAMBIA_A_CHICA)
    s.addobject(1); s.goto("reflejo_espera")
    s.etq("reflejo_ok"); s.waitse(); s.playse(0x15); s.closemessage(); s.fadescreen(1)
    s.removeobject(1)
    for a in ASM_FIN_EDITOR: s.callasm(a)
    s.removeobject(1); s.setobjectxyperm(1, 2, 0); s.setobjectmovementtype(1, 0)
    # --- 3. la voz... el nombre... la voz continúa ---
    for i in range(len(PAGINAS_2)): s.pagina(f"p2_{i}")
    s.callasm(ASM_NOMBRE); s.delay(0x10); s.fadescreen(1)      # como el original: pantalla a negro tras el nombre
    for a in ASM_FIN_NOMBRE: s.callasm(a)
    for i in range(len(PAGINAS_3)): s.pagina(f"p3_{i}")
    # --- 4. destello y rugido ---
    s.fadescreen(3)                                   # a blanco
    s.playmoncry(DIALGA, 0); s.waitmoncry()
    s.delay(0x20)
    # --- 5. a la habitación (como el "saltar apertura" de Unbound) ---
    s.setvar(0x5011, 1); s.call(SUB_PREPARA_PARTIDA)
    s.warpsilent(4, 1, 1, 7); s.waitstate(); s.end()          # cuarto (4.1): en la cama (x=1, y=7)

    rom = bytearray(t.ROM.read_bytes())
    trabajo = bytearray(rom)
    dirs = {}
    for k, v in textos.items():
        d = t.codificar(v)
        o = t.buscar_libre(bytes(trabajo), len(d)); trabajo[o:o + len(d)] = d; dirs[k] = o
    base = t.buscar_libre(bytes(trabajo), s.tam(), alinear=4)
    codigo = s.ensamblar(base, dirs)
    trabajo[base:base + len(codigo)] = codigo
    trabajo[PUNTERO_SCRIPT_INTRO:PUNTERO_SCRIPT_INTRO + 4] = struct.pack("<I", 0x08000000 + base)

    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-sueno_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp); print("Respaldo:", resp.relative_to(t.RAIZ))
    t.ROM.write_bytes(trabajo)
    print(f"Script del sueño: {len(codigo)} bytes en 0x{base:X}; {len(textos)} textos. "
          f"El mapa de la intro apunta ahora a él (0x{PUNTERO_SCRIPT_INTRO:X}).")


if __name__ == "__main__":
    main()
