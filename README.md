# images_IABet

Este proyecto ofrece utilidades para manejar las imágenes utilizadas en IABet.

## Descarga de imágenes

El módulo `scripts/download_images.py` expone funciones que descargan las
imágenes de jugadores y logos de equipos sin guardarlas en disco:

- `fetch_player_image(player_id)`: devuelve los bytes de la foto del jugador.
- `fetch_team_logo(team_id, team_code)`: devuelve los bytes del logo del equipo.

Cada función intenta múltiples fuentes y, en caso de no lograr la descarga,
lanza una excepción para que la aplicación llamante decida cómo proceder.

## Generación de `players_id.json`

Para construir el archivo final `data/players_id.json` se partió de una plantilla
manual (`players_id copy.json`). Dicha plantilla se comparó con la lista de
nombres almacenada en `jugadores.txt` para obtener los identificadores
correctos y producir el archivo definitivo `players_id.json`.

