# Guía del proyecto: Unbound con estética cordobesa

Guía de trabajo y material de clase. Explica qué hay en la carpeta, cómo se
instala cada herramienta y cómo funcionan por dentro las dos tareas grandes:
añadir un Pokémon nuevo y crear tilesets y mapas.

---

## 0. Lo que hemos verificado y lo que no

| Afirmación | Estado | Fuente |
|---|---|---|
| La ROM es un FireRed modificado (código `BPRE`) de 32 MB | **Verificado** (cabecera leída) | la propia ROM |
| A la ROM solo le queda ~1,3 MB libre (bloques de `0xFF`); el mayor mide 471 KB, en `0x15FA3E0` | **Verificado** (medido con script) | la propia ROM |
| CFRU y DPE son de Skeli789 y se usan juntos | **Verificado** | GitHub de Skeli789 |
| Unbound está hecho con CFRU y DPE | **Muy probable, no confirmado** con una fuente primaria en esta búsqueda (lo dice la comunidad) | foros/Reddit |
| HexManiacAdvance (HMA) **no está pensado** para editar hacks de otras personas: puede no ver tablas o Pokémon | **Verificado** (FAQ oficial de HMA) | wiki de HMA |
| En HMA es **inseguro** usar "Add New" en las tablas de Pokémon (nombres y stats), movimientos, MTs, tutores, entrenadores y Pokédex | **Verificado** (FAQ oficial) | wiki de HMA |
| Hay usuarios que editaron Unbound con HMA y los cambios no surtieron efecto | **Verificado como testimonio**, no reproducido | PokéCommunity |
| Advance Map, PGE y XSE rompen ROMs con CFRU | **Testimonio de la comunidad**, no probado aquí | Reddit |
| HMA incluye un motor de scripts en Python (IronPython) | **Verificado** (sus DLL están en la carpeta) | instalación local |
| HMA reconoce bien las tablas de **esta** ROM | **No verificado**: es lo primero que hay que comprobar | — |

### Tablas localizadas en esta ROM (análisis propio, 14/11/2026, solo lectura)

Scripts en `scripts/analisis/`. Comprobado extrayendo y dibujando sprites reales
(Bulbasaur, Pikachu, especies de Gen 8): ver `pruebas/extraccion_tablas.png`.

| Tabla | Dirección | Entradas | Formato |
|---|---|---|---|
| Nombres de especie | `0x1689AE8` | 1268 | 11 bytes por nombre |
| Sprite frontal | `0x1A26798` | 1268 | puntero + `0x0800` + nº especie |
| Sprite trasero | `0x19E8A84` | 1268 | ídem |
| Paleta normal | `0x1A3B3A0` | 1268 | puntero + etiqueta = nº especie |
| Paleta shiny | `0x1A47BEC` | 1268 | puntero + etiqueta = nº especie + 1268 |

**Huecos libres:** las especies **254 a 276** se llaman `?` y usan el sprite
"??". Son los huecos de relleno clásicos de FireRed y los mejores candidatos
para especies nuevas sin ampliar tablas.

**Conclusión práctica:** con Unbound vamos a **sustituir** contenido que ya
existe (huecos de especies, sprites, mapas) en vez de **añadir** contenido
nuevo, porque ampliar tablas es inseguro y casi no queda espacio.

---

## 1. Sistema y herramientas

Sistema detectado: **Windows 11 Pro** (10.0.26200), con Python 3.13 y .NET 6
Desktop ya instalados.

| Herramienta | Para qué | ¿Solo Windows? | Estado |
|---|---|---|---|
| HexManiacAdvance 0.5.6.1 | editar datos, sprites, mapas y scripts | **Sí** (usa WPF de .NET) | instalado en `herramientas/` |
| mGBA 0.10.5 | emulador para probar | No (Win/Mac/Linux) | instalado, modo portátil |
| Flips v198 | crear y aplicar parches BPS/IPS | No (Win/Linux) | instalado |
| Python + Pillow | scripts de conversión | No | entorno propio en `herramientas/python-venv` |
| Editor de pixel art | dibujar sprites y tiles | depende | **sin instalar** (ver abajo) |
| Advance Map 1.92 | editor clásico de mapas | **Sí** | **no instalado a propósito** (riesgo con CFRU) |

