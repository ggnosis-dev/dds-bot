import json
import sqlite3

from database_paths import DEMONS_DIR, PLAYERS_DB_PATH
from shared_enums import GemList, Personality

demon_data = []

for race_json in DEMONS_DIR.glob("*.json"):
	data = {}
	demon = {}
	race = race_json.stem.capitalize()

	print(f"Adding {race} to database.")

	with open(race_json) as f:
		data = json.load(f)

	for entry in data:
		prevent_spawn = bool(entry.get("prevent_spawn", False))
		image_url = entry.get("image_url", None)

		demon = (
			entry["name"],
			race,
			entry["rank"],
			int(entry["color"], 16),
			Personality[entry["personality"]].name,
			GemList[entry["gem"]].name,
			entry["profile_url"],
			image_url,
			prevent_spawn,
		)

		demon_data.append(demon)

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# Delete existing demon table in case changes to general structure.
	# cursor.execute("DROP TABLE IF EXISTS demons")
	# cursor.execute("DELETE FROM demons WHERE name LIKE 'Jack%'")

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
			profile_url TEXT,
			image_url TEXT,
			prevent_spawn INTEGER DEFAULT 0,
			UNIQUE (race, name)
		)
	""")

	# Insert demon data.
	cursor.executemany(
		"""
			INSERT OR IGNORE INTO demons (name, race, rank, colour, personality, gem, profile_url, image_url, prevent_spawn)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(race, name) DO UPDATE SET
				rank = excluded.rank,
				colour = excluded.colour,
				personality = excluded.personality,
				gem = excluded.gem,
				profile_url = excluded.profile_url,
				image_url = excluded.image_url,
				prevent_spawn = excluded.prevent_spawn
		""",
		demon_data,
	)
