from dataclasses import dataclass

from shared_enums import Personality, Tone


@dataclass
class DesignData:
	colour: int
	profile_img: str
	encounter_img: str


@dataclass
class DemonData:
	"""
	Data class for a demon's information.

	Args:
		id (int): Demon's unique ID.
		name (str): Demon name.
		race (str): Demon race.
		rank (int): Demon's Rank signifies its strength and base rarity.
		personality_type (Personality): Personality type, stored as a string in DB but converted to a Personality enum.
		design_data (DesignData): Design data class
		tone_type (Tone): The category the demon falls into for dialogue. Dialogue altered based on it.
	"""

	id: int
	name: str
	race: str
	rank: int
	personality_type: Personality
	design_data: DesignData
	prevent_spawn: bool
	tone_type: Tone


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
		d_id, name, race, rank, col, pers_id, pr_url, im_url, prevent, tone_id = row

		return DemonData(
			id=d_id,
			name=name,
			race=race,
			rank=rank,
			personality_type=Personality(pers_id),
			design_data=DesignData(
				colour=col,
				profile_img=pr_url,
				encounter_img=im_url,
			),
			prevent_spawn=prevent,
			tone_type=Tone(tone_id),
		)
	except Exception as e:
		print(e)
		raise KeyError(f"ERROR: Problem when creating DemonData | {e}")