**Editores de pixel art recomendados:**
- **LibreSprite**: gratis, multiplataforma. Bueno para clase.
- **Aseprite**: de pago, el estándar actual, con modo de paleta indexada muy cómodo.
- **Usenti**: gratis, solo para Windows, pensado específicamente para paletas de GBA.

**Lo que puede automatizar Claude:** descargas e instalación dentro de la
carpeta, respaldos, restauración, parches, conversión de imágenes y paletas,
análisis de la ROM (espacio libre, buscar datos), y generar sprites de prueba.

**Lo que tienes que hacer tú:** el trabajo dentro de la interfaz de HMA
(importar, colocar bloques en el mapa) y probar en mGBA. Más adelante podría
automatizarse parte de HMA con su motor de scripts en Python.

---

## 2. Estructura de la carpeta y reglas de seguridad

```
GBA/
├── original/      ← Unbound intacto, marcado como solo lectura. NO SE TOCA.
├── MiHack.gba     ← la única ROM que se edita
├── respaldos/     ← copias con fecha (Crear respaldo.bat)
├── parches/       ← lo único que se comparte (Crear parche.bat)
├── scripts/       ← restaurar_copia.py, crear_parche.py, png_a_gba.py
├── herramientas/  ← HMA, mGBA, Flips, Python
└── GUIA.md
```

- **Restaurar MiHack.bat**: comprueba la huella SHA-1 del original, guarda la
  copia actual en `respaldos/` y deja MiHack.gba como el Unbound original.
- **Crear parche.bat**: genera `parches/MiHack_FECHA.bps`. Se usa BPS porque
  IPS no admite archivos de más de 16 MB. Para aplicarlo hace falta el mismo
  Unbound v2.0.3.2.
- **Nunca se comparte** la ROM ni assets con copyright: solo el parche. Si
  algún día se publica, conviene además pedir permiso al autor de Unbound.

---

## 3a. Flujo: añadir una especie nueva

### Cómo guarda la ROM a un Pokémon (concepto clave)

Un Pokémon no es "un archivo". Es **un número de especie** que sirve de
índice en muchas **tablas**, una por cada tipo de dato:

| Tabla | Qué guarda | Tamaño por especie en FireRed |
|---|---|---|
| Nombres | el nombre | 11 bytes |
| Base stats | PS, Ataque..., tipos, habilidades, ratio de captura, EXP | 28 bytes |
| Sprite frontal | puntero al dibujo comprimido + tamaño + especie | 8 bytes |
| Sprite trasero | ídem | 8 bytes |
| Paleta normal | puntero a la paleta comprimida + especie | 8 bytes |
| Paleta shiny | ídem | 8 bytes |
| Iconos | puntero al icono + qué paleta de iconos usa | 4 + 1 bytes |
| Evoluciones | método, parámetro y especie destino | 5 × 8 bytes (CFRU puede cambiarlo) |
| Movimientos por nivel | puntero a la lista de movimientos | 4 bytes |
| Compatibilidad MT/tutor | qué MTs aprende | variable |
| Pokédex | número nacional, altura, peso, descripción | variable |
| Otros | posición vertical en combate, animación, grito, huella | variable |

Si el Pokémon nº 412 es "X", la fila 412 de **cada** tabla habla de X.

### ¿Qué es el "repointing"?

Las tablas están una detrás de otra en la ROM. Para añadir una fila más no
hay hueco, porque justo detrás empieza otra cosa. La solución es:

1. Copiar la tabla entera a un **espacio libre** (zona llena de `FF`).
2. Añadir la fila nueva al final.
3. Buscar **todos los punteros** que apuntaban a la tabla vieja y cambiarlos
   para que apunten a la nueva. Si se olvida uno, el juego lee basura y se cuelga.

HMA hace esto automáticamente **cuando conoce la tabla**. El problema en
Unbound es doble: DPE ya amplió las tablas a cientos de especies (puede que
HMA no las conozca bien) y queda muy poco espacio libre.

