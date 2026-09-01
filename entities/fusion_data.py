from collections import defaultdict
from dataclasses import dataclass
from sqlite3 import Row

FUSION_ACCIDENT_CHANCE = 0.01


## FUSION RELATED.
@dataclass
class IngredientData:
	ing_id: int
	race: str
	name: str


@dataclass
class SpecialFusionShopData:
	key: str
	ingredients: tuple[IngredientData, ...]
	demon_id: int
	name: str
	race: str
	rank: int


ELEMENT_RACE = ["Erthys", "Aeros", "Aquans", "Flaemis", "Gnome", "Salamander", "Sylph", "Undine"]

# Races typically have 2 pairings for level up.
ELEMENT_PAIRS = {
	"Erthys": ["Beast", "Femme", "Jaki"],
	"Aeros": ["Fairy", "Flight"],
	"Aquans": ["Fairy", "Wilder"],
	"Flaemis": ["Beast", "Femme", "Flight", "Jaki", "Wilder"],
	"Gnome": [],
	"Salamander": [],
	"Sylph": ["Avian", "Holy", "Dragon", "Lady"],
	"Undine": [],
}


def convert_row_to_special_fusion_data(recipe_rows: list[Row], ingredient_rows: list[Row]) -> list[SpecialFusionShopData]:
	try:
		recipe_ingredients: dict[int, list[IngredientData]] = defaultdict(list)
		for row in ingredient_rows:
			recipe_ingredients[row["recipe_id"]].append(
				IngredientData(
					ing_id=row["id"],
					race=row["race"].title(),
					name=row["name"],
				)
			)

		all_recipes = []
		for row in recipe_rows:
			recipe_id = row["recipe_id"]
			key = row["required_key"]
			ings = tuple(recipe_ingredients[recipe_id])

			all_recipes.append(
				SpecialFusionShopData(
					key=key,
					ingredients=ings,
					demon_id=row["id"],
					name=row["name"],
					race=row["race"].title(),
					rank=row["rank"],
				)
			)

		return all_recipes
	except Exception as e:
		raise KeyError(f"ERROR: Problem when creating SpecialFusionData | {e}")
