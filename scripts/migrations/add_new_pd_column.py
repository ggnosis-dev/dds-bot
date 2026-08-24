import sqlite3

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute("""
		ALTER TABLE player_demons
		ADD COLUMN dupes INTEGER DEFAULT 0
	""")

	cursor.execute("""
		ALTER TABLE player_demons
		ADD COLUMN colour INTEGER DEFAULT NULL
	""")

	cursor.execute("""
		ALTER TABLE player_demons
		ADD COLUMN greeting TEXT DEFAULT NULL
	""")