### Flujo recomendado en Unbound: reutilizar un hueco

1. **Respaldo** (Crear respaldo.bat).
2. **Elegir el hueco**: una especie existente que no vayamos a usar, o una
   entrada vacía o de relleno si la hay (está por comprobar en esta ROM).
3. **Dibujar** frontal y trasero de 64×64, con un máximo de 15 colores más el
   transparente, **los dos con la misma paleta**.
4. **Convertir** con el script:
   ```
   herramientas\python-venv\Scripts\python.exe scripts\png_a_gba.py dibujo\frontal.png --tipo frontal
   herramientas\python-venv\Scripts\python.exe scripts\png_a_gba.py dibujo\trasero.png --tipo trasero --usar-paleta dibujo\frontal_gba.png
   ```
5. **Importar en HMA**: buscar la tabla de sprites frontales, ir a la fila de la
   especie, importar `frontal_gba.png`. HMA lo comprime (LZ77), busca sitio y
   actualiza el puntero. Repetir con el trasero, la paleta normal y la shiny
   (`_normal.pal`, `_shiny.pal`, o el hex de `_paletas.txt`).
6. **Datos**: en *Data > Pokémon Stats* cambiar nombre, stats, tipos y
   habilidades. Después movimientos, evoluciones y Pokédex.
7. **Probar en mGBA**: hacerlo aparecer (por ejemplo, ponerlo en la tabla de
   salvajes de una ruta) y revisar combate, menú, Pokédex y shiny.
8. Si algo falla, **Restaurar MiHack.bat** o volver al último respaldo.

**Atajo sin HMA:** `scripts/insertar_pokemon.py` hace los pasos 5 y parte del 6
(sprites, paletas y nombre) en un solo comando. Crea su propio respaldo, escribe en
la zona libre de `0x15FA500`, repuntea las cuatro tablas y lo verifica todo:
```
herramientas\python-venv\Scripts\python.exe scripts\insertar_pokemon.py --especie 1 --nombre Arquillo --carpeta assets\arquillo
```
Con `--simular` enseña lo que haría sin escribir nada. Es ideal para explicar el
repointing en clase, porque imprime las direcciones de antes y de después.

> Añadir especies **de verdad**, ampliando las tablas, se descarta en esta
> ROM: la FAQ de HMA lo marca como inseguro y no hay espacio para muchas.

---

## 3b. Flujo: tilesets y mapas

### Conceptos

- **Tile**: cuadrado de 8×8 píxeles con 16 colores (4 bits por píxel).
- **Bloque (metatile)**: cuadrado de 16×16 = 4 tiles por capa × 2 capas
  (abajo y arriba, para que el jugador pueda pasar "por detrás" de un tejado).
  Cada bloque tiene además un **comportamiento**: agua, hierba alta, puerta...
- **Tileset primario**: lo común (hierba, caminos, agua). En FireRed tiene
  640 tiles y usa las paletas 0-6.
- **Tileset secundario**: lo propio de una zona (casas, monumentos).
  En FireRed tiene 384 tiles y usa las paletas 7-12.
- **Mapa** = cabecera (música, tiempo, nombre) + **layout** (cuadrícula de
  bloques con su colisión y elevación) + **eventos** (personas, puertas,
  carteles, disparadores) + **conexiones** con otros mapas + scripts.

### Paleta cordobesa sugerida (15 colores)

- **Cal**: blanco, blanco hueso, gris azulado para las sombras.
- **Albero**: ocre claro y ocre oscuro.
- **Arco de herradura de la Mezquita**: rojo ladrillo y crema para las dovelas alternas.
- **Patio**: azul cobalto de las macetas, rojo de los geranios, dos verdes de las hojas.
- **Rejas y contornos**: negro y marrón oscuro.
- **Azulejo**: un turquesa.

### Flujo

1. **Respaldo**.
2. **Elegir qué sustituir**: un pueblo de Unbound y su tileset secundario.
   Sustituir es más seguro que crear, por el espacio.
