from entities.demon_data import TOO_WEAK_LEEWAY, DemonData, convert_row_to_demon_data
from entities.fusion_data import (
	SpecialFusionShopData,
	convert_row_to_special_fusion_data,
)
from helpers.db import query_all, query_one


async def get_fused_race_id(race_1: int, race_2: int) -> int | None:
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


async def get_fused_demon(player_id: int, race_1_id: int, race_2_id: int, average_rank: int) -> DemonData | None:
	fused_race = await get_fused_race_id(race_1_id, race_2_id)

	# Some races won't fuse together deliberately.
	if not fused_race:
		return None

	# The ELEMENT race are defined as their own races.
	if fused_race == 1:
		return await fuse_into_element(player_id, race_1_id)

	return await get_closest_demon_in_race(player_id, fused_race, average_rank)


async def get_fuse_with_element(
	player_id: int,
	race_id: int,
	element_demon_id: int,
	original_rank: int,
) -> DemonData | None:
	"""If the pair is a good one, get the next demon up in the race, otherwise next demon down."""

	row = query_one(
		"""
			SELECT 1 FROM element_pairings
			WHERE race_id = ? AND element_id = ?
		""",
		(race_id, element_demon_id),
	)

	positive_dir = row is not None
	return await get_next_demon_in_race(player_id, race_id, original_rank, positive_dir)


async def get_special_fusion_list(server_id: int) -> list[SpecialFusionShopData]:
	"""Get list of available special fusions for the server."""

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
			JOIN special_fusion_data_VIEW v ON v.id = fr.result_demon_id
			WHERE fr.required_key IS NULL
				OR su.unlock_key IS NOT NULL
			ORDER BY v.race, v.name ASC
		""",
		(server_id,),
	)

	if not recipe_rows:
		raise RuntimeError("Special Fusion list was not retrieved.")

	# Get all the recipe IDs in response.
	recipe_ids = [r["recipe_id"] for r in recipe_rows]
	gem_placeholders = ",".join("?" * len(recipe_ids))

	ing_rows = query_all(
		f"""
			SELECT fi.recipe_id, v.*
			FROM sp_fusion_ingredients fi
			JOIN special_fusion_data_VIEW v ON v.id = fi.demon_id
			WHERE fi.recipe_id IN ({gem_placeholders})
		""",
		tuple(recipe_ids),
	)
	return convert_row_to_special_fusion_data(recipe_rows, ing_rows)


async def get_closest_demon_in_race(player_id: int, race_id: int, rank: int) -> DemonData | None:
	"""Get the closest demon's data to the rank inside of a specific race."""

	row = query_one(
		"""
			SELECT v.*, pd.dupes
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON v.id = pd.demon_id
				AND pd.player_id = ?
			WHERE v.race_id = ?
				AND v.prevent_spawn = 0
			ORDER BY
				-- Order by absolute rank minus the passed in rank. If tied, prioritise the smaller one.
				ABS(v.rank - ?), v.rank
			LIMIT 1
		""",
		(player_id, race_id, rank),
	)
	return convert_row_to_demon_data(row) if row else None


async def get_next_demon_in_race(player_id: int, race_id: int, rank: int, positive_dir: bool) -> DemonData | None:
	"""Get the neighbouring demon of the specified race."""

	row = query_one(
		f"""
			SELECT
				v.*,
				pd.dupes
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON v.id = pd.demon_id
				AND pd.player_id = ?
			WHERE race_id = ? AND rank {">" if positive_dir else "<"} ?
			ORDER BY rank {"ASC" if positive_dir else "DESC"}
			LIMIT 1
		""",
		(player_id, race_id, rank),
	)
	return convert_row_to_demon_data(row) if row else None


async def fuse_into_element(player_id: int, race_id: int) -> DemonData | None:
	"""Used to get an Element from the specified race_id."""

	row = query_one(
		"""
			SELECT
				v.*,
				pd.dupes
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON v.id = pd.demon_id
				AND pd.player_id = ?
			JOIN fusion_elements fe
				ON v.id = fe.element_id
			WHERE fe.race_id = ?
		""",
		(player_id, race_id),
	)
	return convert_row_to_demon_data(row) if row else None


async def get_random_unowned_demon(player_id: int, rank: int) -> DemonData:
	"""
	Retrieve a random demon's data that is not currently in the player's party, from the database.
	Range is between 1 and rank + 10. Used exclusively for fusion accidents.
	"""

	rank += TOO_WEAK_LEEWAY

	row = query_one(
		"""
			SELECT
				v.*,
				pd.dupes
			FROM demon_data_VIEW v
			LEFT JOIN player_demons pd
				ON v.id = pd.demon_id
				AND pd.player_id = ?
			WHERE v.rank BETWEEN 1 AND ?
				AND v.prevent_spawn = 0
				AND pd.in_party = 0
			ORDER BY RANDOM()
			LIMIT 1
		""",
		(player_id, rank),
	)

	return convert_row_to_demon_data(row)
