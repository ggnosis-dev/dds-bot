import json
import sqlite3

from database_paths import ITEMS_JSON, PLAYERS_DB_PATH, ensure_db_dir_exists
from shared_enums import Emotes

ensure_db_dir_exists()

item_data = []
json_data = {}

# item_json = load_json(ITEMS_JSON)


with open(ITEMS_JSON) as f:
	json_data = json.load(f)

for entry in json_data:
	print(f"Adding {entry['name']} to database.")

	item = (
		entry["name"],
		entry["type"],
		entry["description"],
		Emotes.GEM.name,
		entry["exclusive_to"],
		json.dumps(entry["cost"]),
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
			name TEXT,
			type TEXT,
			cost TEXT,
			exclusive_to TEXT,
			description TEXT,
			emote TEXT
		)
	""")

	# Insert item data.
	cursor.executemany(
		"""
			INSERT INTO items (name, type, description, emote, exclusive_to, cost)
			VALUES (?, ?, ?, ?, ?, ?)
		""",
		item_data,
	)
