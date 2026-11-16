# Estados guardados del emulador (mGBA)

Para no tener que jugar desde el principio cada vez que se prueba algo, se guardan
**estados** (fotos completas de la memoria de la consola) en puntos clave del capítulo 0.
mGBA los guarda junto a la ROM como `MiHack.ss1` … `MiHack.ss9`.

* **Cargar**: F1 … F9   ·   **Guardar**: Mayús + F1 … F9
* Para saber dónde está cada uno: `python scripts/analisis/ver_estados.py`
  (y `scripts/analisis/donde.py` dice la casilla exacta de cada personaje).

| Ranura | Punto de la historia |
|---|---|
| 1 | Pantalla de título ("PULSA START") |
| 2 | Sueño: el reflejo en el agua (elegir chico/chica) |
| 3 | Sueño: pantalla del nombre |
| 4 | Despertar en la cama (cuarto, mapa 4.1) |
| 5 | Planta baja, empieza la escena de Mamá (mapa 4.0) |
| 6 | Planta baja, después de la escena (zapatillas recibidas, var 0x5011 = 3) |
| 7 | Calle de la casa, recién salido por la puerta (mapa 3.0, Tendillas, versión 3) |
| 8 | Plaza de las Tendillas, al lado de Chalo mirándolo (antes de hablar con él) |
| 9 | temporal (lo usa Claude para leer posiciones durante las pruebas) |

**Ojo (para clase):** un estado guarda la RAM, no la ROM. Si se cambian los eventos de un
mapa, el estado cargado *dentro* de ese mapa sigue usando la copia vieja que ya estaba en
memoria: hay que salir del mapa y volver a entrar (o usar un estado anterior) para ver el cambio.
Y después de modificar la ROM hay que **cerrar y abrir** mGBA (Ctrl+R no recarga el archivo).

Si se vuelve a ejecutar `scripts/tendillas/escribir.py`, los estados 7 y 8 (dentro de la plaza)
pueden quedarse con datos viejos: lo seguro es cargar el 6 y salir por la puerta.
