import json
import os
import argparse
from pathlib import Path

from nba_api.stats.endpoints import commonteamroster

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PLAYERS_JSON = DATA_DIR / "players_id.json"
TEAMS_JSON = DATA_DIR / "teams_id.json"

def fetch_team_roster(team_id: int, season: str):
    try:
        # Aquí ya puede saltar KeyError("Coaches") dentro de __init__ o get_request()
        endpoint = commonteamroster.CommonTeamRoster(team_id=team_id, season=season)
    except KeyError:
        # Si la API ya no incluye “Coaches”, devolvemos un roster vacío
        return []

    # Si llegamos aquí, la instancia fue exitosa
    data = endpoint.get_normalized_dict()
    return data.get("CommonTeamRoster", [])

def build_rosters(season: str):
    with open(TEAMS_JSON, "r", encoding="utf-8") as f:
        teams = json.load(f)

    rosters = {}
    used_ids = set()
    duplicates = []

    for abbr, info in teams.items():
        roster_data = fetch_team_roster(info["id"], season)
        players = []
        for player in roster_data:
            player_id = player["PLAYER_ID"]
            if player_id in used_ids:
                duplicates.append(player_id)
                continue
            used_ids.add(player_id)
            players.append({
                "id": player_id,
                "nombre": player["PLAYER"],
                "dorsal": player["NUM"],
                "posicion": player["POSITION"]
            })
        rosters[abbr] = {
            "nombre_completo": info["nombre"],
            "jugadores": players
        }

    return rosters, duplicates


def main():
    parser = argparse.ArgumentParser(description="Update players_id.json from NBA API")
    parser.add_argument("--season", default="2025-26", help="Season string, e.g. 2025-26")
    args = parser.parse_args()

    rosters, duplicates = build_rosters(args.season)

    with open(PLAYERS_JSON, "w", encoding="utf-8") as f:
        json.dump(rosters, f, indent=2, ensure_ascii=False)

    if duplicates:
        print("Duplicated IDs detected:", duplicates)


if __name__ == "__main__":
    main()
