import sqlite3

from database_paths import PLAYERS_DB_PATH, ensure_db_dir_exists

ensure_db_dir_exists()

# https://www.sqlitetutorial.net/sqlite-json/
with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# TESTS:
	cursor.execute("DROP TABLE IF EXISTS players")
	# cursor.execute("DROP TABLE IF EXISTS player_demons")
	# cursor.execute('DROP TABLE IF EXISTS player_gems')
	# cursor.execute('DROP TABLE IF EXISTS player_items')

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS players (
			player_id 			INTEGER,
			server_id 			INTEGER,
			selected_demon_id	INTEGER DEFAULT 1,
			mag 				INTEGER DEFAULT 0,
			party_size			INTEGER DEFAULT 0,
			party_cap			INTEGER DEFAULT 10,
			party_average_rank	INTEGER DEFAULT 0,
			daily_timer			INTEGER DEFAULT 0,
			encounter_timer		INTEGER DEFAULT 0,
			PRIMARY KEY (player_id, server_id),
			FOREIGN KEY (selected_demon_id) REFERENCES demons(id),
			UNIQUE (player_id, server_id)
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS player_demons (
			player_id 		INTEGER,
			server_id 		INTEGER,
			demon_id		INTEGER,
			stored_rank		INTEGER,
			in_party		INTEGER CHECK (in_party IN (0, 1)),
			on_loan			INTEGER
				DEFAULT 0
				CHECK (on_loan IN (0, 1)),
			PRIMARY KEY (player_id, server_id, demon_id)
			FOREIGN KEY (demon_id) REFERENCES demons (id)
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS player_gems (
			player_id 		INTEGER,
			server_id 		INTEGER,
			gem_name		TEXT,
			meter			INTEGER DEFAULT 0,
			quantity		INTEGER DEFAULT 0,
			UNIQUE (player_id, server_id, gem_name)
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS player_items (
			player_id 		INTEGER,
			server_id 		INTEGER,
			item_id			TEXT,
			quantity		INTEGER DEFAULT 0,
			UNIQUE (player_id, server_id, item_id)
		)
	""")
