import json
import sqlite3

from database_paths import PLAYERS_DB_PATH, TALK_JSON
from queries.demon_queries import get_demon_id_by_name


def load_fusion_recipes():
	all_questions = []
	all_answers = []

	with open(TALK_JSON) as f:
		data = json.load(f)

	for talk_id, entry in enumerate(data, 1):
		# Do fusion_recipes first.
		questions = entry["questions"]
		answers = entry["answers"]

		print(f"INFO: Adding Talk entry for: {questions['cheerful']}")

		new_question = (
			talk_id,
			questions["cheerful"],
			questions["aggressive"],
			questions["shy"],
		)

		all_questions.append(new_question)
		print(all_questions)

		# # Do fusion ingredients next.
		# for i in entry["ingredients"]:
		# 	ingr_id = get_demon_id_by_name(i)

		# 	new_ingredient = (
		# 		recipe_id,
		# 		ingr_id,
		# 	)

		# 	ingredients.append(new_ingredient)

	return all_questions, all_answers


with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	conn.execute("PRAGMA foreign_keys = ON")
	cursor = conn.cursor()

	# cursor.execute("DROP TABLE IF EXISTS sp_fusion_ingredients")
	# cursor.execute("DROP TABLE IF EXISTS sp_fusion_recipes")

	# cursor.execute("""
	# 	CREATE TABLE IF NOT EXISTS talk_questions (
	# 		id 				INTEGER PRIMARY KEY,
	# 		cheerful		TEXT NOT NULL,
	# 		aggressive		TEXT NOT NULL,
	# 		shy				TEXT NOT NULL,
	# 	)
	# """)

	# cursor.execute("""
	# 	CREATE TABLE IF NOT EXISTS talk_answers (
	# 		talk_id 	INTEGER NOT NULL REFERENCES talk_questions(id),
	# 		personality	INTEGER NOT NULL,
	# 		reaction	INTEGER NOT NULL,
	# 		label		TEXT NOT NULL,
	# 		response	TEXT NOT NULL,
	# 		PRIMARY KEY (talk_id, personality)
	# 	)
	# """)

	rec, ing = load_fusion_recipes()

	# Insert fusion recipes data.
	# cursor.executemany(
	# 	"""
	# 		INSERT OR IGNORE INTO sp_fusion_recipes (id, result_demon_id, required_key)
	# 		VALUES (?, ?, ?)
	# 	""",
	# 	rec,
	# )

	# cursor.executemany(
	# 	"""
	# 		INSERT OR IGNORE INTO sp_fusion_ingredients (recipe_id, demon_id)
	# 		VALUES (?, ?)
	# 	""",
	# 	ing,
	# )
