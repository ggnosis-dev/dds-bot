import json
import sqlite3

from database_paths import ITEMS_JSON, PLAYERS_DB_PATH
from shared_enums import Emotes

item_data = []
json_data = {}

with open(ITEMS_JSON) as f:
	json_data = json.load(f)

for entry in json_data:
	print(f"Adding {entry['name']} to database.")

	emote_key = entry.get("emote", None)
	emote_name = Emotes[emote_key].name if emote_key else None
	cost = entry.get("cost", None)
	cost_json = json.dumps(cost) if cost else None

	item = (
		entry["name"],
		entry["type"],
		entry.get("exclusive_to", None),
		cost_json,
		emote_name,
		entry["description"],
	)

	item_data.append(item)

with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	cursor = conn.cursor()

	# Delete existing item table in case changes to general structure.
	cursor.execute("DROP TABLE IF EXISTS items")

	# Create item table.
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS items (
			item_id INTEGER PRIMARY KEY,
			name TEXT UNIQUE,
			type TEXT NOT NULL,
			exclusive_to TEXT,
			cost TEXT,
			emote TEXT,
			description TEXT NOT NULL
		)
	""")

	# Insert item data.
	cursor.executemany(
		"""
			INSERT OR IGNORE INTO items (
				name,
				type,
				exclusive_to,
				cost,
				emote,
				description
			)
			VALUES (?, ?, ?, ?, ?, ?)
			ON CONFLICT (name) DO UPDATE SET
				name = excluded.name,
				type = excluded.type,
				exclusive_to = excluded.exclusive_to,
				cost = excluded.cost,
				emote = excluded.emote,
				description = excluded.description
		""",
		item_data,
	)
