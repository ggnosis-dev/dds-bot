import json
import sqlite3

from database_paths import PLAYERS_DB_PATH, RACE_GEMS_JSON
from queries.gem_queries import add_gem, increase_gems

gem_list = []
with open(RACE_GEMS_JSON) as f:
	data = json.load(f)

for entry in data:
	name = entry["name"]
	races = entry["races"]

	for r in races:
		gem_list.append((name, r))

print(gem_list)

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	cursor.execute("DROP TABLE IF EXISTS race_gems")

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


increase_gems(233142721819312128, 1486175238256464025, 1)
add_gem(233142721819312128, 1486175238256464025, "Fairy", 1)
