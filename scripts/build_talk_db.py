import json
import sqlite3

from database_paths import PLAYERS_DB_PATH, TALK_JSON
from shared_enums import Personality, ResponseType


def load_questions_answers():
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

		# Do answers next.
		for a in answers:
			# Each answer has a label acting as the words the player says.
			label = a["label"]

			for r in a["reactions"]:
				pers = Personality[r["personality"]].value
				typ = ResponseType[r["type"]].value
				res = r["response"]

				new_answer = (
					talk_id,
					pers,
					typ,
					label,
					res,
				)

				all_answers.append(new_answer)

	return all_questions, all_answers


with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	conn.execute("PRAGMA foreign_keys = ON")
	cursor = conn.cursor()

	cursor.execute("DROP TABLE IF EXISTS talk_questions")
	cursor.execute("DROP TABLE IF EXISTS talk_answers")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS talk_questions (
			id 				INTEGER PRIMARY KEY,
			cheerful		TEXT NOT NULL,
			aggressive		TEXT NOT NULL,
			shy				TEXT NOT NULL
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS talk_answers (
			talk_id 		INTEGER NOT NULL REFERENCES talk_questions(id),
			personality		INTEGER NOT NULL,
			response_type	INTEGER NOT NULL,
			label			TEXT NOT NULL,
			response		TEXT NOT NULL,
			PRIMARY KEY (talk_id, personality)
		)
	""")

	q, a = load_questions_answers()

	# Insert fusion recipes data.
	cursor.executemany(
		"""
			INSERT OR IGNORE INTO talk_questions (id, cheerful, aggressive, shy)
			VALUES (?, ?, ?, ?)
		""",
		q,
	)

	cursor.executemany(
		"""
			INSERT OR IGNORE INTO talk_answers (talk_id, personality, response_type, label, response)
			VALUES (?, ?, ?, ?, ?)
		""",
		a,
	)
