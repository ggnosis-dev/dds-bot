import sqlite3

from database_paths import PLAYERS_DB_PATH, ensure_db_dir_exists


ensure_db_dir_exists()

# https://www.sqlitetutorial.net/sqlite-json/
with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS players (
			player_id 		INTEGER,
			server_id 		INTEGER,
			CONSTRAINT player_server_id PRIMARY KEY (player_id, server_id)
		)
	''')

	cursor.execute('''		   
		CREATE TABLE IF NOT EXISTS player_demons (
			player_id 		INTEGER,
			server_id 		INTEGER,
			demon_id		INTEGER,
			stored_rank		INTEGER,
			in_party		INTEGER CHECK (in_party IN (0, 1)),
			UNIQUE(player_id, server_id, demon_id)
		)
	''')

	cursor.execute('''
		CREATE TABLE IF NOT EXISTS player_gems (
			player_id 		INTEGER,
			server_id 		INTEGER,
			gem_name		TEXT,
			meter			INTEGER,
			quantity		INTEGER,
			UNIQUE(player_id, server_id, gem_name)
		)
	''')

	# Index for faster lookup of player's parties and compendiums.
	cursor.execute('''
		CREATE INDEX IF NOT EXISTS idx_player_demons ON player_demons(player_id, server_id)
	''')

	# TESTS:
	# cursor.execute('DELETE FROM players')
	# cursor.execute('DELETE FROM player_demons')
	# cursor.execute('UPDATE player_demons SET in_party = 0')
