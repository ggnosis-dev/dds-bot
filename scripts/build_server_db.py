import sqlite3

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# cursor.execute("DROP TABLE IF EXISTS servers")
	# cursor.execute("DROP TABLE IF EXISTS server_demons")
	# cursor.execute("DROP TABLE IF EXISTS server_unlocks")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS servers (
			server_id			INTEGER PRIMARY KEY,
			player_count		INTEGER DEFAULT 1,
			dedicated_channel	INTEGER,
			server_level		INTEGER DEFAULT 1,
			server_level_xp 	INTEGER DEFAULT 0,
			-- Rank cap is upper bound of what a player can spawn.
			rank_cap			INTEGER DEFAULT 5
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS server_demons (
			server_id		INTEGER NOT NULL,
			player_id		INTEGER NOT NULL,
			demon_id		INTEGER NOT NULL,
			PRIMARY KEY 	(server_id, demon_id),
			FOREIGN KEY 	(server_id)
				REFERENCES 	servers (server_id),
			-- A demon doesn't exist in server_demons in the usual sense, it's a reference pointing to player_demons.
			FOREIGN KEY 	(player_id, server_id, demon_id)
				REFERENCES 	player_demons (player_id, server_id, demon_id)
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS server_unlocks (
			-- Small relational table to keep track of what has been unlocked.
			server_id		INTEGER NOT NULL,
			unlock_key		TEXT NOT NULL,
			PRIMARY KEY (server_id, unlock_key)
		)
	""")
