from dataclasses import dataclass
from sqlite3 import Row

from shared_enums import EmbedColours, Personality, Tone


@dataclass
class DesignData:
	profile_img: str
	encounter_img: str
	colour: int
	greeting: str | None


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
	dupes: int
	tone_type: Tone
	personality_type: Personality
	design_data: DesignData
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


# TODO: Fix this whole thing. Lowkey just make these their own races and
# replace their race names with ELEMENT when using them.
ELEMENT_RACE = ["Erthys", "Aeros", "Aquans", "Flaemis"]

ELEMENT_PAIRS = {
	"Erthys": ["Beast", "Femme", "Jaki"],
	"Aeros": ["Fairy", "Flight"],
	"Aquans": ["Fairy", "Wilder"],
	"Flaemis": ["Beast", "Femme", "Flight", "Jaki", "Wilder"],
}


def convert_row_to_demon_data(row: Row) -> DemonData:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		new_demon = DemonData(
			id=row["id"],
			name=row["name"],
			race=row["race"].title(),
			rank=row["rank"],
			dupes=row["dupes"] or 0,
			tone_type=Tone(row["tone"]),
			personality_type=Personality(row["personality"]),
			design_data=DesignData(
				profile_img=row["profile_img"],
				encounter_img=row["encounter_img"],
				colour=row["colour"] or EmbedColours.DEFAULT.value,
				greeting=row["greeting"],
			),
			prevent_spawn=row["prevent_spawn"],
		)
		print(new_demon)

		return new_demon
	except Exception as e:
		print(e)
		raise KeyError(f"ERROR: Problem when creating DemonData | {e}")
