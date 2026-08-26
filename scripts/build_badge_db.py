import json
import sqlite3

from database_paths import DEMONS_DIR, PLAYERS_DB_PATH

badge_data = []

for race_json in DEMONS_DIR.glob("*.json"):
	data = {}
	race = race_json.stem.capitalize()

	print(f"Adding {race} to badge database.")

	with open(race_json) as f:
		data = json.load(f)

	for entry in data:
		badge = (
			entry.get("badge_id", None),
			entry["name"].lower(),
			entry["name"],
		)

		badge_data.append(badge)

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute("DROP TABLE IF EXISTS badges")
	cursor.execute("DROP TABLE IF EXISTS player_badges")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS badges (
			id			INTEGER PRIMARY KEY,
			emote_id	INTEGER NOT NULL,
			name		TEXT NOT NULL,
			-- Demon ID is nullable as we can have special types of badges.
			demon_id	INTEGER,
			FOREIGN KEY (demon_id) REFERENCES demons(id),
			UNIQUE (demon_id, emote_id)
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS player_badges (
			player_id 	INTEGER NOT NULL,
			badge_id	INTEGER NOT NULL,
			FOREIGN KEY (badge_id) REFERENCES badges(id),
			UNIQUE (player_id, badge_id)
		)
	""")

	cursor.executemany(
		"""
			INSERT OR IGNORE INTO badges
				(demon_id, emote_id, name)
			SELECT id, ?, ?
			FROM demons
			WHERE name = ?
		""",
		(badge_data),
	)

	cursor.execute("""INSERT OR IGNORE INTO badges (emote_id, name) VALUES (?, ?)""", (1524641172356730880, "kn"))
