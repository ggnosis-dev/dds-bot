import sqlite3

from time import time

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute("""
		ALTER TABLE player_demons
		ADD COLUMN date_met INTEGER
	""")

	cursor.execute(
		"""
		UPDATE player_demons
		SET date_met = ?
		WHERE date_met IS NULL
	""",
		(int(time()),),
	)
