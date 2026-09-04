from collections import defaultdict

from entities.encounter_data import AnswerData, ReactionData, TalkData
from helpers.db import query_all, query_one
from shared_enums import Personality, ResponseType


async def get_talk_dialogue(tone_index: int, personality_index: int) -> TalkData:
	"""Get a randomly selected question, answers and reactions based on the demon's tone and personality."""

	# Get a randomly selected question.
	talk_id, q_text = query_one(
		"""
			SELECT id, question FROM talk_questions tq
			JOIN talk_question_tones tqt ON tqt.talk_id = tq.id
			WHERE tqt.tone = ?
			ORDER BY RANDOM() LIMIT 1
		""",
		(tone_index,),
	)

	# Get the answer label and response variations.
	answer_react_data = query_all(
		"""
			SELECT ta.label, tr.personality, tr.response_type, tr.response
			FROM talk_answers ta
			JOIN talk_reactions tr ON tr.answer_id = ta.id
			WHERE ta.talk_id = ? AND tr.personality = ?
		""",
		(talk_id, personality_index),
	)

	# Create dictionary where label: list of reactions.
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
