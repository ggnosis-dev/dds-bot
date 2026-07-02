from dataclasses import dataclass

from shared_enums import Personality


@dataclass
class DemonData:
	"""
	Data class for a demon's information.

	Args:
		id (int): Demon's unique ID.
		name (str): Demon name.
		race (str): Demon race.
		rank (int): Demon's Rank signifies its strength and base rarity.
		colour (int): Colour is used for styling and various embeds.
		personality_type (Personality): Personality type, stored as a string in DB but converted to a Personality enum.
		gem (str): Gem that the demon can hunt for.
		image_url (str): Image URL for demon's encounter art.
		profile_url (str): Image URL for the profile art.
	"""

	id: int
	name: str
	race: str
	rank: int
	colour: int
	personality_type: Personality
	gem: str
	profile_url: str
	image_url: str
	prevent_spawn: bool


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
	demon_data: DemonData


ELEMENT_RACE = ["Erthys", "Aeros", "Aquans", "Flaemis"]

ELEMENT_PAIRS = {
	"Erthys": ["Beast", "Femme", "Jaki"],
	"Aeros": ["Fairy", "Flight"],
	"Aquans": ["Fairy", "Wilder"],
	"Flaemis": ["Beast", "Femme", "Flight", "Jaki", "Wilder"],
}


def convert_row_to_demon_data(row: tuple) -> DemonData:
	"""
	Convert retrieved DB row into a DemonData object.

	Args:
		row (tuple): A tuple containing demon data.
	Returns:
		DemonData: Normalised DemonData object created from values provided.
	"""
	try:
		id, name, race, rank, colour, personality_type, gem, profile_url, image_url, prevent_spawn = row

		return DemonData(
			id=id,
			name=name,
			race=race,
			rank=rank,
			colour=colour,
			personality_type=Personality[personality_type],
			gem=gem,
			profile_url=profile_url,
			image_url=image_url,
			prevent_spawn=prevent_spawn,
		)
	except Exception as e:
		print(e)
		raise KeyError(f"ERROR: Problem when creating DemonData | {e}")
