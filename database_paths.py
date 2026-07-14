import json

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_DIR = PROJECT_ROOT / "databases"
DEMONS_DB_PATH = DATABASE_DIR / "demons.db"
PLAYERS_DB_PATH = DATABASE_DIR / "players.db"

DATA_DIR = PROJECT_ROOT / "data"
DEMONS_DIR = DATA_DIR / "demons"

ITEMS_JSON = DATA_DIR / "items.json"
SPECIAL_FUSION_JSON = DATA_DIR / "special_fusions.json"
TALK_JSON = DATA_DIR / "talk.json"
RACE_GEMS_JSON = DATA_DIR / "race_gems.json"
FUSION_CSV = DATA_DIR / "fusion.csv"


def load_json(path: Path):
	with open(path) as data:
		return json.load(data)
