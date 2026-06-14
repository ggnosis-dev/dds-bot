import json

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_DIR = PROJECT_ROOT / "databases"
DEMONS_DB_PATH = DATABASE_DIR / "demons.db"
PLAYERS_DB_PATH = DATABASE_DIR / "players.db"

DATA_DIR = PROJECT_ROOT / "data"
DEMONS_DIR = DATA_DIR / "demons"
ITEMS_JSON = DATA_DIR / "items.json"
FUSION_CSV = DATA_DIR / "fusion.csv"


def ensure_db_dir_exists() -> Path:
	"""
	Ensure the database directory exists, creating it if necessary.
	Returns:
		Path: The path to the database directory.
	"""
	DATABASE_DIR.mkdir(exist_ok=True)
	return DATABASE_DIR


def load_json(path: Path):
	with open(path) as data:
		return json.load(data)