3. **Dibujar los tiles** en el editor, en una imagen de ancho múltiplo de 8
   y respetando las paletas del tileset.
4. **Convertir**: `png_a_gba.py tiles.png --tipo libre --shiny-tono 0`
5. **Importar en HMA** el gráfico del tileset y montar los bloques
   (4 tiles + capa + comportamiento).
6. **Editar el layout del mapa** colocando los bloques nuevos, y después los
   eventos y las conexiones.
7. **Probar en mGBA**: colisiones, puertas, capas (que el jugador no
   "camine por encima" del tejado).

> Pendiente de comprobar: si el editor de mapas de HMA reconoce bien los mapas
> de Unbound. Advance Map queda descartado hasta comprobarlo con un respaldo.

---

## 3c. Scripts del capítulo 0 (intro)

| Script | Qué hace |
|---|---|
| `scripts/textos.py` | Lee, busca y sustituye textos (tabla de caracteres, repointing automático si no caben) |
| `scripts/cap0_intro.py` | Cambia los 35 textos de la intro por los del Profesor Acisclo, en español. Se puede reejecutar. |
| `assets/acisclo/crear_desde_unbound.py` | Crea al Profesor a partir del entrenador 107 de Unbound cambiando solo la paleta |
| `scripts/cap0_profesor_mapa.py` | Registra al Profesor como sprite de mapa de 64×64 (gráfico 0xFB, paleta 0x1268) y lo muestra como 3.ª persona del mapa negro de la intro, tras la página 1 |
| `scripts/cap0_quitar_imagenes.py` | Deshace la versión antigua con recuadros (showpokepic) |

**Lecciones aprendidas (probadas en mGBA):**
- La ventana de página completa de la intro de Unbound tapa cualquier imagen.
  Las imágenes van entre páginas.
- `showpokepic` abre un recuadro blanco que no encaja con el estilo de Unbound.
  Unbound enseña al jugador como un NPC grande sobre un mapa negro (cabecera
  `0xB55F58`), y el Profesor se muestra igual.
- Tabla de sprites del mapa: la tabla 0 está en `0x8110E0` (hay más tablas en
  `0x2825A4`, pero el byte alto del gráfico no se lee de los datos del mapa).
  Las posiciones 251-255 de la tabla 0 están libres: ningún mapa usa 0xFB-0xFF.
- Tabla de paletas de sprites del mapa: `0xEB994C`, con búsqueda por etiqueta.
  Las entradas vacías (360-364) se pueden usar.
- En mGBA, una pulsación muy larga puede saltar varias páginas.

## 3d. Portada y rótulo (scripts)

| Script | Qué hace |
|---|---|
| `scripts/portada_logo.py [--vista]` | Logo: mantiene "POKéMON" y cambia "UNBOUND" por "CÓRDOBA" (mismo estilo y colores) + "Ecos del Tiempo" |
| `scripts/portada_fondo.py [--vista] [--dialga]` | Fondo: "SKELI" pasa a "RANDES". `--dialga` (experimental, aún no usar) cambia la silueta |
| `scripts/portada_quitar_aros.py` | Vacía los aros dorados (la antigua "O" de UNBOUND) que tapaban "CÓRDOBA" |
| `scripts/portada_rotulo.py [--vista]` | "Skeli Games PRESENTS" pasa a "Randes PRESENTA" |
| `scripts/portada_mezquita.py [--vista]` | **Portada actual** (con `CON_DIALGA = False`: sin silueta, por decisión del usuario): fondo nuevo con la arquería de la Mezquita (dovelas rojas y crema, 3 planos), la silueta de Dialga a contraluz y "PULSA START"; paleta del fondo y del logo en la gama de la Mezquita. Sustituye a lo que hacía `portada_fondo.py`. |
| `scripts/portada_quitar_aros.py --destellos` | Vacía los destellos de Hoopa, que quedaban como puntos rojos sobre Dialga |

