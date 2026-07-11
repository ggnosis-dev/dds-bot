import json
import sqlite3

from database_paths import PLAYERS_DB_PATH, TALK_JSON
from queries.talk_queries import get_talk_dialogue
from shared_enums import Personality, ResponseType


def load_questions_answers():
	all_questions = []
	all_answers = []
	all_reactions = []

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
		for a_id, a in enumerate(answers, 1):
			# Each answer has a label acting as the words the player says.
			label = a["label"]
			all_answers.append((talk_id, label))

			for r in a["reactions"]:
				pers = Personality[r["personality"]].value
				typ = ResponseType[r["type"]].value
				res = r["response"]

				new_reaction = (
					a_id,
					pers,
					typ,
					res,
				)

				all_reactions.append(new_reaction)

	return all_questions, all_answers, all_reactions


with sqlite3.connect(PLAYERS_DB_PATH) as conn:
	conn.execute("PRAGMA foreign_keys = ON")
	cursor = conn.cursor()

	cursor.execute("DROP TABLE IF EXISTS talk_reactions")
	cursor.execute("DROP TABLE IF EXISTS talk_answers")
	cursor.execute("DROP TABLE IF EXISTS talk_questions")

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
			id				INTEGER PRIMARY KEY,
			talk_id 		INTEGER NOT NULL REFERENCES talk_questions(id),
			label			TEXT NOT NULL
		)
	""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS talk_reactions (
			answer_id 		INTEGER NOT NULL REFERENCES talk_answers(id),
			personality		INTEGER NOT NULL,
			response_type	INTEGER NOT NULL,
			response		TEXT NOT NULL,
			PRIMARY KEY (answer_id, personality)
		)
	""")

	q, a, r = load_questions_answers()

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
			INSERT OR IGNORE INTO talk_answers (talk_id, label)
			VALUES (?, ?)
		""",
		a,
	)

	cursor.executemany(
		"""
			INSERT OR IGNORE INTO talk_reactions (answer_id, personality, response_type, response)
			VALUES (?, ?, ?, ?)
		""",
		r,
	)

get_talk_dialogue(2)
