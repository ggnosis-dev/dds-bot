import sqlite3

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute("DROP TABLE IF EXISTS factions")
	cursor.execute("DROP TABLE IF EXISTS faction_unlocks")

	# cursor.execute("""
	# 	CREATE TABLE IF NOT EXISTS factions (
	# 		server_id			INTEGER NOT NULL,
	# 		-- faction_id also helps determine the alignment type.
	# 		faction_id			INTEGER NOT NULL,
	# 		name				TEXT NOT NULL,
	# 		member_count		INTEGER DEFAULT 0,
	# 		level				INTEGER DEFAULT 1,
	# 		level_xp			INTEGER DEFAULT 0,
	# 		rank_cap			INTEGER DEFAULT 10,
	# 		PRIMARY KEY (server_id, faction_id),
	# 		-- Names in servers should be unique.
	# 		UNIQUE (server_id, name)
	# 	)
	# """)

	# cursor.execute("""
	# 	CREATE TABLE IF NOT EXISTS faction_unlocks (
	# 		-- Small relational table to keep track of what has been unlocked.
	# 		server_id		INTEGER NOT NULL,
	# 		faction_id		INTEGER NOT NULL,
	# 		unlock_key		TEXT NOT NULL,
	# 		PRIMARY KEY (server_id, faction_id, unlock_key)
	# 	)
	# """)
