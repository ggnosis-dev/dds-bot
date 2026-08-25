import sqlite3

from database_paths import PLAYERS_DB_PATH

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute(
		"""
			CREATE VIEW IF NOT EXISTS demon_data_VIEW AS
			SELECT
				d.*,
				r.name AS race
			FROM demons d
			JOIN races r
				ON d.race_id = r.id
		"""
	)

	cursor.execute(
		"""
			CREATE VIEW IF NOT EXISTS demon_entry_VIEW AS
			SELECT
				d.id,
				d.name,
				d.rank,
				d.tone,
				r.name AS race
			FROM demons d
			JOIN races r ON d.race_id = r.id
		"""
	)
