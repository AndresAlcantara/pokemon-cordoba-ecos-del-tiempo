# Pokémon Córdoba — Ecos del Tiempo

Documento de diseño de la historia. Base técnica: Pokémon Unbound v2.0.3.2
(ROM modificada; solo se comparte como parche). Los Pokémon son los que ya
tiene Unbound, más la línea de Fuecoco, que habrá que añadir.

---

## 1. Idea general

El protagonista vive hoy junto a la **Plaza de las Tendillas**. Un día el
pasado de Córdoba empieza a borrarse: los monumentos desaparecen y nadie lo
recuerda salvo él. **Dialga** lo envía atrás en el tiempo para recuperar los
**ocho Engranajes del Tiempo** *(pendiente de sustituir por un concepto propio, ver 4.3)*, repartidos por la historia de la ciudad, antes
de que el **Equipo Olvido** los reúna.

Cada época tiene un gimnasio, y van de la más antigua a la más moderna, hasta
la Guerra Civil. La **Liga** se celebra en la Córdoba actual, ya restaurada.

**Giro final:** en el primer viaje (época turdetana) el protagonista pronuncia
la palabra que acabará dando nombre a la ciudad, *Corduba*, sin saberlo. Se
revela al final: siempre fue parte del origen de Córdoba. El origen real del
nombre está discutido por los historiadores, y el juego lo dice expresamente
a través de un personaje del museo.

**Tono:** aventura clásica e históricamente interesante. Sin posicionamiento
político: los hechos se cuentan tal cual y los bandos se nombran, sin juzgarlos.

---

## 2. Personajes

| Personaje | Descripción |
|---|---|
| **Protagonista** | 12-13 años, vive en las Tendillas. **El jugador elige chico o chica y su nombre.** |
| **Profesor Acisclo** | Profesor Pokémon. Tiene su laboratorio junto al **lago subterráneo de las Tendillas**. Su nombre viene de San Acisclo, patrón de Córdoba. |
| **Gonzalo, "Chalo"** | Rival y amigo de la infancia del barrio. Nombre fijo: Gonzalo, aunque todos le llaman Chalo. Su nombre viene de Gonzalo Fernández de Córdoba, el Gran Capitán, cuya estatua está en las Tendillas. Será el campeón de la Liga. |
| **Dialga** | Guardián del tiempo. Aparece sobre la estatua del Gran Capitán, en las Tendillas. |
| **El relojero** | Mantiene el reloj de las Tendillas y es el líder secreto del Equipo Olvido. Perdió a alguien querido y quiere reescribir la historia para evitarlo. |

### Pokémon iniciales: el mayo y la tradición cordobesa

| Inicial | Tipo | Referencia |
|---|---|---|
| **Mudbray** → Mudsdale | Tierra | Las Caballerizas Reales (1570) y el caballo andaluz |
| **Fuecoco** → Crocalor → Skeledirge | Fuego | El Caimán de la Fuensanta (*hay que añadirlo a la ROM*) |
| **Flabébé** → Floette → Florges | Hada | La Fiesta de los Patios (Patrimonio UNESCO, 2012) |

---

## 3. Estructura

**Mecánica central:** el reloj de las Tendillas marca la hora y el **lago
subterráneo** de debajo de la plaza abre el paso al pasado. Al volver al
presente con cada engranaje, **reaparece un monumento** en la Córdoba actual.

### El lago subterráneo de las Tendillas

Inspirado en la historia popular cordobesa del lago bajo la plaza (agua en el
subsuelo, entre la realidad y la leyenda, cerca de donde estuvo el foro romano).

- Se entra por una puerta discreta en una calle de la plaza y se baja por
  unas escaleras antiguas a una cueva con el lago, columnas y piedras romanas
  a medio enterrar, y el laboratorio del Profesor Acisclo montado entre ellas.
- Acisclo lo estudia porque "su agua guarda la memoria de la ciudad".
- Es el lugar de la entrega del Pokémon inicial, del primer combate, de los
  viajes en el tiempo y del enfrentamiento final con el relojero.