La silueta de Dialga sale del arte oficial (`descargas/dialga/483.png`, del
repositorio público de PokeAPI en GitHub). Solo se usa su contorno. Esa imagen
no se comparte; solo va el parche.
| `scripts/analisis/estado_mgba.py`, `render_bg.py`, `buscar_graficos.py` | Leen estados de mGBA (Shift+F1…F9), dibujan las capas y buscan en la ROM los gráficos que hay en la VRAM |

**Método para encontrar cualquier gráfico (para clase):**
1. En mGBA, pausar (Ctrl+P) en la pantalla deseada, avanzar fotograma a fotograma (Ctrl+N) y guardar el estado (Shift+F1…).
2. El estado es un PNG con la memoria de la consola comprimida: de ahí se sacan la VRAM, la paleta y los registros de vídeo (qué capas hay y dónde están sus tiles y su mapa).
3. Se buscan en la ROM bloques LZ77 que, descomprimidos, coincidan con la VRAM. Después se buscan los punteros que apuntan a esos bloques.

**Direcciones encontradas:**
- Logo: tiles `0x1FD4120` y mapa `0x1FD50A0`, apuntados desde `0x1ECE444`/`0x1ECE448`.
- Fondo: tiles 8bpp `0x1FC94FC` y mapa `0x1FCED50`, apuntados desde `0x1ECE508`/`0x1ECE74C` y `0x1ECE510`/`0x1ECE754`; paleta `0x1FCF1EC`.
- Rótulo: tiles `0xEF23D4` (puntero `0xECB6C`) y sprite "PRESENTS" `0xEF2674` (puntero `0x40BBE0`).

## 3e. Música de la portada

| Script | Qué hace |
|---|---|
| `scripts/musica_a_midi.py audio.m4a` | Transcribe una grabación a MIDI con Basic Pitch (modelo ONNX) → `musica/*.mid` |
| `scripts/midi_a_gba.py musica/medley_guitarra.mid --desde 4.03 --hasta 47.6` | Convierte el fragmento al formato de música de la GBA (M4A), en bucle, con la guitarra de nylon (programa 24) y lo pone como canción nº 278 (la de la portada) |

- Tabla de canciones: `0x7FE000` (8 bytes por canción: cabecera, reproductor).
  La portada usa la nº 278; la original tenía 8 pistas y el banco de instrumentos `0x104A5EC`.
- Cómo se encontró: en un estado de mGBA guardado en la portada, el reproductor
  de música (`0x03007300`) apuntaba a la cabecera de la canción, y esa cabecera
  aparecía en la tabla.
- Secciones del medley (por sus pausas): 0-49 s, 49-77 s, 77-100 s y 102-139 s.
  Para usar otra, basta con cambiar `--desde` y `--hasta`.
- La grabación original no se comparte: solo el parche.

**Versión actual (desde la partitura):**
- `scripts/partitura_pokemon.py`: "Pokémon Theme Tune, arranged for Classical Guitar"
  (Syd R. Duke), compases 1-20, transcritos a mano desde la tablatura (cuerda + traste
  = nota exacta). Genera `musica/pokemon_guitarra.mid` (200 notas, 40 s a 120 bpm), con
  la melodía más fuerte, los arpegios dejados sonar y los acordes rasgueados.
- `scripts/guitarra_instrumento.py`: guitarra española por síntesis aditiva con las
  resonancias de la caja (100, 205 y 450 Hz), 5 muestras a 13 379 Hz. Es el instrumento 0
  de un banco nuevo. El programa 24 de Unbound NO es una guitarra.
- `scripts/midi_a_gba.py musica/pokemon_guitarra.mid --desde 0 --hasta 40 --tal-cual --voicegroup <banco> --voz 0`
- `scripts/escucha_gba.py ... --tal-cual`: escucha de prueba que simula la GBA.


## 3f. Intro del sueño (escrita desde cero)

| Script | Qué hace |
|---|---|
| `scripts/cap0_sueno.py` | Escribe el script NUEVO de la intro (el sueño) y hace que el mapa de la intro lo ejecute (puntero `0x1E6865A`). Sustituye entero al script de Unbound: sin Profesor, sin test de dificultad, sin la historia de Borrius |
| `scripts/analisis/script_dec.py 0xDIR` | Decodificador de scripts: convierte los bytes en órdenes legibles |

