from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_DIR = PROJECT_ROOT / "databases"
DEMONS_DIR = DATABASE_DIR / "demons"
DEMONS_DB_PATH = DATABASE_DIR / "demons.db"
PLAYERS_DB_PATH = DATABASE_DIR / "players.db"
FUSION_CSV_PATH = DATABASE_DIR / "fusion.csv"


def ensure_db_dir_exists() -> Path:
	"""
	Ensure the database directory exists, creating it if necessary.
	Returns:
		Path: The path to the database directory.
	"""
	DATABASE_DIR.mkdir(exist_ok=True)
	return DATABASE_DIR