- En lo técnico, se pueden reutilizar los tilesets de cueva con agua de
  Unbound y añadir columnas romanas.

### Recorrido del rival (Chalo)

1. **Intro:** el Profesor lo presenta: se llama Gonzalo, aunque todos le llaman Chalo.
2. **Prólogo:** te espera en la plaza, porque él también recibe hoy su primer
   Pokémon. En el laboratorio del lago eliges tú primero y él coge el que
   mejor aguanta al tuyo:
   - si eliges Fuecoco, él coge Mudbray;
   - si eliges Mudbray, él coge Flabébé;
   - si eliges Flabébé, él coge Fuecoco.

   Primer combate a la orilla del lago.
3. **El reloj al revés:** se queda congelado y no recuerda el Templo Romano
   desaparecido. Así ves que lo que pasa es real.
4. **Entre gimnasios, en el presente:** entrena y te reta, cada vez más fuerte.
   No sabe nada de los viajes, pero nota cosas raras ("¿ese puente siempre ha
   estado ahí?").
5. **A mitad de juego (tras el gimnasio 4):** descubre tu secreto, se cuela en
   un viaje y te acompaña un capítulo. Luego decide quedarse protegiendo el barrio.
6. **Antes del final:** el relojero intenta reclutarlo y él se niega.
7. **Liga:** es el campeón. "Mientras tú salvabas la historia, yo me preparaba
   para ganarte."

| # | Época | Lugar | Líder | Tipo |
|---|---|---|---|---|
| 1 | Turdetanos (s. III a. C.) | Colina de los Quemados (Parque Cruz Conde) | Caudillo turdetano (ficticio) | Roca |
| 2 | Roma (s. I) | Templo Romano, Puente Romano, Teatro | Séneca (con Lucano) | Psíquico |
| 3 | Emirato (s. IX) | Primera Mezquita | Abbás ibn Firnás (con Ziryab) | Volador |
| 4 | Califato (s. X) | Medina Azahara | Lubna (con Abderramán III y Alhakén II) | Hada o Psíquico |
| 5 | s. XII | Judería, Sinagoga | Averroes (con Maimónides de niño) | Lucha o Psíquico |
| 6 | s. XV (1486) | Alcázar de los Reyes Cristianos | El Gran Capitán (con Colón e Isabel I) | Acero |
| 7 | Barroco (s. XVII) | Plaza de la Corredera | Góngora | Siniestro o Fantasma |
| 8 | 1936-1939 | Museo de Bellas Artes / Museo Julio Romero de Torres | Conservadora del museo (ficticia) | Normal o Fuego |

**Liga (en la actualidad):** el Alto Mando en la Mezquita-Catedral, el Palacio
de Viana, Medina Azahara y la Torre de la Calahorra. El campeón es Chalo.

---

## 4. Capítulo 0: pantalla de inicio e introducción

### 4.1 Pantalla de título

**Escena:** de noche, la **Plaza de las Tendillas** con el **reloj** al fondo.
Las agujas giran hacia atrás. Detrás del reloj, la silueta de **Dialga** se
recorta contra arcos de herradura rojos y blancos, como un eco de la Mezquita.

- **Logo:** "Pokémon CÓRDOBA", y debajo, más pequeño, "Ecos del Tiempo".
- **Animación (si es viable):** las agujas del reloj giran al revés, los ojos
  de Dialga brillan y caen destellos lentos (azul y plata, los colores de Dialga).
- **Texto:** `PULSA START`
- **Sonido:** unos acordes de guitarra, el sonido del reloj de las Tendillas,
  antes de la música del título.
- **Créditos pequeños abajo:** "Hack de Pokémon Unbound · Proyecto no oficial".

**Límites técnicos:** la pantalla mide 240×160 píxeles, con 4 capas de fondo
y paletas de 16 colores. El arte se diseña con eso en mente.

### 4.2 Introducción: el sueño (antes de empezar)

**Decisiones (revisadas con el usuario):** la intro es un **sueño**. El
Profesor no aparece en ella, no hay test de dificultad (dificultad por defecto,
cambiable en Opciones) ni la historia de Borrius de Unbound. Se elige **chico o
chica** (sin el editor de piel, pelo y ropa) y el **nombre**. **No se dice quién
habla** (es Dialga, pero el jugador no lo sabe todavía): una voz que lleva
siglos llamando a través del tiempo y, por primera vez, alguien le responde.
Por eso tiene sentido que pregunte quién es, y el giro final queda intacto.
Hay muchos silencios ("...") y nada de "engranajes".

[Pantalla negra. Se oye agua correr.]
```
▶ ...
▶ ......
▶ (Agua... Oyes agua corriendo
  bajo tus pies.)
▶ (Te asomas. En la superficie,
  tu reflejo te devuelve la mirada.)
      [elegir CHICO / CHICA: el reflejo]
▶ ......
▶ ...¿Me oyes?
▶ ...Por fin...
  ...alguien responde.
▶ He llamado a través de los siglos...
  ...y nadie había contestado.
▶ ...¿Cómo te llamas?
      [pantalla de nombre]
▶ ...NOMBRE.
▶ Escúchame bien, NOMBRE...
  ...no queda mucho tiempo.
▶ Hay quien quiere borrar el pasado
  de tu ciudad...
▶ ...piedra a piedra...
  ...recuerdo a recuerdo.
▶ Y cuando el pasado desaparece...
  ...el presente lo sigue.
▶ ......
▶ Ha llegado el momento de que sepas
  por qué estás aquí.
▶ ...Tú puedes ir...
  ...donde yo no puedo.
▶ ......
▶ Cuando el reloj cante al revés...
  ...sigue el agua.
▶ ......Despierta.
      [destello azul; un rugido lejano]
```

- *"Tú puedes ir donde yo no puedo"*: el viaje en el tiempo, dicho con sutileza.
- *"Cuando el reloj cante al revés... sigue el agua"*: se entiende en el prólogo
  (el reloj de las Tendillas y el lago bajo la plaza).
- Al final del juego la voz podrá cerrar el círculo: *"no fue casualidad que
  respondieras tú"*.

**Nombres sugeridos en el teclado:**
- **Chico:** RAFAEL (San Rafael, custodio de Córdoba), LUCIO (Lucio Anneo
  Séneca), MANUEL.
- **Chica:** VICTORIA (Santa Victoria, patrona), LUBNA, ANA.

### 4.3 Decisiones

- [x] Intro como sueño, con una voz sin nombre (Dialga)
- [x] Se elige chico o chica, y el nombre
- [x] Sin Profesor en la intro, sin test de dificultad, sin la historia de Borrius
- [x] Rival: nombre fijo, Gonzalo, "Chalo" (se le conoce en la plaza)
- [x] Título: "Pokémon Córdoba — Ecos del Tiempo"
- [ ] **Pendiente:** sustituir los "Engranajes del Tiempo" por un concepto
      propio. Propuesta: los **ecos**, la memoria viva de cada época que el
      villano va borrando, enlazado con el título.

### 4.4 Regla de redacción: texto neutro para el jugador

Como se puede jugar con chico o con chica, los textos dirigidos al jugador
evitan las palabras con género: no "¿Estás listo?", sino "¿Todo listo?"; no
"Bienvenido", sino "Te doy la bienvenida". Así no hace falta duplicar cada
texto. Es un buen ejercicio de redacción para clase.

### 4.5 Notas técnicas (para cuando se modifique la ROM)

- Las tildes, la ñ, ¿ y ¡ existen en el juego de caracteres de la GBA. Hay que
  comprobar que la fuente de Unbound las dibuja bien.
- Los textos de la intro de Unbound se pueden sustituir. Si el texto nuevo es
  más largo que el original, hay que reubicarlo (repuntear), como con los sprites.
- La pantalla de título exige cambiar gráficos, tilemaps y paletas del título
  de Unbound. Es la parte técnica más delicada del capítulo 0.

---

## 5. Prólogo: "El reloj que sonó al revés"

**Cuándo:** primeros de **mayo**, en la actualidad. Es el cumpleaños del
protagonista y la ciudad prepara las **Cruces de Mayo**, que conectan con los
iniciales del mayo cordobés.
**Dónde:** casa del protagonista, Plaza de las Tendillas y calles cercanas,
y el laboratorio del lago subterráneo.
**Duración estimada:** 20-30 minutos.
**Objetivo:** recibir el inicial, presentar a Chalo, al Profesor y al relojero,
ver el primer borrado del pasado, conocer a Dialga y viajar a la época turdetana.

Notación: `▶` es una caja de texto; `[ ]` son acciones o efectos; `NOMBRE`
es el nombre del jugador; `INICIAL` es el Pokémon elegido.

---

### Escena 1: el despertar (casa, piso alto)

[Tras el destello del sueño, pantalla en negro. Se oyen a lo lejos los toques
de guitarra del reloj. Fundido al cuarto del protagonista, en la cama.]

```
▶ .........
▶ ...Qué sueño más raro...
```
[Desde abajo:]

**MADRE:**
```
▶ ¡NOMBRE! ¡Que son las diez y media!
▶ ¡Ojú, qué criatura! ¡Ni el día de su
  cumpleaños se levanta temprano!
```

Objetos del cuarto:
- **Ventana:** `▶ El reloj de las Tendillas. Ya han dado las diez y media.`
- **Póster:** `▶ Un cartel de la Fiesta de los Patios. Las macetas azules llenan las paredes blancas.`
- **PC:** guarda una Poción (como en FireRed).
- **Estantería:** `▶ "Leyendas de Córdoba". Hay una página doblada: "El lago bajo la plaza".`

[Al bajar las escaleras:]

**MADRE** (exagerada, cariñosa y un poco mandona; expresiones cordobesas):
```
▶ ¡Mira quién baja! ¡La persona más
  dormilona de toda Córdoba!
▶ Anda, ven aquí, que te dé un beso.
  ¡Feliz cumpleaños!
▶ He ido a por tejeringos a la plaza...
  ...pero ya están fríos. Eso te pasa
  por dormir tanto.
▶ El Profesor Acisclo ha llamado tres
  veces. ¡Tres! Ese hombre no tiene
  paciencia ninguna.
▶ Y Chalo ha salido de su casa a las
  ocho. Lo he visto desde el balcón,
  dando saltitos como un saltamontes.
▶ Toma, mi regalo: unas zapatillas
  nuevas. Para que corras detrás de
  los Pokémon y no del autobús.
      [Recibe ZAPATILLAS DE DEPORTE]
▶ ¡Y llévate una chaqueta, que en mayo
  por la mañana refresca!
▶ ...Bueno, haz lo que quieras, que ya
  eres mayor. ¡Ea, a la calle!
```
*(Tejeringos: así se llaman los churros en Córdoba.)*

---

### Escena 2: la Plaza de las Tendillas

[La plaza con el reloj, la fuente con la estatua de bronce de Dialga (en lugar de la del Gran Capitán; nadie sabe qué Pokémon es), terrazas y
gente paseando. Suena la guitarra del reloj: son las diez.]

**Vecinos de la plaza (opcionales):**
- **Señora con macetas:** `▶ ¡Estamos montando la Cruz de Mayo en la calle de al lado! Este año la vamos a llenar de claveles.`
- **Turista:** `▶ ¿Ese reloj toca guitarra flamenca? ¡En mi ciudad solo hacen "dong"!`
- **Abuelo en un banco:** `▶ Dicen que debajo de esta plaza hay un lago. Mi padre decía que lo oía correr por las noches...`
- **Niño junto a la estatua:** `▶ ¡Esa estatua es de un Pokémon legendario! Mi abuela dice que vigila el reloj para que nunca se pare.`

**EL RELOJERO** (junto a la puertecita de la torre del reloj; amable, todavía
sin nombre):
```
▶ Buenos días. ¿Te gusta el reloj?
▶ Llevo media vida cuidándolo. Cada
  pieza, cada engranaje...
▶ El tiempo es lo más valioso que
  tenemos. Y lo más cruel.
▶ Bah, no me hagas caso. ¡Que tengas
  un buen día!
```
*(El jugador no lo sabe, pero es el líder del Equipo Olvido.)*

**CHALO** (junto a la estatua; da saltitos):
```
▶ ¡NOMBRE! ¡Por fin! ¡Llevo aquí desde
  las ocho!
▶ ¿Sabes qué día es hoy? ¡Nuestro primer
  Pokémon!
▶ Yo ya lo tengo decidido. Bueno, más o
  menos. Bueno, no.
▶ ¡Venga, vamos al lago, que el Profesor
  nos espera!
      [Chalo sale corriendo hacia la calle de la puerta]
```

**Bloqueo:** si el jugador intenta salir del barrio, un **guardia urbano**
le corta el paso:
`▶ Sin Pokémon no se sale del centro, ¿eh? Que hay mucho Pokémon salvaje por ahí fuera.`

---

### Escena 3: la bajada al lago

[En una calle junto a la plaza hay una puerta de madera antigua con una placa:
"Laboratorio de Investigación Pokémon. Prof. Acisclo".]

[Escaleras de piedra que bajan. Se oye el agua. Al llegar: una cueva amplia
con un **lago de agua quieta y oscura**, **columnas y sillares romanos** a
medio enterrar y, sobre una plataforma de madera, el laboratorio del Profesor
con mesas, ordenadores y frascos con muestras de agua.]

**AYUDANTE DEL PROFESOR** (en la entrada):
```
▶ ¡Hola! Cuidado con los escalones,
  que resbalan.
▶ Estas piedras son del foro de la
  Córdoba romana. ¡Tienen 2000 años!
```

**PROFESOR ACISCLO:**
```
▶ ¡Ah, NOMBRE! ¡Feliz cumpleaños!
▶ Te doy la bienvenida a mi laboratorio.
  Impresiona, ¿verdad?
▶ Todo el mundo cree que el lago de las
  Tendillas es una leyenda.
▶ Pues aquí lo tienes. Agua que lleva
  siglos bajo la ciudad.
▶ Yo creo que esta agua guarda la
  memoria de Córdoba.
▶ Romanos, califas, poetas... Todos
  bebieron de ella.
▶ Pero bueno, ¡no habéis venido a oír
  las batallitas de un viejo!
▶ Ahí, junto a la orilla, hay tres
  Pokémon. Cada uno tiene algo de
  nuestra ciudad.
▶ NOMBRE, como es tu cumpleaños, eliges
  tú primero.
```

**Los tres pedestales junto al agua.** Al mirar cada uno, el Profesor cuenta
su historia:

**Mudbray:**
```
▶ Mudbray, de tipo Tierra.
▶ Córdoba es tierra de caballos. Las
  Caballerizas Reales se fundaron en
  1570, y de ahí salió el caballo de
  pura raza española.
▶ Es terco, pero fiel como pocos.
▶ ¿Te quedas con Mudbray?   [SÍ / NO]
```

**Fuecoco:**
```
▶ Fuecoco, de tipo Fuego.
▶ ¿Conoces el caimán del Santuario de
  la Fuensanta? Lleva siglos colgado
  allí, y cada uno cuenta su leyenda.
▶ Pues este pequeñajo es igual de
  famoso... ¡y bastante más tragón!
▶ ¿Te quedas con Fuecoco?   [SÍ / NO]
```

**Flabébé:**
```
▶ Flabébé, de tipo Hada.
▶ En mayo, Córdoba llena sus patios
  de flores. Es nuestra fiesta más
  bonita.
▶ Flabébé nunca se separa de su flor.
  La cuida como una abuela cuida sus
  macetas.
▶ ¿Te quedas con Flabébé?   [SÍ / NO]
```

[Al elegir:] `▶ ¡NOMBRE ha recibido a INICIAL!` (opción de ponerle mote)

**CHALO** coge el que mejor aguanta al tuyo:
```
▶ ¡Pues yo me quedo con este!
      [Chalo coge su inicial]
▶ ¡Ja! ¡Mira qué bien nos llevamos ya!
```

---

### Escena 4: primer combate (a la orilla del lago)

**CHALO:**
```
▶ ¡NOMBRE! ¡Vamos a probarlos!
▶ ¡Mi primer combate tiene que ser
  contra ti!
```
[Combate. INICIAL nivel 5 contra el inicial de Chalo nivel 5.]

**Si ganas:** `▶ ¡Uf! ¡Vale, vale! ¡La próxima vez te gano yo!`
**Si pierdes:** `▶ ¡Toma! ¡Bueno, tampoco te lo tomes a mal! ¡Ha sido suerte!`
(Como en FireRed, el juego continúa ganes o pierdas.)

**PROFESOR ACISCLO:**
```
▶ ¡Magnífico combate!
▶ Tomad, una Pokédex para cada uno.
  Registra cada Pokémon que veas.
      [Recibe POKÉDEX]
      [Recibe 5 POKÉ BALLS]
▶ Y ahora, a la calle. ¡Córdoba está
  llena de Pokémon esperando!
```
**CHALO:** `▶ ¡Voy a registrar más Pokémon que tú! ¡Nos vemos arriba!` [sale]

---

### Escena 5: el reloj que sonó al revés

[Al salir a la plaza. Es casi mediodía. El relojero ya no está en su puerta.
El reloj marca las 12...]

[En vez de la guitarra normal, **la melodía suena al revés**. La pantalla se
vuelve azul y gris (los colores de Dialga). **Todos los personajes se quedan
congelados.** Un destello.]

[Vuelve el color. La gente sigue con su vida como si nada.]

**Vecinos tras el destello:**
- **Señora de las macetas:** `▶ ¿Has visto? Qué calor hace ya, ¿eh?` *(no ha notado nada)*
- **Abuelo del banco:** `▶ ...¿Has oído eso? El reloj... no, serán cosas mías.` *(lo ha notado a medias)*

**CHALO** (en la plaza, confundido):
```
▶ ¡NOMBRE! ¿Te pasa algo? Pones una
  cara muy rara.
▶ ¿El reloj? Ha tocado como siempre.
```

[En la calle Claudio Marcelo, donde debería estar el **Templo Romano**, solo
hay un solar vallado.]

**Peatón junto al solar:**
```
▶ ¿Un templo romano? ¿Aquí?
▶ Aquí siempre ha habido un solar, que
  yo recuerde.
```
**CHALO:**
```
▶ ¿Columnas? ¿Qué columnas? NOMBRE,
  ¿seguro que estás bien?
▶ ...Oye, que yo me voy a por Pokémon.
  ¡Descansa un poco, anda!
```

[El jugador vuelve al laboratorio del lago.]

[**El agua del lago corre en sentido contrario**, formando remolinos. Un
instante: en el reflejo aparece la **silueta de Dialga**. Desaparece.]

**PROFESOR ACISCLO:**
```
▶ ¡NOMBRE! Lo has visto, ¿verdad?
▶ ¿El Templo Romano ya no está?
▶ ...Y aun así tú lo recuerdas.
  Y yo también.
▶ Ya decía yo que esta agua guarda la
  memoria. Los que estábamos cerca del
  lago... no lo hemos olvidado.
▶ Algo está borrando el pasado de
  Córdoba. Y si se borra el pasado...
▶ ...lo que hay hoy tampoco tendrá por
  qué existir.
▶ Vuelve a casa y descansa. Esta noche
  vigilaré el lago.
```

---

### Escena 6: la noche (las Tendillas vacías)

> **Revisar:** tras el sueño, aquí el protagonista **reconoce la voz** ("...Esa voz... es la del sueño"),
> y es la primera vez que ve a Dialga. Quitar las menciones a los Engranajes cuando se decida el concepto nuevo.

[En casa, al irse a dormir. Fundido. **Noche.** El protagonista no puede
dormir; se oye el agua bajo el suelo.]

`▶ No puedes dormir. Algo te llama desde la plaza...`

[La plaza vacía, iluminada por las farolas. Dos figuras con un **emblema de
engranaje tachado** salen de la puerta de la torre del reloj.]

**RECLUTA DEL EQUIPO OLVIDO 1:**
`▶ ¡Rápido! El primer engranaje ya está en camino. El jefe dice que esta noche se abrirá del todo.`
**RECLUTA 2:**
`▶ ¡Eh! ¡Nos han visto! ¡Da igual, mañana nadie se acordará de nada!` [huyen]

[El reloj marca las 12 de la noche. Silencio total. Un resplandor azul sobre
la **estatua del Gran Capitán**: aparece **DIALGA**.]

**DIALGA** (habla en la mente del jugador; texto en otro color):
```
▶ ...Humano. Tú puedes oírme.
▶ Soy Dialga. Guardo el tiempo de este
  mundo.
▶ El tiempo de esta ciudad se deshace.
  Unos humanos roban mis Engranajes.
▶ Ocho fragmentos de mi poder,
  escondidos en ocho épocas de tu
  ciudad.
▶ Si los reúnen, podrán reescribir la
  historia a su antojo.
▶ Y la ciudad que conoces... dejará de
  haber existido.
▶ Yo no puedo entrar en el tiempo de
  los humanos. Tú sí.
▶ ¿Por qué tú? Porque tu historia
  empezó aquí...
▶ ...hace mucho más tiempo del que
  crees.
▶ Ve al lago. El agua te llevará.
      [Dialga desaparece en un destello]
```

---

### Escena 7: el salto

[El laboratorio del lago, de noche. El agua brilla con una luz azul.]

**PROFESOR ACISCLO:**
```
▶ ¡NOMBRE! ¿Tú también lo has sentido?
▶ El lago lleva un rato brillando. Como
  si esperase a alguien.
▶ ...Dialga. ¿Has hablado con Dialga?
▶ Entonces no hay tiempo que perder.
▶ Toma, este reloj de bolsillo. Era de
  mi abuelo.
▶ Lo hizo un relojero de las Tendillas,
  hace muchos años.
▶ Mientras lo lleves, el lago sabrá
  traerte de vuelta.
      [Recibe RELOJ DE BOLSILLO (objeto clave)]
▶ Ten cuidado, NOMBRE.
▶ Y sobre todo... no cambies nada que
  no debas cambiar.
```
*(Pista: el reloj lo fabricó la familia del relojero, el villano. Se aclarará
en el desenlace.)*

[El jugador entra en el agua. La pantalla ondula y se funde en blanco.]

**FIN DEL PRÓLOGO.** Continúa en el **Capítulo 1: Corduba, s. III a. C.**: el
protagonista despierta en lo alto de una colina, junto a un poblado turdetano
y un río enorme, el Guadalquivir, sin puentes.

---

### 5.1 Lo que necesita el prólogo (lista para la parte técnica)

**Mapas**
- [x] Casa del protagonista (planta alta y planta baja)
- [x] Plaza de las Tendillas con el reloj, la estatua (de Dialga, en lugar del Gran Capitán) y terrazas; la casa está en una calle al lado
- [ ] Calle Claudio Marcelo con el Templo Romano, en dos versiones: con templo y con solar
- [ ] Calle con la puerta del laboratorio (y la Cruz de Mayo de decoración)
- [ ] Laboratorio del lago subterráneo (cueva con agua, columnas romanas)
- [ ] Plaza de noche (paleta nocturna)

**Personajes (sprites de mapa)**
- [ ] Protagonista chico y chica (al principio se pueden reutilizar los de Unbound)
- [ ] Chalo · Profesor Acisclo · Madre · Relojero · Ayudante
- [ ] Reclutas del Equipo Olvido · vecinos (reutilizando los de Unbound)
- [ ] Dialga en el mapa (Unbound ya tiene un sprite para legendarios)

**Gráficos de combate:** Chalo (sprite de entrenador).

**Objetos:** Zapatillas de deporte (ya existen), Pokédex, Poké Balls,
Reloj de bolsillo (objeto clave nuevo; se puede reutilizar uno sin uso).

**Efectos:** tono azul y gris y personajes congelados (*flash* y cambio de
paleta, que FireRed ya hace en algunas escenas); agua del lago con remolinos;
música del reloj al revés.

**Pokémon:** Mudbray (966) y Flabébé (777) ya están en Unbound; **Fuecoco
hay que añadirlo** (huecos libres 254-276).
