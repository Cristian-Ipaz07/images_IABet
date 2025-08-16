from __future__ import annotations

import time
import json
from typing import Optional, Iterable, Dict, Any
from pathlib import Path

import requests
from unidecode import unidecode

# ---------------------------------------------
# Configuración (sin efectos en disco)
# ---------------------------------------------

# Solo necesitas estas rutas si vas a cargar los JSON de IDs.
# Si prefieres, pásalos como dicts a las funciones públicas.
BASE_DIR = Path(r"F:\Programacion\DESARROLLADOR PROFESIONAL\IABet\images_IABet")
PLAYERS_JSON = BASE_DIR / "data" / "players_id.json"
LOGOS_JSON = BASE_DIR / "data" / "teams_id.json"

DELAY_BETWEEN_PLAYERS = 1.5
MAX_RETRIES = 3
TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.nba.com/",
}

PLAYER_URLS = [
    "https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png",
    "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png",
]

LOGO_URLS = [
    # NBA CDN (PNG)
    "https://cdn.nba.com/logos/nba/{team_id}/primary/D/logo.png",
    # ESPN (PNG)
    "https://a.espncdn.com/i/teamlogos/nba/500/{team_code}.png",
    # NBA CDN alternativa (PNG)
    "https://cdn.nba.com/logos/nba/{team_id}/global/D/logo.png",
    # Variante SVG (algunas franquicias)
    "https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg",
]

# ---------------------------------------------
# Utilidades
# ---------------------------------------------

def _http_get_bytes(url: str, timeout: int = TIMEOUT) -> Optional[bytes]:
    """Devuelve bytes del recurso o None si falla."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200 and resp.content and len(resp.content) > 1000:
            return resp.content
    except Exception:
        pass
    return None


def _safe_name(name: str) -> str:
    """Normaliza el nombre para usarlo como clave/filename (si hiciera falta)."""
    return (
        unidecode(name)
        .replace(" ", "_")
        .replace("'", "")
        .replace("-", "_")
        .strip()
    )


# ---------------------------------------------
# Funciones públicas (NO escriben en disco)
# ---------------------------------------------

def fetch_player_image(player_id: int | str, *, retries: int = MAX_RETRIES, delay: float = DELAY_BETWEEN_PLAYERS) -> Optional[bytes]:
    """
    Devuelve los bytes de la foto del jugador (PNG) o None si no se pudo.
    No guarda archivos, no crea carpetas.
    """
    for attempt in range(retries):
        for template in PLAYER_URLS:
            url = template.format(player_id=player_id)
            data = _http_get_bytes(url)
            if data:
                return data
        # backoff simple entre reintentos
        time.sleep(delay * (attempt + 1))
    return None


def fetch_team_logo(team_id: int | str, team_code: str, *, timeout: int = TIMEOUT) -> Optional[bytes]:
    """
    Devuelve los bytes del logo del equipo.
    Si la URL es SVG e incluye contenido SVG, intenta convertir a PNG en memoria (opcional).
    """
    for template in LOGO_URLS:
        url = template.format(team_id=team_id, team_code=team_code)
        data = _http_get_bytes(url, timeout=timeout)
        if not data:
            continue

        # Si parece SVG, intenta convertir a PNG (recomendado para uso homogéneo)
        if data[:100].lstrip().startswith(b"<") and b"<svg" in data[:400].lower():
            try:
                import cairosvg  # asegúrate de incluir 'cairosvg' en requirements.txt
                png_bytes = cairosvg.svg2png(bytestring=data)
                if png_bytes and len(png_bytes) > 1000:
                    return png_bytes
            except Exception:
                # Si falla la conversión, devuelve el SVG original por si el consumidor lo acepta
                return data
        else:
            return data

    return None


# ---------------------------------------------
# Funciones de “batch” que devuelven resultados en memoria
# ---------------------------------------------

def load_players_data(path: Path = PLAYERS_JSON) -> Dict[str, Any]:
    """Carga y retorna el dict de jugadores por equipo desde JSON (en memoria)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_logos_data(path: Path = LOGOS_JSON) -> Dict[str, Any]:
    """Carga y retorna el dict con metadatos de equipos (ids, etc.)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_team_players_images(
    equipo_abrev: str,
    equipo_data: Dict[str, Any],
    *,
    retries: int = MAX_RETRIES,
    delay: float = DELAY_BETWEEN_PLAYERS,
) -> Dict[str, Optional[bytes]]:
    """
    Devuelve un dict {nombre_normalizado: bytes|None} con las fotos de los jugadores del equipo.
    No escribe en disco.
    """
    results: Dict[str, Optional[bytes]] = {}
    for jugador in equipo_data.get("jugadores", []):
        player_id = jugador["id"]
        nombre = jugador["nombre"]
        key = _safe_name(nombre)
        results[key] = fetch_player_image(player_id, retries=retries, delay=delay)
    return results


def fetch_everything_in_memory(
    players_data: Dict[str, Any],
    logos_data: Dict[str, Any],
    equipos_a_descargar: Iterable[str] | None = None,
    equipos_a_excluir: Iterable[str] | None = None,
    solo_logos: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Recorre equipos **en memoria** y devuelve un resumen con bytes:
    {
      'LAL': {
          'logo': b'...',            # bytes o None
          'jugadores': {'LeBron_James': b'...', ...}  # si solo_logos=False
      },
      ...
    }
    """
    equipos_a_descargar = set(equipos_a_descargar or [])
    equipos_a_excluir = set(equipos_a_excluir or [])

    out: Dict[str, Dict[str, Any]] = {}

    for equipo_abrev, equipo_data in players_data.items():
        if equipos_a_excluir and equipo_abrev in equipos_a_excluir:
            continue
        if equipos_a_descargar and equipo_abrev not in equipos_a_descargar:
            continue

        # logo
        team_meta = logos_data.get(equipo_abrev, {})
        team_id = team_meta.get("id")
        logo_bytes = None
        if team_id is not None:
            logo_bytes = fetch_team_logo(team_id=team_id, team_code=equipo_abrev)

        entry: Dict[str, Any] = {"logo": logo_bytes}

        # jugadores
        if not solo_logos:
            entry["jugadores"] = fetch_team_players_images(equipo_abrev, equipo_data)

        out[equipo_abrev] = entry

    return out

# Nota: NO hay bloque if __name__ == "__main__":  -> al importar no hace nada.
