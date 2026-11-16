"""
cap0_intro.py
=============
Capítulo 0: sustituye la introducción de Unbound por la del Profesor Acisclo,
en español, y traduce las preguntas de dificultad que vienen después.

Cómo funciona la intro de Unbound (script en 0x1E68660):
  - 4 "páginas" en una ventana grande (hasta 7 líneas cada una)
  - creación del personaje (chico o chica, piel, pelo, ropa)
  - nombre
  - test de dificultad (preguntas de sí o no)
Este script solo cambia TEXTOS: el orden y los menús siguen siendo los de Unbound.

Uso (desde la carpeta GBA):
  herramientas\\python-venv\\Scripts\\python.exe scripts\\cap0_intro.py [--simular]
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textos as t  # noqa: E402

MAX_LINEA = 35      # caracteres visibles por línea (medido en los textos de Unbound)

TEXTOS = {
    # ---- páginas de la ventana grande (máx. 7 líneas) ----
    0x1F07432: "¡Hola! ¡Perdona la espera!{n}{n}Te doy la bienvenida al mundo{n}de los Pokémon.{n}{n}"
               "Me llamo Acisclo, aunque en Córdoba{n}me llaman el Profesor Pokémon.",
    0x1F074D9: "Este mundo está habitado por unas{n}criaturas llamadas Pokémon.{n}{n}"
               "Las personas y los Pokémon llevamos{n}siglos viviendo juntos en esta{n}ciudad.",
    0x1F07586: "Romanos, califas, sabios y poetas…{n}todos pasaron por estas calles.{n}{n}"
               "Y cada uno dejó su huella en{n}Córdoba.",
    0x1F07628: "Pero bueno, ¡basta de historia!{n}{n}Ahora quiero saber de ti.{n}{n}¡Vamos a conocerte!",
    # ---- creación del personaje ----
    0x1F07678: "¿Chico o chica? Elige tu personaje.",
    0x1F0768C: "Elige el tono de piel.",
    0x1F076A0: "Elige el color del pelo.",
    0x1F076B6: "Elige el color de la chaqueta.",
    0x1F076CE: "Elige el color de los detalles.",
    0x1F076E4: "¿Te gusta cómo ha quedado?",
    0x1F07700: "Y por último, ¿cómo te llamas?",
    0x1F07728: "¿Te llamas {JUGADOR}?",
    # ---- tras el nombre: Chalo, el reloj y la pista del final ----
    0x1F07739: "¡Así que te llamas {JUGADOR}!{p}"
               "Tu vecino y amigo de la infancia se{n}llama Gonzalo…{p}"
               "…aunque en el barrio todo el mundo{n}le llama Chalo.{p}"
               "Vivís en las Tendillas, junto al{n}famoso reloj de la plaza.{p}"
               "¿Sabías que ese reloj no toca{n}campanas, sino guitarra flamenca?{p}"
               "Dicen que en Córdoba el tiempo{n}suena distinto…{p}"
               "{JUGADOR}, tu historia está a punto{n}de comenzar.{p}"
               "Aunque quizá… empezó hace mucho{n}más tiempo del que imaginas.{p}"
               "Pero antes, unas preguntas para{n}ajustar el juego a ti.{p}"
               "¿Es tu primera vez con este juego?",
    # ---- test de dificultad (traducción) ----
    0x1F077A6: "¿Juegas con los emuladores Eclipse,{n}JohnGBA o No$GBA?",
    0x1F077E4: "Ese emulador hará que el juego se{n}cuelgue.{p}Cambia de emulador antes de{n}seguir jugando.",
    0x1F07867: "¿Se te suele olvidar guardar?",
    0x1F07884: "¿Te gustan los puzles difíciles?{p}Por ejemplo, puzles de sigilo o{n}de empujar rocas.",
    0x1F078ED: "¿Conoces las ventajas de tipo más{n}comunes, como que el tipo Hada{l}es débil contra el tipo Veneno?",
    0x1F0794F: "¿Conoces los tipos de la mayoría{n}de los Pokémon, como que Gliscor{l}es de tipo Tierra y Volador?",
    0x1F079B5: "¿Buscas una experiencia tranquila,{n}sin preocuparte mucho por los{l}combates?",
    0x1F07A0F: "¿Te parece bien entrenar a un{n}Pokémon nuevo de vez en cuando?",
    0x1F07A51: "¿Conoces los EV y los IV, y te{n}gusta tenerlos en cuenta?",
    0x1F07A8C: "¿Te importaría entrenar EV si la{n}situación lo pide?",
    0x1F07AC9: "{FC:0106}{FD:02}{FC:0102} es la dificultad{n}recomendada para ti.{p}"
               "Puedes elegir una más alta, pero{n}podría estropear tu experiencia.{p}"
               "¿Continuamos con la dificultad{n}{FC:0106}{FD:02}{FC:0102}?",
    0x1F07B8F: "{FC:0106}Expert{FC:0102} es la dificultad{n}recomendada para ti.{p}"
               "Si tienes buena mano, no tendrás{n}que entrenar EV al principio.{p}"
               "Más adelante sí hará falta, además{n}de algo de estrategia en{l}los combates.{p}"
               "¿Continuamos con la dificultad{n}Expert?",
    0x1F07CB1: "Elige la dificultad de los puzles.{p}Cuanto más difícil, más complicados{n}serán los de lógica y sigilo.",
    0x1F07D18: "Dificultad de los puzles:{n}{FC:0106}{FD:02}{FC:0102}.{p}"
               "Si la cambias en el menú de{n}opciones, sal de la zona para que{l}se aplique el cambio.",
    0x1F07DBF: "Elige la dificultad del combate.{p}Cuanto más alta, más fuertes son{n}"
               "los entrenadores y más listos{l}los Pokémon salvajes.",
    0x1F07E2E: "Este modo es para quien ya tiene{n}algo de experiencia en combates.{p}"
               "No tendrás que preocuparte por los{n}EV ni los IV, pero conviene pensar{l}"
               "una estrategia antes de luchar.{p}¿Continuamos con la dificultad{n}{FC:0106}Difficult{FC:0102}?",
    0x1F07F43: "Este modo está pensado para un{n}equipo entrenado en EV.{p}"
               "Con un equipo así, seguramente no{n}tendrás que cambiarlo entre los{l}combates importantes.{p}"
               "¿{FC:0106}SEGURO{FC:0102} que quieres la dificultad{n}{FC:0106}Expert{FC:0102}?",
    0x1F08036: "{FC:0107}¡AVISO!{FC:0102}{p}Este modo está pensado para ser{n}casi imposible.{p}"
               "Muchas veces te parecerá injusto{n}o pesado.{p}¡Y es a propósito!{p}"
               "Si la eliges, prepárate para{n}perder muchísimas veces.{p}"
               "Y si sigues adelante, no podrás{n}culpar a nadie más que a ti…{p}"
               "¿{FC:0106}SEGURO{FC:0102} que quieres la dificultad{n}{FC:0106}Insane{FC:0102}?",
    0x1F081AD: "Dificultad de la partida:{n}{FC:0106}{FD:02}{FC:0102}.{p}"
               "Puedes cambiar entre Vanilla y{n}Difficult cuando quieras desde el{l}menú de opciones.",
    0x1F08234: "Dificultad de la partida:{n}{FC:0106}{FD:02}{FC:0102}.{p}"
               "Como tienes Nueva Partida +, puedes{n}cambiarla cuando quieras desde el{l}menú de {FC:0106}opciones{FC:0102}.",
    0x1F082C9: "Además, hay un límite de nivel{n}activado, pero puedes quitarlo{l}cuando quieras desde el menú de{l}opciones.",
    0x1F0834E: "¿Quieres activar un límite de nivel{n}opcional?{p}"
               "Al llegar a ciertos niveles, tus{n}Pokémon no ganarán más experiencia{l}hasta superar el siguiente reto.",
}

PAGINAS = {0x1F07432, 0x1F074D9, 0x1F07586, 0x1F07628}


def comprobar(off, texto):
    """Revisa largo de líneas y número de líneas por caja. Devuelve lista de avisos."""
    import re
    avisos = []
    visible = re.sub(r"\{(FC|FD):[0-9A-F]+\}", "", texto).replace("{JUGADOR}", "X" * 7)
    cajas = visible.split("{p}")
    for caja in cajas:
        lineas = re.split(r"\{n\}|\{l\}", caja)
        for ln in lineas:
            if len(ln) > MAX_LINEA:
                avisos.append(f"0x{off:X}: línea de {len(ln)} caracteres: «{ln}»")
        if off in PAGINAS and len(lineas) > 7:
            avisos.append(f"0x{off:X}: la página tiene {len(lineas)} líneas (máx. 7)")
    t.codificar(texto)  # lanza error si hay caracteres no admitidos
    return avisos


def main():
    simular = "--simular" in sys.argv
    avisos = [a for off, txt in TEXTOS.items() for a in comprobar(off, txt)]
    for a in avisos:
        print("AVISO:", a)
    if avisos:
        sys.exit("Corrige los avisos antes de escribir.")
    print(f"{len(TEXTOS)} textos revisados: longitud y caracteres correctos.")
    if simular:
        return
    resp = t.RAIZ / "respaldos" / f"MiHack_antes-de-cap0_{datetime.now():%Y-%m-%d_%H%M%S}.gba"
    shutil.copy2(t.ROM, resp)
    print("Respaldo:", resp.relative_to(t.RAIZ))
    rom = bytearray(t.ROM.read_bytes())
    # Las claves son las direcciones ORIGINALES de Unbound. Si un texto ya se movió
    # en una pasada anterior, se encuentra siguiendo el puntero del script.
    # Así este script se puede ejecutar las veces que haga falta.
    original = (t.RAIZ / "original" / "Pokemon Unbound v2.0.3.2 (ORIGINAL - no tocar).gba").read_bytes()
    actuales = {}
    for off in TEXTOS:
        refs = t.punteros_a(original, off)
        if not refs:
            sys.exit(f"ERROR: nadie apunta a 0x{off:X} en el original")
        valor = int.from_bytes(rom[refs[0]:refs[0] + 4], "little")
        if 0x08000000 <= valor < 0x0A000000:
            actual = valor - 0x08000000
        else:
            # Ese trozo del script se desvió (cap0_imagenes.py): el texto sigue en su sitio original
            actual = off
        refs_actuales = t.punteros_a(bytes(rom), actual)
        actuales[off] = (refs_actuales, actual)
    for off, txt in TEXTOS.items():
        print(" ", t.sustituir(rom, actuales[off][1], txt))
    t.ROM.write_bytes(rom)
    # Verificación: desde CADA puntero del script se lee exactamente el texto nuevo
    rom2 = t.ROM.read_bytes()
    fallos = 0
    for off, txt in TEXTOS.items():
        for r in actuales[off][0]:
            destino = int.from_bytes(rom2[r:r + 4], "little") - 0x08000000
            if rom2[destino:destino + len(t.codificar(txt))] != t.codificar(txt):
                fallos += 1; print(f"  FALLO en el puntero 0x{r:X}")
    print("Verificación:", "TODO CORRECTO" if not fallos else f"{fallos} fallos")
    print("Escrito. Verifica en el juego con 'Jugar MiHack (mGBA).bat'.")


if __name__ == "__main__":
    main()
