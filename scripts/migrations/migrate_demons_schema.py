import sqlite3

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

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

	cursor.execute("""
		INSERT INTO new_demons (
			id, name, race_id, rank, tone, personality, prevent_spawn, profile_img, encounter_img
		)
		SELECT
			d.id, d.name, r.id, d.rank, d.tone, d.personality, d.prevent_spawn, d.profile_img, d.encounter_img
		FROM demons d
		JOIN races r ON d.race = r.name
	""")

	cursor.execute("DROP TABLE demons")
	cursor.execute("ALTER TABLE new_demons RENAME TO demons")
