"""
Generates `roster_diff_2025_offseason.json` with all players who landed on a new
NBA franchise during the 2025 offseason (15 Jun – 31 Jul). The script also
refreshes `data/players_id.json` using official NBA API rosters, removing any
duplicate player IDs in the process.

Requirements:
    pip install requests beautifulsoup4 nba_api unidecode
"""

import json
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from nba_api.stats.static import players
from unidecode import unidecode

# URLs tracking trades, free-agent signings, and draft picks
TRADE_URL = "https://www.nba.com/news/2025-offseason-trade-tracker"
FA_URL = "https://www.nba.com/news/nba-offseason-deals-2025"
DRAFT_URL = "https://www.nba.com/news/2025-draft-results-picks-1-59"

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ROSTER_DIFF_JSON = DATA_DIR / "roster_diff_2025_offseason.json"


def clean(name: str) -> str:
    """Normalize names for comparison with nba_api."""
    return unidecode(name.strip()).lower()


def player_id_lookup(name: str):
    """Return NBA player ID for a given name using nba_api."""
    hits = [p for p in players.get_players() if clean(p["full_name"]) == clean(name)]
    if not hits:
        tokens = clean(name).split()
        core = " ".join(tokens[:2])
        hits = [p for p in players.get_players() if clean(p["full_name"]).startswith(core)]
    return hits[0]["id"] if hits else None


def scrape_trade_tracker():
    soup = BeautifulSoup(requests.get(TRADE_URL, timeout=15).text, "html.parser")
    names = re.findall(r"•\s([A-ZÁÉÍÓÚÄÖÜÂÊÎÔÛÀÈÌÒÙa-z'\.\-]+\s[A-Z][a-z]+)", soup.get_text())
    return set(n for n in names if n.lower() not in ["official", "related"])


def scrape_fa_additions():
    soup = BeautifulSoup(requests.get(FA_URL, timeout=15).text, "html.parser")
    text = soup.get_text()
    teams_blocks = re.split(r"\* \* \*", text)
    additions = set()
    for block in teams_blocks:
        if "Additions" in block:
            additions.update(
                re.findall(r"•\s([A-Z][\w\.' -]+?)\s(?:agrees|joins|arrives)", block)
            )
    return additions


def scrape_draft():
    soup = BeautifulSoup(requests.get(DRAFT_URL, timeout=15).text, "html.parser")
    picks = re.findall(r"\d+\.\s(.+?)\s+—?\s?(?:Draft|–)", soup.get_text())
    ids = re.findall(r'"player_id":\s?(\d+)', soup.get_text())
    return {name: int(pid) for name, pid in zip(picks, ids)}


def build_roster_diff():
    trade_names = scrape_trade_tracker()
    fa_names = scrape_fa_additions()
    draft_map = scrape_draft()

    veterans = trade_names.union(fa_names)
    roster = []

    for name in sorted(veterans):
        pid = player_id_lookup(name)
        if pid:
            roster.append({"id": pid, "name": name})
        else:
            print(f"[WARN] sin id: {name}")

    for name, pid in draft_map.items():
        roster.append({"id": pid, "name": name, "rookie": True})

    with open(ROSTER_DIFF_JSON, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    print(
        f"Total jugadores nuevos: {len(roster)}  →  {ROSTER_DIFF_JSON.name}"
    )


def refresh_players_json(season: str = "2025-26"):
    from update_roster import build_rosters, PLAYERS_JSON

    rosters, duplicates = build_rosters(season)
    with open(PLAYERS_JSON, "w", encoding="utf-8") as f:
        json.dump(rosters, f, indent=2, ensure_ascii=False)
    if duplicates:
        print("Duplicated IDs detected:", duplicates)


if __name__ == "__main__":
    build_roster_diff()
    refresh_players_json()
