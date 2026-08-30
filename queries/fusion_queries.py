from entities.demon_data import TOO_WEAK_LEEWAY
from entities.fusion_data import (
	ELEMENT_PAIRS,
	ELEMENT_RACE,
	FusionDemonData,
	SpecialFusionData,
	convert_row_to_fusion_demon_data,
	convert_row_to_special_fusion_data,
)
from helpers.db import query_all, query_one


def get_fused_race(race_1: str, race_2: str) -> str | None:
	# Database has race_1 in alphabetical order.
	race_1, race_2 = sorted([race_1, race_2])
	race_result = query_one(
		"""
			SELECT race_result FROM fusion_chart
			WHERE race_1 = ? AND race_2 = ?
		""",
		(race_1, race_2),
	)

	return race_result[0] if race_result else None


def get_fused_demon(race_1: str, race_2: str, average_rank: int) -> FusionDemonData | None:
	fused_race = get_fused_race(race_1, race_2)

	# Some races won't fuse together deliberately.
	if not fused_race:
		print(f"INFO: {race_1} + {race_2} cannot fuse together.")
		return None

	# The ELEMENT race are defined as their own races.
	if fused_race in ELEMENT_RACE:
		return get_specifc_fusion_demon(name=fused_race)

	return get_closest_demon_in_race(fused_race, average_rank)


def get_fuse_with_element(race: str, element: str, original_rank: int) -> FusionDemonData | None:
	"""If the pair is a good one, get the next demon up in the race, otherwise next demon down."""
	direction = 1 if race in ELEMENT_PAIRS[element] else -1
	return get_next_demon_in_race(race, original_rank, direction)


async def get_special_fusion_list(server_id: int) -> list[SpecialFusionData]:
	recipe_rows = await get_unlocked_sp_fusions(server_id)

	# Get all the recipe IDs in response.
	recipe_ids = [r["recipe_id"] for r in recipe_rows]
	gem_placeholders = ",".join("?" * len(recipe_ids))

	ing_rows = query_all(
		f"""
			SELECT fi.recipe_id, v.*
			FROM sp_fusion_ingredients fi
			JOIN fusion_demon_data_VIEW v ON v.id = fi.demon_id
			WHERE fi.recipe_id IN ({gem_placeholders})
		""",
		tuple(recipe_ids),
	)

	return convert_row_to_special_fusion_data(recipe_rows, ing_rows)


async def get_unlocked_sp_fusions(server_id: int) -> list:
	recipe_rows = query_all(
		"""
			SELECT
				fr.id AS recipe_id,
				fr.required_key,
				v.*
			FROM sp_fusion_recipes fr
			LEFT JOIN server_unlocks su
				ON su.unlock_key = fr.required_key
				AND su.server_id = ?
			JOIN fusion_demon_data_VIEW v ON v.id = fr.result_demon_id
			WHERE fr.required_key IS NULL
				OR su.unlock_key IS NOT NULL
			ORDER BY v.race, v.name ASC
		""",
		(server_id,),
	)

	if not recipe_rows:
		raise RuntimeError("Error: Special Fusion list was not retrieved.")

	return recipe_rows


def get_closest_demon_in_race(race: str, rank: int) -> FusionDemonData | None:
	row = query_one(
		"""
			SELECT * FROM fusion_demon_data_VIEW
			WHERE race = UPPER(?)
				AND prevent_spawn = 0
			ORDER BY
				-- Order by absolute rank minus the passed in rank. If tied, prioritise the smaller one.
				ABS(rank - ?), rank
			LIMIT 1
		""",
		(race, rank),
	)

	return convert_row_to_fusion_demon_data(row) if row else None


def get_next_demon_in_race(race: str, rank: int, direction: int) -> FusionDemonData | None:
	query = f"""
		SELECT * FROM fusion_demon_data_VIEW
		WHERE race = UPPER(?) AND rank {">" if direction == 1 else "<"} ?
		ORDER BY rank {"ASC" if direction == 1 else "DESC"}
		LIMIT 1
	"""

	row = query_one(
		query,
		(race, rank),
	)

	return convert_row_to_fusion_demon_data(row) if row else None


def get_specifc_fusion_demon(name: str) -> FusionDemonData | None:
	row = query_one(
		"""
			SELECT * FROM fusion_demon_data_VIEW
			WHERE name = ?
		""",
		(name,),
	)

	return convert_row_to_fusion_demon_data(row) if row else None


def get_random_unowned_demon(player_id: int, server_id: int, rank: int) -> FusionDemonData | None:
	"""
	Retrieve a random demon's data that is not currently in the player's party, from the database.
	Range is between 1 and rank + 10.
	Used exclusively for fusion accidents.
	"""
	rank += TOO_WEAK_LEEWAY

	row = query_one(
		"""
			SELECT v.* FROM fusion_demon_data_VIEW v
			JOIN player_demons pd ON v.id = pd.demon_id
				-- Scope to the player and server to avoid incoming from other servers.
				AND pd.player_id = ?
				AND pd.server_id = ?
			WHERE v.rank BETWEEN 1 AND ?
				AND v.prevent_spawn = 0
				AND pd.in_party = 0
			ORDER BY RANDOM()
			LIMIT 1
		""",
		(player_id, server_id, rank),
	)

	return convert_row_to_fusion_demon_data(row) if row is not None else None
