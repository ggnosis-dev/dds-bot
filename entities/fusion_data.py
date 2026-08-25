from collections import defaultdict
from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class FusionDemonData:
	"""Data class for a demon's information."""

	id: int
	name: str
	race: str
	rank: int


## FUSION RELATED.
@dataclass
class IngredientData:
	ing_id: int
	race: str
	name: str


@dataclass
class SpecialFusionData:
	key: str
	ingredients: tuple[IngredientData, ...]
	fusion_demon_data: FusionDemonData


# TODO: Fix this whole thing. Lowkey just make these their own races and
# replace their race names with ELEMENT when using them.
ELEMENT_RACE = ["Erthys", "Aeros", "Aquans", "Flaemis"]

ELEMENT_PAIRS = {
	"Erthys": ["Beast", "Femme", "Jaki"],
	"Aeros": ["Fairy", "Flight"],
	"Aquans": ["Fairy", "Wilder"],
	"Flaemis": ["Beast", "Femme", "Flight", "Jaki", "Wilder"],
}

FUSION_DIFF_CAP = 5


def convert_row_to_fusion_demon_data(row: Row) -> FusionDemonData:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		return FusionDemonData(
			id=row["id"],
			name=row["name"],
			race=row["race"].title(),
			rank=row["rank"],
		)
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating FusionDemonData | {e}")


def convert_row_to_ingredient_data(rows: list[dict]) -> dict:
	"""Get all the ingredients for the recipe. Create a dictionary where recipe_id: ingredients."""
	try:
		ingredients_for_recipes = defaultdict(list)

		for row in rows:
			ingredients_for_recipes[row["recipe_id"]].append(
				IngredientData(
					ing_id=row["id"],
					race=row["race"].title(),
					name=row["name"],
				)
			)

		return ingredients_for_recipes
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating IngreidentData | {e}")


def convert_row_to_special_fusion_data(rows: list, ingredients_for_recipe: dict) -> list[SpecialFusionData]:
	try:
		all_recipes = []

		for row in rows:
			recipe_id = row["recipe_id"]
			key = row["required_key"]
			fd_data = convert_row_to_fusion_demon_data(row)
			ings = tuple(ingredients_for_recipe.get(recipe_id, ()))

			all_recipes.append(
				SpecialFusionData(
					key=key,
					ingredients=ings,
					fusion_demon_data=fd_data,
				)
			)

		return all_recipes
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating SpecialFusionData | {e}")
