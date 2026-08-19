import json
import sqlite3

from database_paths import PLAYERS_DB_PATH, RACE_GEMS_JSON
from queries.gem_queries import get_possible_gems

gem_list = []
with open(RACE_GEMS_JSON) as f:
	data = json.load(f)

for entry in data:
	name = entry["name"]
	races = entry["races"]

	for r in races:
		gem_list.append((name, r))

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# cursor.execute("DROP TABLE IF EXISTS race_gems")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS race_gems (
			gem_name TEXT NOT NULL,
			race TEXT NOT NULL REFERENCES demons(race),
			PRIMARY KEY (gem_name, race)
		)
	""")

	cursor.executemany(
		"""
			INSERT OR IGNORE INTO race_gems
				(gem_name, race)
			VALUES
				(?, ?)
		""",
		gem_list,
	)


print(get_possible_gems("Fairy"))
