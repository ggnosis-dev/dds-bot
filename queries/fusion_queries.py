from collections import defaultdict

from entities.demon_data import (
	ELEMENT_PAIRS,
	ELEMENT_RACE,
	DemonData,
	IngredientData,
	SpecialFusionData,
	convert_row_to_demon_data,
)
from helpers.db import query_all, query_one
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


def get_fuse_with_element(race: str, element: str, original_rank: int) -> DemonData | None:
	direction = 1 if race in ELEMENT_PAIRS[element] else -1
	return demon_queries.get_next_demon_in_race(race, original_rank, direction)


async def get_special_fusion_list(server_id: int) -> list[SpecialFusionData]:
	# 1. Check if key has been obtained. Keys in server_unlocks.
	# 2. Don't provide information on locked ones (TODO: maybe? Test this out)
	# 3. Each key is a foreign key to a demon_id. So retrieve each demon ID.
	recipe_rows = await get_unlocked_sp_fusions(server_id)

	# Get all the recipe IDs in response. Can't use row_factory.
	recipe_ids = [r[0] for r in recipe_rows]
	gem_placeholders = ",".join("?" * len(recipe_ids))

	ing_rows = query_all(
		f"""
			SELECT
				fi.recipe_id,
				d.id,
				d.race,
				d.name
			FROM sp_fusion_ingredients fi
			JOIN demons d ON d.id = fi.demon_id
			WHERE fi.recipe_id IN ({gem_placeholders})
		""",
		tuple(recipe_ids),
	)

	# Create a dictionary where recipe_id: ingredients.
	ingredients_by_recipe = defaultdict(list)
	for row in ing_rows:
		ingredients_by_recipe[row[0]].append(IngredientData(ing_id=row[1], race=row[2], name=row[3]))

	entries = []
	try:
		for row in recipe_rows:
			recipe_id = row[0]
			key = row[1]
			d_raw_data = row[2:]
			d_data = convert_row_to_demon_data(d_raw_data)
			ings = tuple(ingredients_by_recipe.get(recipe_id, ()))

			entries.append(
				SpecialFusionData(
					key=key,
					ingredients=ings,
					demon_data=d_data,
				)
			)

		# print(f"DEBUG: Special Fusion entries: {entries}")
		return entries
	except Exception as e:
		print(e)
		raise Exception(f"ERROR: get_special_fusion_list | {e}")


async def get_unlocked_sp_fusions(server_id: int) -> list:
	recipe_rows = query_all(
		"""
			SELECT
				fr.id,
				fr.required_key,
				d.*
			FROM sp_fusion_recipes fr
			LEFT JOIN server_unlocks su
				ON su.unlock_key = fr.required_key
				AND su.server_id = ?
			JOIN demons d ON d.id = fr.result_demon_id
			WHERE fr.required_key IS NULL
				OR su.unlock_key IS NOT NULL
			ORDER BY d.race, d.name ASC
		""",
		(server_id,),
	)

	# print(f"DEBUG: Recipe rows: {recipe_rows}")

	if not recipe_rows:
		raise RuntimeError("Error: Special Fusion list was not retrieved.")

	return recipe_rows
