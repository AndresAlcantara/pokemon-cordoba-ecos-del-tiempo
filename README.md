# Pokémon Córdoba — Ecos del Tiempo

Hack de GBA ambientado en **Córdoba**, construido sobre **Pokémon Unbound v2.0.3.2**
(un hack binario de FireRed). Es un proyecto educativo: cada paso está explicado para
poder enseñarlo en clase.

> **Este repositorio no contiene ninguna ROM ni recursos con copyright.** Solo hay
> scripts propios, documentación y **parches BPS** (`parches/`). Para jugar hace falta
> tener tu propia copia de Pokémon Unbound v2.0.3.2 y aplicarle el parche (por ejemplo con Flips).

---

## De qué va la historia

El protagonista (chico o chica, con el nombre que elija el jugador) vive junto a la
**Plaza de las Tendillas**. Una noche sueña con una voz sin nombre que le llama a
través de los siglos: es **Dialga**, aunque el jugador todavía no lo sabe.

Al despertar, el día de su cumpleaños, el pasado de Córdoba empieza a borrarse:
los monumentos desaparecen y nadie lo recuerda salvo él. Dialga le envía atrás en el
tiempo para salvar la memoria de la ciudad antes de que el **Equipo Olvido**, dirigido
en secreto por el **relojero** de las Tendillas, la reescriba.

- **Ocho gimnasios, uno por época**, de la más antigua a la más moderna:

  | # | Época | Lugar | Líder |
  |---|---|---|---|
  | 1 | Turdetanos (s. III a. C.) | Colina de los Quemados | Caudillo turdetano |
  | 2 | Roma (s. I) | Templo Romano, Puente Romano | Séneca |
  | 3 | Emirato (s. IX) | Primera Mezquita | Abbás ibn Firnás |
  | 4 | Califato (s. X) | Medina Azahara | Lubna |
  | 5 | s. XII | Judería | Averroes |
  | 6 | 1486 | Alcázar de los Reyes Cristianos | El Gran Capitán |
  | 7 | Barroco | Plaza de la Corredera | Góngora |
  | 8 | 1936-1939 | Museo de Bellas Artes | Conservadora del museo |

- **La Liga** se celebra en la Córdoba actual, ya restaurada. El campeón es **Chalo**
  (Gonzalo), el rival y amigo de la infancia.
- **Profesor Acisclo:** tiene su laboratorio junto al **lago subterráneo** que, según
  la leyenda, hay bajo las Tendillas.
- **Iniciales del mayo cordobés:** Mudbray (las Caballerizas), Fuecoco (el Caimán de
  la Fuensanta; hay que añadirlo) y Flabébé (la Fiesta de los Patios).
- **Tono:** aventura clásica con mucha historia real. En la Guerra Civil se nombran
  los bandos sin tomar partido.
- **Giro final:** en el primer viaje, el protagonista pronuncia sin saberlo la palabra
  que acabará dando nombre a la ciudad, *Corduba*.

El diseño completo está en [HISTORIA.md](HISTORIA.md).

---

## Lo que llevamos

### Hecho y probado en el emulador

- **Pantalla de título:** arcos de la Mezquita en rojo ladrillo y crema, logo
  "Pokémon CÓRDOBA – Ecos del Tiempo", "PULSA START", rótulo "Randes PRESENTA" y
  aviso de copyright de Unbound saltado.
- **Música del título:** transcrita a mano de una tablatura de guitarra, con un
  instrumento de guitarra española sintetizado (`scripts/guitarra_instrumento.py`,
  `scripts/midi_a_gba.py`). La partitura no se incluye por tener copyright; la
  canción ya va dentro del parche.
- **Intro nueva, escrita desde cero (el sueño):** agua y reflejo para elegir chico o
  chica, la voz pide el nombre y deja pistas ("piedra a piedra... recuerdo a recuerdo",
  "Cuando el reloj cante al revés... sigue el agua"). Sin profesor ni test de
  dificultad (`scripts/cap0_sueno.py`).
- **Prólogo en casa:** despertar en la cama ("...Qué sueño más raro..."), grito de
  Mamá con su nombre en el recuadro, escena de la madre cordobesa (tejeringos,
  zapatillas de deporte) y carteles del cuarto y la planta baja (`scripts/prologo_casa.py`).
- **Plaza de las Tendillas (mapa nuevo):**
  - Orientada al norte y simétrica respecto a un eje: calle norte, fuente y pasaje sur.
  - Edificios clásicos de 3-4 plantas en crema, ocre, blanco y rosa, con balcones de
    hierro y toldos. El **edificio del reloj**, en el lateral oeste, con la esfera
    marcando las diez. En la esquina noreste, un edificio con cúpula y figura alada.
  - **Fuente central** en perspectiva con **Dialga de bronce** sobre un pedestal
    escalonado y un parterre de flores. Minifuentes a ambos lados (con colisión).
  - Naranjos en alcorques, farolas, bancos, quioscos, mosaicos y sombras.
  - Límites visibles en todos los lados (edificios, árboles y bolardos), sin muros invisibles.
  - Vida: vecinos con diálogo, paseantes, palomas (sprite dibujado a mano), un
    guitarrista, el relojero, el guardia que corta la calle y **Chalo**, que se marcha
    hacia el laboratorio tras hablar con él.
  - La casa del protagonista está en una calle junto a la plaza.

### Pendiente

1. **Laboratorio** junto al lago subterráneo y elección del inicial (añadir Fuecoco).
2. Primer combate, el reloj que suena al revés, la noche en las Tendillas y el primer
   salto en el tiempo (escenas 3-7 del prólogo en HISTORIA.md).
3. Decidir el concepto que sustituye a los "Engranajes del Tiempo" (propuesta: los *ecos*).
4. Traducir la pantalla de nombre y los menús Sí/No, que siguen en inglés.
5. Probar los diálogos y carteles que aún no se han probado en la plaza.

---

## Cómo está organizado

| Carpeta / archivo | Qué hay |
|---|---|
| `HISTORIA.md` | Diseño de la historia, personajes, épocas y escenas |
| `GUIA.md` | Guía técnica para clase: direcciones de la ROM, cómo funciona cada script y lecciones aprendidas |
| `ESTADOS.md` | Qué hay en cada estado guardado del emulador (para probar rápido) |
| `scripts/` | Todos los scripts en Python que modifican la ROM |
| `scripts/tendillas/` | El **compositor** de mapas y la Plaza de las Tendillas |
| `scripts/analisis/` | Herramientas de solo lectura: dibujar mapas, leer estados de mGBA, decodificar scripts... |
| `parches/` | Parches BPS para aplicar sobre Pokémon Unbound v2.0.3.2 |
| `*.bat` | Accesos directos (Windows) para jugar, editar, hacer respaldos y crear el parche |

Las herramientas externas (mGBA, HexManiacAdvance, Flips y el entorno de Python) no
se incluyen; la GUIA explica cuáles son y cómo instalarlas en `herramientas/`.

## Cómo jugar

1. Consigue tu propia copia de **Pokémon Unbound v2.0.3.2**.
2. Aplica el parche más reciente de `parches/` con Flips (o cualquier programa de parches BPS).
3. Abre la ROM resultante en un emulador de GBA (probado en mGBA 0.10.5).
