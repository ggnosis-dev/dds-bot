import json
import sqlite3

from database_paths import DEMONS_DIR, PLAYERS_DB_PATH
from shared_enums import Personality, Race, Tone

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
		race_id = Race[entry.get("race")].value
		pers_id = Personality[entry.get("personality", "NONE")].value
		tone_id = Tone[entry.get("tone", "NONE")].value

		demon = (
			entry["name"],
			race_id,
			entry["rank"],
			int(entry["color"], 16),
			pers_id,
			entry["profile_url"],
			image_url,
			prevent_spawn,
			tone_id,
		)

		demon_data.append(demon)

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# Delete existing demon table in case changes to general structure.
	# cursor.execute("DROP TABLE IF EXISTS demons")
	# cursor.execute("DELETE FROM demons WHERE name LIKE 'Jack%'")

	# Create demon table.
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS new_demons (
			id INTEGER PRIMARY KEY,
			name TEXT NOT NULL,
			race_id INTEGER NOT NULL,
			rank INTEGER NOT NULL,
			tone INTEGER NOT NULL,
			personality INTEGER NOT NULL,
			prevent_spawn INTEGER DEFAULT 0,
			profile_img TEXT,
			encounter_img TEXT,
			UNIQUE (race_id, name)
			FOREIGN KEY (race_id) REFERENCES races (id)
		)
	""")

	# Insert demon data.
	cursor.executemany(
		"""
			INSERT OR IGNORE INTO demons
				(name, race_id, rank, tone, personality, prevent_spawn, profile_img, encounter_img)
			VALUES
				(?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(name, race_id) DO UPDATE SET
				rank = excluded.rank,
				tone = excluded.tone,
				personality = excluded.personality,
				prevent_spawn = excluded.prevent_spawn,
				profile_img = excluded.profile_img,
				encounter_img = excluded.encounter_img
		""",
		demon_data,
	)
