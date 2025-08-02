# images_IABet

This project stores NBA team and player IDs and provides scripts to download player photos and team logos.

## Requirements
Install dependencies with:

```bash
pip install -r requirements.txt
```

## Offseason Changes
Generate a list of players who joined a new franchise during the 2025 offseason
and refresh `players_id.json` with:

```bash
python scripts/generate_roster_diff.py
```

The script creates `data/roster_diff_2025_offseason.json` and rewrites
`data/players_id.json` with up-to-date rosters.

## Updating Rosters
Use `scripts/update_roster.py` to refresh `data/players_id.json` with official rosters from the NBA API.
If the API does not yet expose a roster for the requested season, the script
keeps the previously stored players so existing data is not lost.

```bash
python scripts/update_roster.py --season 2025-26
```

This script writes the updated data to `data/players_id.json` and warns about any duplicated player IDs.

## Downloading Images
After updating rosters, run `scripts/download_images.py` to download the latest player photos and team logos.

```bash
python scripts/download_images.py
```
