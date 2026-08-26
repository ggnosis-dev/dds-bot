import json
import sqlite3

from database_paths import PLAYERS_DB_PATH, SPECIAL_FUSION_JSON


def get_demon_id_by_name(demon_name: str) -> int:
	"""Retrieve a demon's ID from the database using its name."""
	with sqlite3.connect(PLAYERS_DB_PATH) as conn:
		conn.execute("PRAGMA foreign_keys = ON")
		cursor = conn.cursor()
		response = cursor.execute(
			"""
				SELECT id FROM demons
				WHERE LOWER(name) = LOWER(?)
			""",
			(demon_name,),
		).fetchone()
		return response[0] if response else 0


def load_fusion_recipes():
	recipes = []
	ingredients = []

	with open(SPECIAL_FUSION_JSON) as f:
		data = json.load(f)

	for recipe_id, entry in enumerate(data, 1):
		# Do fusion_recipes first.
		name = entry["result_demon"]
		result_id = get_demon_id_by_name(name)
		key = entry.get("required_key", None)

		print(f"INFO: Adding Special Fusion entry for: {name}")

		new_recipe = (
			recipe_id,
			result_id,
			key,
		)

		recipes.append(new_recipe)

		# Do fusion ingredients next.
		for i in entry["ingredients"]:
			ingr_id = get_demon_id_by_name(i)

			new_ingredient = (
				recipe_id,
				ingr_id,
			)

			ingredients.append(new_ingredient)

	return recipes, ingredients


with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	conn.execute("PRAGMA foreign_keys = ON")
	cursor = conn.cursor()

	# cursor.execute("DROP TABLE IF EXISTS sp_fusion_ingredients")
	# cursor.execute("DROP TABLE IF EXISTS sp_fusion_recipes")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS sp_fusion_recipes (
			id 					INTEGER PRIMARY KEY,
			result_demon_id		INTEGER NOT NULL REFERENCES demons(id),
			-- required_key should match LevelReward.value.
			required_key 		TEXT
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS sp_fusion_ingredients (
			recipe_id 	INTEGER NOT NULL REFERENCES sp_fusion_recipes(id),
			demon_id	INTEGER NOT NULL REFERENCES demons(id),
			PRIMARY KEY (recipe_id, demon_id)
		)
	""")

	rec, ing = load_fusion_recipes()

	# Insert fusion recipes data.
	cursor.executemany(
		"""
			INSERT OR IGNORE INTO sp_fusion_recipes (id, result_demon_id, required_key)
			VALUES (?, ?, ?)
		""",
		rec,
	)

	cursor.executemany(
		"""
			INSERT OR IGNORE INTO sp_fusion_ingredients (recipe_id, demon_id)
			VALUES (?, ?)
		""",
		ing,
	)
