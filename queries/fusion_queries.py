from helpers.db import query_one
from queries.demon_queries import DemonData, DemonQueries

ELEMENT_RACE = ["Erthys", "Aeros", "Aquans", "Flaemis"]

ELEMENT_PAIRS = {
	"Erthys": ["Beast", "Femme", "Jaki"],
	"Aeros": ["Fairy", "Flight"],
	"Aquans": ["Fairy", "Wilder"],
	"Flaemis": ["Beast", "Femme", "Flight", "Jaki", "Wilder"],
}


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
		return DemonQueries().get_demon_by_name(fused_race)

	return DemonQueries().get_closest_demon_in_race(fused_race, average_rank)


def get_fuse_with_element(race, element, original_rank) -> DemonData | None:
	# How do I do this?
	# Do I store all of pairs in the DB or just make a dictionary?
	if race in ELEMENT_PAIRS[element]:
		direction = 1
	else:
		direction = -1

	return DemonQueries().get_next_demon_in_race(race, original_rank, direction)