Piezas del motor de Unbound que reutiliza:
- `callasm 0x09EAA7C5`: página de texto a pantalla completa (blanco sobre negro);
- primer paso del editor de personaje (`callasm 0x09EB53B9` con `0x8001 = 0`): chico o chica;
- `callasm 0x09EBE495`: pantalla de nombre;
- el final del "saltar apertura" de Unbound: `setvar 0x5011 1`, `call 0x09E68FAF` y
  `warpsilent 4 10 (1,2)`, la habitación inicial.

El script se escribe con una pequeña clase `Script` en Python: cada orden es un
método que añade sus bytes, y las etiquetas (saltos) se resuelven al final.

## 3g. Prólogo en casa (`scripts/prologo_casa.py`)

Eventos y scripts nuevos para el cuarto (mapa 4.1) y la planta baja (4.0). El sueño
termina con `warpsilent 4 1 (1,7)`: la casilla (1,7) es la cama (antes era (2,7) y el
protagonista aparecía al lado).

Lecciones aprendidas probándolo:
- Los eventos (warps, carteles, triggers) deben empezar en una dirección **múltiplo de 4**
  (`s.alinear(4)`); si no, la GBA lee mal los punteros y la escalera no funciona.
- Las escaleras de FireRed son "felpudos de flecha": hay que estar encima y **empujar hacia
  la escalera** (izquierda en el cuarto, derecha en la planta baja).
- Para cortar el paso por una puerta, el trigger va **sobre el felpudo** (fila 9), que es la
  fila por la que camina el jugador; en la fila 8 se podía rodear.
- Un objeto grande (la tele, 2x2) necesita un cartel en cada casilla desde la que se pueda mirar.
- Para probar rápido se usan estados guardados: ver `ESTADOS.md`.

## 3h. La Plaza de las Tendillas (`scripts/tendillas/`)

Mapa propio (3.0), orientado al norte, con la casa en una calle de al lado.

| Script | Qué hace |
|---|---|
| `tendillas/compositor.py` | "Photoshop de mapas": recorta piezas de CUALQUIER mapa de Unbound (por número de diseño), las pega en un lienzo, admite dibujos propios y lo convierte todo en un tileset completo propio (primario + secundario: 1024 tiles, 13 paletas) |
| `tendillas/plaza.py` | El PLANO de la plaza (se puede ejecutar solo para ver la vista previa; `--convertir` dice cuántos tiles y paletas gasta) |
| `tendillas/vista_previa.py` | Vista previa con la estatua de Dialga colocada exactamente como en el juego |
| `tendillas/arte.py` | Paleta de bronce de la estatua (y dibujos de la versión 1) |
| `tendillas/escribir.py` | Lo mete en la ROM: tilesets, diseño (hueco 22), sprites nuevos (estatua 0xFC, paloma 0xFD), eventos, scripts y cabecera |
| `tendillas/tileset.py`, `tendillas/mapa.py` | Versión 1 (un solo tileset de Unbound). Ya no se usan; se guardan como ejemplo |

Piezas de Unbound (diseño n.º): 87 ciudad del puerto (edificios de piedra con ventanas en arco, a los que
se les repite la fila de ventanas para hacerlos de 3-4 plantas y se les cambian los colores), 81 plaza
del mercado (puestos de rayas), 155 plaza moderna (farolas negras), 486 ciudad costera (pavimento,
sombrillas, macetas), 510 ciudad del desierto (palmeras, bancos, árboles redondos). Dibujos propios:
la fuente con pedestal escalonado y parterre de flores, las minifuentes, la torre del reloj, la cúpula,
balcones, toldos y mosaicos. Las palomas son un sprite de 16x16 dibujado a mano.

