from collections import defaultdict

from entities.encounter_data import AnswerData, ReactionData, TalkData
from helpers.db import query_all, query_one
from shared_enums import Personality, ResponseType


def get_talk_dialogue(personality_index: int):
	"""
	- Get randomly selected question.
	- Get out the one based on the personality value.
	- Join answers that have the question id as its talk_id
	- Join reactions that have the answer id as its answer_id
	"""
	pers_col = Personality(personality_index).name.lower()

	# Get a randomly selected question.
	talk_id, q_text = query_one(
		f"""
			SELECT id, {pers_col} FROM talk_questions
			ORDER BY RANDOM() LIMIT 1
		"""
	)

	answer_react_data = query_all(
		"""
			SELECT ta.label, tr.personality, tr.response_type, tr.response
			FROM talk_answers ta
			JOIN talk_reactions tr ON tr.answer_id = ta.id
			WHERE ta.talk_id = ? AND tr.personality = ?
		""",
		(talk_id, personality_index),
	)

	d: defaultdict[str, list[ReactionData]] = defaultdict(list)

	for entry in answer_react_data:
		label, pers, r_type, r = entry

		new_reaction = ReactionData(
			personality=Personality(pers),
			response_type=ResponseType(r_type),
			response=r,
		)

		d[label].append(new_reaction)

	answers = tuple(AnswerData(label=label, reactions=reactions) for label, reactions in d.items())

	# print(f"DEBUG: Question text chosen will be: {q_text}.\n\nDialogue options will be: {answers}")

	return TalkData(question=q_text, answers=answers)
