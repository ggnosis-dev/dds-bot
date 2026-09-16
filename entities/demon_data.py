"""
This is stuff for encounters.
"""

from dataclasses import dataclass
from sqlite3 import Row

from shared_enums import EmbedColours, Personality, Tone

DEFAULT_DEMON_MULT_INCREMENT = 0.05
DEFAULT_RACE_MULT_INCREMENT = 0.1
GREETING_LENGTH = 48
TOO_WEAK_LEEWAY = 3


@dataclass
class DesignData:
	profile_img: str
	encounter_img: str
	colour: int
	greeting: str | None


@dataclass
class DemonData:
	"""Data class for a demon encounter's information."""

	id: int
	race_id: int
	name: str
	race: str
	rank: int
	dupes: int
	tone_type: Tone
	personality_type: Personality
	gems: tuple[str, str]
	design_data: DesignData


def convert_row_to_demon_data(row: Row) -> DemonData:
	"""Convert retrieved DB row into a DemonData object."""
	try:
		return DemonData(
			id=row["id"],
			race_id=row["race_id"],
			name=row["name"],
			race=row["race"].title(),
			rank=row["rank"],
			dupes=row["dupes"],
			tone_type=Tone(row["tone"]),
			personality_type=Personality(row["personality"]),
			gems=(row["gem_1"], row["gem_2"]),
			design_data=convert_row_to_design_data(row),
		)
	except Exception as e:
		raise KeyError(f"Problem when creating DemonData | {e}")


def convert_row_to_design_data(row: Row) -> DesignData:
	try:
		row_keys = row.keys()
		colour = row["colour"] if "colour" in row_keys else EmbedColours.DEFAULT.value
		greeting = row["greeting"] if "greeting" in row_keys else None

		return DesignData(
			profile_img=row["profile_img"],
			encounter_img=row["encounter_img"],
			colour=colour,
			greeting=greeting,
		)
	except Exception as e:
		raise KeyError(f"Problem when creating DesignData | {e}")