Composición (versión 3): todo es **simétrico respecto a un eje** (columna 18): la calle del norte,
la fuente y el pasaje del sur están alineados; a cada lado, lo mismo (minifuentes, mosaico, farolas en
las esquinas del marco de franjas, bancos mirando a la fuente, quioscos y naranjos en alcorques).
La fuente se dibuja en perspectiva 3/4: de cada pieza se ven la cara de arriba (clara) y la de delante
(con degradado), el muro del pilón y del parterre asoma por delante y el pedestal proyecta sombra
sobre el agua. Dialga se apoya en una peana de bronce sobre la cornisa.

Lecciones aprendidas:
- **Paletas:** con más de 120 colores distintos, un reparto "voraz" no encuentra cómo meterlos en
  13 paletas. El compositor usa un reparto **aglomerativo** (va uniendo los grupos de colores que
  menos colores nuevos añaden) y solo fusiona colores casi iguales si aun así no cabe.
- **Unbound tiene su propia lista de mapas.** El banco 3 real está en `0xB6D550` (la tabla de
  FireRed, `0x3526A8`, ya no se usa). El mapa 3.0 apuntaba a un pueblo de Unbound (cabecera
  `0x350880`): escribimos nuestra cabecera encima.
- El juego carga el **diseño** por su número (campo de la cabecera) en la tabla `0xB6FB20`, no por el puntero.
- Un mapa solo usa 2 tilesets. Para mezclar piezas de muchos, el compositor trabaja con IMÁGENES y
  luego genera tiles (sin repetidos, también volteados), 13 paletas de 15 colores (fusionando colores casi
  iguales si hace falta) y bloques. El tileset primario es una COPIA propia sin animaciones (callback 0).
- Al copiar una pieza se quita su suelo original: por bloques (`fondo`) o por colores (`quitar_colores_de`).
- **Capas:** lo que está en la capa de arriba se pinta encima del jugador (copas de árbol, cabezas de
  farola, columnas de agua de las minifuentes); el suelo, la fuente y los bancos van en la de abajo.
- Un **trigger con variable 0** es un trigger de clima en 3.ª generación: no lanza scripts.
- **Espacio libre:** la zona antigua (0x15FA500...) se llenó. La plaza usa una zona propia al final de
  la ROM (`0x1FE2B10-0x1FF8000`) y la casa otra (`0x1FF8000-0x1FFFF00`): se borran y se reescriben
  en cada ejecución.

## 4. Script `png_a_gba.py`

Ver los comentarios dentro de `scripts/png_a_gba.py`. Resumen:

- Comprueba el tamaño según el tipo (`frontal`, `trasero`, `entrenador`
  64×64; `icono` 32×64; `overworld16x16/16x32/32x32` como hojas de
  fotogramas; `libre`, cualquier múltiplo de 8).
- Pasa los colores a 15 bits (múltiplos de 8) y deja el índice 0 como
  transparente. Si el PNG ya trae transparencia, elige como fondo un color que
  no esté en el dibujo, para no borrar los contornos negros.
- Si hay más de 15 colores, reduce sin tramado y avisa.
- Genera la paleta shiny girando el tono (`--shiny-tono`, en grados). Los
  grises, el blanco y el negro no cambian.
- Exporta PNG indexado, vista previa del shiny, `.pal` (JASC) y hex GBA.

---

## Fuentes

- FAQ de HexManiacAdvance: https://github.com/haven1433/HexManiacAdvance/wiki/Hex-Maniac-Advance-%E2%80%90-Frequently-Asked-Questions
- HUBOL, añadir sprites: https://github.com/haven1433/HexManiacAdvance/wiki/HUBOL-%E2%80%90-Adding-New-Sprites-&-Particles
- Complete FireRed Upgrade: https://github.com/Skeli789/Complete-Fire-Red-Upgrade
- Dynamic Pokémon Expansion: https://github.com/Skeli789/Dynamic-Pokemon-Expansion
- Hilo de Unbound (Skeli): https://www.pokecommunity.com/threads/pok%C3%A9mon-unbound-completed.382178/
- Edición de la tabla de tipos de Unbound con HMA: https://www.pokecommunity.com/threads/hexmaniacadvance-editing-pokemon-unbound-type-chart.531709/
- Flips: https://github.com/Sir-Walrus/Flips
