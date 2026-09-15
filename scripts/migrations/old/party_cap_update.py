import sqlite3

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute("""
		UPDATE players
		SET party_cap = party_cap - 5
	""")
