import json
import sqlite3

from database_paths import DEMONS_DIR, PLAYERS_DB_PATH, ensure_db_dir_exists
from shared_enums import GemList, Personality

ensure_db_dir_exists()

demon_data = []

for race_json in DEMONS_DIR.glob("*.json"):
	data = {}
	demon = {}
	race = race_json.name.capitalize()

	print(f"Adding {race} to database.")

	with open(race_json) as f:
		data = json.load(f)

	for entry in data:
		demon = (
			entry["name"],
			race,
			entry["rank"],
			int(entry["color"], 16),
			Personality[entry["personality"]].name,
			GemList[entry["gem"]].name,
			entry["image_url"],
		)

	demon_data.append(demon)

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# Delete existing demon table in case changes to general structure.
	cursor.execute("DROP TABLE IF EXISTS demons")

	# Create demon table.
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS demons (
			id INTEGER PRIMARY KEY,
			name TEXT,
			race TEXT,
			rank INTEGER,
			colour INTEGER,
			personality TEXT,
			gem TEXT,
			image_url TEXT
		)
	""")

	# Insert demon data.
	cursor.executemany(
		"""
		INSERT INTO demons (name, race, rank, colour, personality, gem, image_url)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	""",
		demon_data,
	)
