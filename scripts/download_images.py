"""Utility functions to fetch NBA player headshots and team logos.

Each function returns the image bytes so that callers can handle the
content as needed without writing temporary files.
"""

from __future__ import annotations

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.nba.com/",
}

PLAYER_URLS = [
    "https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png",
    "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png",
]

LOGO_URLS = [
    "https://cdn.nba.com/logos/nba/{team_id}/primary/D/logo.png",
    "https://a.espncdn.com/i/teamlogos/nba/500/{team_code}.png",
    "https://cdn.nba.com/logos/nba/{team_id}/global/D/logo.png",
    "https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg",
]

TIMEOUT = 15


def fetch_player_image(player_id: str) -> bytes:
    """Return the headshot image for the given player.

    Raises:
        ValueError: if none of the candidate URLs provided a valid image.
    """

    for url_template in PLAYER_URLS:
        url = url_template.format(player_id=player_id)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content
        except requests.RequestException:
            continue
    raise ValueError(f"No se pudo descargar imagen para jugador {player_id}")


def fetch_team_logo(team_id: str, team_code: str) -> bytes:
    """Return the logo for the given team.

    For "NOP" (New Orleans Pelicans) a special URL is tried first to obtain an
    SVG that callers can convertir a PNG u otro formato.

    Raises:
        ValueError: if none of the candidate URLs provided a valid logo.
    """

    if team_code == "NOP":
        special_url = "https://cdn.nba.com/logos/nba/1610612740/global/L/logo.svg"
        try:
            resp = requests.get(special_url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.content
        except requests.RequestException:
            pass

    for url_template in LOGO_URLS:
        url = url_template.format(team_id=team_id, team_code=team_code)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 1024:
                return resp.content
        except requests.RequestException:
            continue
    raise ValueError(f"No se pudo descargar logo para equipo {team_code}")

