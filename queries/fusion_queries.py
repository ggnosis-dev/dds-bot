from entities.demon_data import DemonData
from entities.fusion_data import ELEMENT_PAIRS, ELEMENT_RACE
from helpers.db import query_one
from queries import demon_queries


def get_fused_race(race_1: str, race_2: str) -> str | None:
	# Database has race_1 in alphabetically order.
	race_1, race_2 = sorted([race_1, race_2])
	race_result = query_one(
		"""
			SELECT race_result FROM fusion_chart
			WHERE race_1 = ? AND race_2 = ?
		""",
		(race_1, race_2),
	)

	return race_result[0] if race_result else None


def get_fused_demon(race_1: str, race_2: str, average_rank: int) -> DemonData | None:
	fused_race = get_fused_race(race_1, race_2)

	# Some races won't fuse together deliberately.
	if not fused_race:
		print(f"INFO: {race_1} + {race_2} cannot fuse together.")
		return None

	if fused_race in ELEMENT_RACE:
		return demon_queries.get_demon_by_name(fused_race)

	return demon_queries.get_closest_demon_in_race(fused_race, average_rank)


def get_fuse_with_element(race, element, original_rank) -> DemonData | None:
	direction = 1 if race in ELEMENT_PAIRS[element] else -1
	return demon_queries.get_next_demon_in_race(race, original_rank, direction)
